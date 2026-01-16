import os, time, json, threading, queue, socket
import sys
import uuid
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_file
import socket
import copy
from network_tests import StepRunner
from report_export import export_csv, export_json, export_pdf
from excel_config_parser import get_enhanced_targets
from databricks_integration import create_databricks_client
import psutil
import subprocess
import requests

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(APP_ROOT, "templates")
STATIC = os.path.join(APP_ROOT, "static")
EXPORTS = os.path.join(APP_ROOT, "exports")
HISTORY_DIR = os.path.join(APP_ROOT, "test_history")

app = Flask(__name__, template_folder=TEMPLATES, static_folder=STATIC)
_jobs = {}
_lock = threading.Lock()

_DEVICE_ID = None
_DEVICE_MAC = None


def _read_mac_from_sysfs(iface):
    try:
        p = f"/sys/class/net/{iface}/address"
        with open(p, 'r') as f:
            mac = (f.read() or '').strip().lower()
        if not mac or mac == '00:00:00:00:00:00':
            return None
        if len(mac.split(':')) == 6:
            return mac
        return None
    except Exception:
        return None


def _get_primary_mac():
    for iface in ('eth0', 'wlan0'):
        mac = _read_mac_from_sysfs(iface)
        if mac:
            return mac

    try:
        addrs = psutil.net_if_addrs() or {}
        for _, lst in addrs.items():
            for a in (lst or []):
                fam = getattr(a, 'family', None)
                if fam in (getattr(psutil, 'AF_LINK', None), getattr(socket, 'AF_PACKET', None)):
                    mac = (getattr(a, 'address', None) or '').strip().lower()
                    if mac and mac != '00:00:00:00:00:00' and len(mac.split(':')) == 6:
                        return mac
    except Exception:
        pass

    try:
        node = uuid.getnode()
        mac = ':'.join(f"{(node >> (i * 8)) & 0xff:02x}" for i in reversed(range(6)))
        if mac and mac != '00:00:00:00:00:00':
            return mac
    except Exception:
        pass

    return None


def _device_id_from_mac(mac):
    h = ''.join([c for c in (mac or '').lower() if c in '0123456789abcdef'])
    suffix = (h[-4:] if len(h) >= 4 else '0000').upper()
    return f"SkydioNT-{suffix}"


def _is_default_hostname(name):
    n = (name or '').strip().lower()
    if not n:
        return True
    if n in ('raspberrypi', 'localhost'):
        return True
    if n.startswith('raspberrypi'):
        return True
    return False


def _try_set_hostname(new_name):
    try:
        if not sys.platform.startswith('linux'):
            return False
        if os.geteuid() != 0:
            return False
        subprocess.run(['hostnamectl', 'set-hostname', new_name], capture_output=True, text=True, timeout=10)
        return socket.gethostname() == new_name
    except Exception:
        return False


def _init_device_identity():
    global _DEVICE_ID, _DEVICE_MAC
    if _DEVICE_ID:
        return
    mac = _get_primary_mac()
    _DEVICE_MAC = mac
    _DEVICE_ID = _device_id_from_mac(mac) if mac else 'SkydioNT-0000'

    try:
        hn = socket.gethostname()
        if _DEVICE_ID and _is_default_hostname(hn) and not hn.strip().lower().startswith('skydiont-'):
            _try_set_hostname(_DEVICE_ID)
    except Exception:
        pass


_init_device_identity()


def _is_local_request():
    try:
        addr = request.remote_addr or ''
        if addr in ('127.0.0.1', '::1'):
            return True
        if addr.startswith('::ffff:127.0.0.1'):
            return True
        return False
    except Exception:
        return False


def _allow_remote_admin():
    try:
        cfg = load_config()
        return bool(cfg.get('allow_remote_admin', False))
    except Exception:
        return False


def local_only(fn):
    @wraps(fn)
    def _wrapped(*args, **kwargs):
        if not _is_local_request() and not _allow_remote_admin():
            return jsonify({
                'error': 'This action is only allowed from the device screen (open the UI on localhost).'
            }), 403
        return fn(*args, **kwargs)

    return _wrapped


def _run(cmd, timeout=10):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or ''), (r.stderr or '')


def _mask_to_prefix(mask):
    try:
        parts = [int(x) for x in (mask or '').strip().split('.')]
        if len(parts) != 4:
            return None
        bits = ''.join(bin(p)[2:].zfill(8) for p in parts)
        if '01' in bits:
            return None
        return bits.count('1')
    except Exception:
        return None


def _prefix_to_mask(prefix):
    try:
        p = int(prefix)
        if p < 0 or p > 32:
            return None
        bits = ('1' * p).ljust(32, '0')
        return '.'.join(str(int(bits[i:i+8], 2)) for i in range(0, 32, 8))
    except Exception:
        return None


def _nmcli_get(fields, args, timeout=8):
    cmd = ['nmcli', '-t', '-g', fields] + args
    code, out, err = _run(cmd, timeout=timeout)
    if code != 0:
        raise RuntimeError(err.strip() or 'nmcli failed')
    return out.strip()


def _get_active_connection_for_device(dev):
    try:
        name = _nmcli_get('GENERAL.CONNECTION', ['device', 'show', dev])
        name = (name or '').strip()
        if name and name != '--':
            return name
    except Exception:
        pass

    try:
        out = _nmcli_get('NAME,TYPE,DEVICE', ['connection', 'show', '--active'])
        for line in (out or '').splitlines():
            parts = line.split(':')
            if len(parts) >= 3 and parts[2] == dev:
                return parts[0]
    except Exception:
        pass
    return None


def _get_device_state(dev):
    try:
        out = _nmcli_get('DEVICE,TYPE,STATE,CONNECTION', ['device', 'status'])
        for line in (out or '').splitlines():
            parts = line.split(':')
            if len(parts) >= 4 and parts[0] == dev:
                return {
                    'device': parts[0],
                    'type': parts[1],
                    'state': parts[2],
                    'connection': (parts[3] if parts[3] != '--' else None),
                }
    except Exception:
        pass
    return {'device': dev, 'type': None, 'state': None, 'connection': None}


def _get_device_details(dev):
    details = _get_device_state(dev)
    try:
        hwaddr = _nmcli_get('GENERAL.HWADDR', ['device', 'show', dev])
        mtu = _nmcli_get('GENERAL.MTU', ['device', 'show', dev])
        details['mac'] = hwaddr or None
        try:
            details['mtu'] = int(mtu)
        except Exception:
            details['mtu'] = None
    except Exception:
        details['mac'] = None
        details['mtu'] = None

    try:
        method = _nmcli_get('IP4.METHOD', ['device', 'show', dev])
        details['ipv4_method'] = method or None
    except Exception:
        details['ipv4_method'] = None

    try:
        addr = _nmcli_get('IP4.ADDRESS[1]', ['device', 'show', dev])
        if addr and '/' in addr:
            ip, prefix = addr.split('/', 1)
            details['ipv4_address'] = ip
            details['ipv4_prefix'] = int(prefix) if str(prefix).isdigit() else None
            details['ipv4_netmask'] = _prefix_to_mask(details['ipv4_prefix']) if details['ipv4_prefix'] is not None else None
        else:
            details['ipv4_address'] = None
            details['ipv4_prefix'] = None
            details['ipv4_netmask'] = None
    except Exception:
        details['ipv4_address'] = None
        details['ipv4_prefix'] = None
        details['ipv4_netmask'] = None

    try:
        gw = _nmcli_get('IP4.GATEWAY', ['device', 'show', dev])
        details['ipv4_gateway'] = gw or None
    except Exception:
        details['ipv4_gateway'] = None

    try:
        dns = _nmcli_get('IP4.DNS', ['device', 'show', dev])
        dns_list = [d for d in (dns or '').splitlines() if d.strip()]
        details['dns_servers'] = dns_list
    except Exception:
        details['dns_servers'] = []

    if dev == 'wlan0':
        try:
            ssid = _nmcli_get('GENERAL.CONNECTION,GENERAL.TYPE', ['device', 'show', dev])
            _ = ssid
        except Exception:
            pass
        try:
            w = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'], capture_output=True, text=True, timeout=5)
            if w.returncode == 0:
                for line in (w.stdout or '').strip().split('\n'):
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[0] == 'yes':
                        details['wifi'] = {
                            'connected': True,
                            'ssid': parts[1],
                            'signal': int(parts[2]) if parts[2].isdigit() else None,
                        }
                        break
        except Exception:
            pass

    details['active_connection'] = _get_active_connection_for_device(dev)
    return details


@app.after_request
def _no_cache_headers(resp):
    try:
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    except Exception:
        pass
    return resp


@app.get('/api/access')
def api_access():
    return jsonify({'is_local': _is_local_request(), 'allow_remote_admin': _allow_remote_admin()})

# Ensure history directory exists
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

DEFAULT_TARGETS = {
  "dns": [
    # Core Skydio domains
    "skydio.com",
    "cloud.skydio.com",
    # S3 buckets for vehicle data, flight data, and updates
    "skydio-vehicle-data.s3-accelerate.amazonaws.com",
    "skydio-vehicle-data.s3.amazonaws.com",
    "skydio-vehicle-data.s3-us-west-2.amazonaws.com",
    "skydio-flight-data.s3-accelerate.amazonaws.com",
    "skydio-flight-data.s3.amazonaws.com",
    "skydio-organization-files.s3-accelerate.amazonaws.com",
    "skydio-organization-files.s3.amazonaws.com",
    "skydio-ota-diff-updates.s3-accelerate.amazonaws.com",
    "skydio-ota-diff-updates.s3.amazonaws.com",
    "skydio-ota-updates.s3-accelerate.amazonaws.com",
    "skydio-ota-updates.s3.amazonaws.com",
    "skydio-controller-ota-updates.s3-accelerate.amazonaws.com",
    "skydio-controller-ota-updates.s3.amazonaws.com",
    "skydio-media-thumbnails.s3-accelerate.amazonaws.com",
    "skydio-media-thumbnails.s3.amazonaws.com",
    "skydio-media-sync-test-files.s3-accelerate.amazonaws.com",
    "skydio-media-sync-test-files.s3.amazonaws.com",
    # u-blox GPS assist services
    "online-live1.services.u-blox.com",
    "offline-live1.services.u-blox.com",
    # DNS servers
    "8.8.8.8",
    "google.com"
  ],
  "tcp": [
    # Rule 1: Skydio Cloud HTTPS (*.skydio.com:443)
    {"host":"44.237.178.82","port":443,"label":"Skydio Cloud IP 1"},
    {"host":"52.39.114.182","port":443,"label":"Skydio Cloud IP 2"},
    {"host":"35.84.246.249","port":443,"label":"Skydio Cloud IP 3"},
    {"host":"52.89.241.109","port":443,"label":"Skydio Cloud IP 4"},
    {"host":"35.84.174.167","port":443,"label":"Skydio Cloud IP 5"},
    {"host":"skydio.com","port":443,"label":"Skydio Main HTTPS"},
    {"host":"cloud.skydio.com","port":443,"label":"Skydio Cloud HTTPS"},
    # Rule 2: Livestreaming TCP 322
    {"host":"52.89.241.109","port":322,"label":"Livestream TCP 322 IP 1"},
    {"host":"35.84.174.167","port":322,"label":"Livestream TCP 322 IP 2"},
    # Rule 3: Livestreaming TCP 7881
    {"host":"34.208.18.168","port":7881,"label":"Livestream TCP 7881 IP 1"},
    {"host":"50.112.181.82","port":7881,"label":"Livestream TCP 7881 IP 2"},
    {"host":"34.214.163.204","port":7881,"label":"Livestream TCP 7881 IP 3"},
    {"host":"54.190.113.196","port":7881,"label":"Livestream TCP 7881 IP 4"},
    {"host":"35.155.8.20","port":7881,"label":"Livestream TCP 7881 IP 5"},
    {"host":"52.40.22.162","port":7881,"label":"Livestream TCP 7881 IP 6"},
    # Rule 6: Dock to Cloud TCP 51334
    {"host":"44.237.178.82","port":51334,"label":"Dock Cloud TCP 51334 IP 1"},
    {"host":"52.39.114.182","port":51334,"label":"Dock Cloud TCP 51334 IP 2"},
    {"host":"35.84.246.249","port":51334,"label":"Dock Cloud TCP 51334 IP 3"},
    # Rule 11: S3 HTTPS endpoints
    {"host":"skydio-vehicle-data.s3-accelerate.amazonaws.com","port":443,"label":"S3 Vehicle Data Accelerate"},
    {"host":"skydio-vehicle-data.s3.amazonaws.com","port":443,"label":"S3 Vehicle Data"},
    {"host":"skydio-flight-data.s3-accelerate.amazonaws.com","port":443,"label":"S3 Flight Data Accelerate"},
    {"host":"skydio-flight-data.s3.amazonaws.com","port":443,"label":"S3 Flight Data"},
    {"host":"skydio-organization-files.s3-accelerate.amazonaws.com","port":443,"label":"S3 Org Files Accelerate"},
    {"host":"skydio-ota-updates.s3-accelerate.amazonaws.com","port":443,"label":"S3 OTA Updates Accelerate"},
    {"host":"skydio-ota-updates.s3.amazonaws.com","port":443,"label":"S3 OTA Updates"},
    {"host":"skydio-controller-ota-updates.s3-accelerate.amazonaws.com","port":443,"label":"S3 Controller OTA Accelerate"},
    {"host":"skydio-media-thumbnails.s3-accelerate.amazonaws.com","port":443,"label":"S3 Media Thumbnails Accelerate"},
    # Rule 12: u-blox AssistNow
    {"host":"online-live1.services.u-blox.com","port":443,"label":"u-blox Online AssistNow"},
    {"host":"offline-live1.services.u-blox.com","port":443,"label":"u-blox Offline AssistNow"}
  ],
  "quic": [
    # Rule 7: Dock to Livestreaming QUIC/UDP 443
    {"host":"35.166.132.69","port":443,"label":"Livestream QUIC IP 1"},
    {"host":"34.214.68.80","port":443,"label":"Livestream QUIC IP 2"},
    {"host":"100.20.220.165","port":443,"label":"Livestream QUIC IP 3"},
    {"host":"35.85.110.98","port":443,"label":"Livestream QUIC IP 4"},
    {"host":"35.164.30.49","port":443,"label":"Livestream QUIC IP 5"},
    {"host":"52.32.44.190","port":443,"label":"Livestream QUIC IP 6"}
  ],
  "https": [
    # Full HTTPS validation (TLS + HTTP) - matches Dock's connection pattern
    {"url":"https://cloud.skydio.com","label":"Skydio Cloud HTTPS"},
    {"url":"https://skydio.com","label":"Skydio Main HTTPS"},
    {"url":"https://skydio-vehicle-data.s3-accelerate.amazonaws.com","label":"S3 Vehicle Data"},
    {"url":"https://skydio-ota-updates.s3-accelerate.amazonaws.com","label":"S3 OTA Updates"},
    {"url":"https://online-live1.services.u-blox.com","label":"u-blox GPS Assist"}
  ],
  "ping": [
    # Core connectivity tests
    "8.8.8.8",
    "1.1.1.1",
    "skydio.com",
    "cloud.skydio.com",
  ],
  "ntp": "time.skydio.com"
}

def _public_ip():
    try:
        import requests
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "unknown"

def _private_ip():
    try:
        import netifaces
        # Prefer eth0, then wlan0, then any other interface
        for interface in ['eth0', 'wlan0', 'en0', 'en1']:
            if interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    if not ip.startswith('127.'):
                        return ip
        return "unknown"
    except Exception:
        return "unknown"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile')
def mobile():
    return render_template('mobile.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/wifi-test')
def wifi_test_page():
    return render_template('wifi_test.html')

@app.route('/security')
def security_page():
    return render_template('security.html')

@app.route('/self-test')
def self_test_page():
    return render_template('self_test.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/device-info')
def get_device_info():
    """Get comprehensive device information"""
    try:
        import platform
        import netifaces
        
        hostname = socket.gethostname()
        
        # Get public IP
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            public_ip = response.text.strip()
        except:
            public_ip = 'Unknown'
        
        # Get private IP (prefer eth0, then wlan0, then any other)
        private_ip = 'Unknown'
        try:
            for interface in ['eth0', 'wlan0', 'en0', 'en1']:
                if interface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        private_ip = addrs[netifaces.AF_INET][0]['addr']
                        if not private_ip.startswith('127.'):
                            break
        except:
            pass
        
        # Get system info
        system_info = {
            'device_id': _DEVICE_ID,
            'hostname': hostname,
            'public_ip': public_ip,
            'private_ip': private_ip,
            'platform': platform.platform(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'uptime': get_system_uptime(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'temperature': get_cpu_temperature()
        }
        
        # Get network interfaces
        interfaces = {}
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    interfaces[interface] = {
                        'ip': addrs[netifaces.AF_INET][0]['addr'],
                        'netmask': addrs[netifaces.AF_INET][0]['netmask'],
                        'status': 'up' if interface in netifaces.interfaces() else 'down'
                    }
            except:
                pass
        
        system_info['interfaces'] = interfaces
        return jsonify(system_info)
        
    except Exception as e:
        return jsonify({
            'device_id': _DEVICE_ID,
            'hostname': socket.gethostname(),
            'public_ip': 'Unknown',
            'private_ip': 'Unknown',
            'error': str(e)
        })

def get_system_uptime():
    """Get system uptime in human readable format"""
    try:
        import datetime
        uptime_seconds = time.time() - psutil.boot_time()
        uptime = datetime.timedelta(seconds=int(uptime_seconds))
        return str(uptime)
    except:
        return 'Unknown'

def get_cpu_temperature():
    """Get CPU temperature (Raspberry Pi specific)"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read()) / 1000.0
            return f"{temp:.1f}°C"
    except:
        return 'N/A'

@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/self-test")
def self_test():
    checks = {}
    is_linux = sys.platform.startswith('linux')
    try:
        checks["nmcli"] = subprocess.run(["which", "nmcli"], capture_output=True, text=True).returncode == 0
    except Exception:
        checks["nmcli"] = False
    try:
        checks["speedtest"] = (
            subprocess.run(["which", "speedtest"], capture_output=True, text=True).returncode == 0
            or subprocess.run(["which", "speedtest-cli"], capture_output=True, text=True).returncode == 0
            or subprocess.run(["which", "speedtest_cli"], capture_output=True, text=True).returncode == 0
        )
    except Exception:
        checks["speedtest"] = False
    try:
        os.makedirs(EXPORTS, exist_ok=True)
        test_path = os.path.join(EXPORTS, ".write_test")
        with open(test_path, "w") as f:
            f.write("ok")
        os.remove(test_path)
        checks["exports_writable"] = True
    except Exception:
        checks["exports_writable"] = False

    ok = bool(checks.get("exports_writable")) and (bool(checks.get("nmcli")) if is_linux else True)
    return jsonify({"ok": ok, "checks": checks})


def _parse_listeners_from_ss(output):
    listeners = []
    for line in (output or '').splitlines():
        line = (line or '').strip()
        if not line:
            continue
        if line.lower().startswith(('netid', 'state', 'recv-q')):
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        proto = parts[0]
        local = parts[4]
        proc = None
        pid = None
        if 'users:(' in line:
            try:
                users = line.split('users:(', 1)[1]
                if '"' in users:
                    proc = users.split('"', 2)[1]
                if 'pid=' in users:
                    pid_part = users.split('pid=', 1)[1]
                    pid = ''.join([c for c in pid_part if c.isdigit()])
            except Exception:
                pass

        listeners.append({'proto': proto, 'local': local, 'process': proc, 'pid': pid})
    return listeners


def _parse_listeners_from_lsof(output):
    listeners = []
    for line in (output or '').splitlines():
        line = (line or '').strip()
        if not line:
            continue
        if line.lower().startswith('command'):
            continue

        parts = line.split()
        if len(parts) < 9:
            continue

        proc = parts[0]
        pid = parts[1]
        name = parts[-1]
        if '->' in name:
            name = name.split('->', 1)[0]
        if '(listen)' not in name.lower() and 'listen' not in (parts[-2] if len(parts) >= 2 else '').lower():
            continue
        local = name.replace('(LISTEN)', '').strip()
        listeners.append({'proto': 'tcp', 'local': local, 'process': proc, 'pid': pid})
    return listeners


def _collect_listeners(is_local):
    try:
        if sys.platform.startswith('linux'):
            r = subprocess.run(['ss', '-lntup'], capture_output=True, text=True, timeout=3)
            out = r.stdout if r.returncode == 0 else ''
            listeners = _parse_listeners_from_ss(out)
        else:
            r = subprocess.run(['lsof', '-nP', '-iTCP', '-sTCP:LISTEN'], capture_output=True, text=True, timeout=3)
            out = r.stdout if r.returncode == 0 else ''
            listeners = _parse_listeners_from_lsof(out)

        if not is_local:
            for l in listeners:
                l['process'] = None
                l['pid'] = None
        return listeners
    except Exception:
        return []


def _proxy_info():
    env = os.environ
    keys = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'no_proxy', 'NO_PROXY']
    found = {k: (env.get(k) or '').strip() for k in keys if (env.get(k) or '').strip()}
    configured = any(k.lower().endswith('proxy') and found.get(k) for k in found)
    return {'configured': bool(configured), 'env_keys': sorted(found.keys())}


def _tls_probe(host='cloud.skydio.com', port=443, timeout=5):
    try:
        import ssl as _ssl
        import socket as _socket

        ctx = _ssl.create_default_context()
        with _socket.create_connection((host, int(port)), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert() or {}
                issuer = cert.get('issuer')
                subject = cert.get('subject')
                protocol = ssock.version()

        def _dn_to_str(dn):
            try:
                parts = []
                for rdn in (dn or []):
                    for k, v in rdn:
                        parts.append(f"{k}={v}")
                return ', '.join(parts)
            except Exception:
                return ''

        issuer_str = _dn_to_str(issuer)
        subject_str = _dn_to_str(subject)

        known_good = ['Amazon', "Let's Encrypt", 'DigiCert', 'Google', 'GlobalSign']
        suspected = True
        if any(x.lower() in issuer_str.lower() for x in known_good):
            suspected = False

        details = [
            {'label': 'TLS protocol', 'value': protocol or 'Unknown'},
            {'label': 'Issuer', 'value': issuer_str or 'Unknown'},
            {'label': 'Subject', 'value': subject_str or 'Unknown'},
        ]

        return {'suspected': bool(suspected), 'details': details}
    except Exception as e:
        return {'suspected': True, 'details': [{'label': 'TLS probe error', 'value': str(e)}]}


def _network_snapshot():
    snap = {
        'gateway': None,
        'dns_servers': [],
        'active_interface': None,
        'connection_type': None,
    }

    try:
        if sys.platform.startswith('linux'):
            r = subprocess.run(['ip', '-4', 'route', 'show', 'default'], capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                line = (r.stdout.strip().split('\n')[0] if r.stdout.strip() else '')
                if line:
                    parts = line.split()
                    if 'via' in parts:
                        snap['gateway'] = parts[parts.index('via') + 1]
                    if 'dev' in parts:
                        snap['active_interface'] = parts[parts.index('dev') + 1]
    except Exception:
        pass

    try:
        dns = []
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                line = (line or '').strip()
                if line.startswith('nameserver'):
                    p = line.split()
                    if len(p) >= 2:
                        dns.append(p[1])
        snap['dns_servers'] = dns
    except Exception:
        snap['dns_servers'] = []

    iface = snap.get('active_interface')
    if iface:
        if iface.startswith('wl') or iface == 'wlan0':
            snap['connection_type'] = 'WiFi'
        elif iface.startswith('en') or iface.startswith('eth'):
            snap['connection_type'] = 'Ethernet'
        else:
            snap['connection_type'] = iface

    return snap


def _collect_outbound_targets():
    try:
        targets = copy.deepcopy(DEFAULT_TARGETS)
        try:
            enhanced = get_enhanced_targets()
            if isinstance(enhanced, dict):
                for k, v in enhanced.items():
                    if k not in targets:
                        continue
                    if k in ('dns', 'ping') and isinstance(v, list):
                        existing = set(targets.get(k, []))
                        for item in v:
                            if item not in existing:
                                targets[k].append(item)
                                existing.add(item)
                    elif k in ('tcp', 'quic', 'https') and isinstance(v, list):
                        targets[k].extend([x for x in v if isinstance(x, dict)])
                    elif k == 'ntp' and isinstance(v, str) and v.strip():
                        targets[k] = v.strip()
        except Exception:
            pass

        out = set()
        for d in targets.get('dns', []):
            out.add(f"dns:{d}")
        for p in targets.get('ping', []):
            out.add(f"icmp:{p}")
        ntp = targets.get('ntp')
        if ntp:
            out.add(f"ntp:{ntp}")
        for t in targets.get('tcp', []):
            host = t.get('host'); port = t.get('port')
            if host and port:
                out.add(f"tcp://{host}:{port}")
        for q in targets.get('quic', []):
            host = q.get('host'); port = q.get('port', 443)
            if host:
                out.add(f"udp://{host}:{port}")
        for h in targets.get('https', []):
            url = h.get('url')
            if url:
                out.add(url)

        # Additional external services used by the app
        out.add('https://api.ipify.org')
        out.add('https://speed.cloudflare.com')

        return sorted(out)
    except Exception:
        return []


@app.get('/api/security')
def api_security():
    is_local = _is_local_request()
    proxy = _proxy_info()
    tls = _tls_probe()
    listeners = _collect_listeners(is_local=is_local)
    outbound = _collect_outbound_targets()

    software = f"skydio-network-tester (python {sys.version.split()[0]})"

    ok = True
    # If a proxy is configured or TLS inspection is suspected, surface as "review".
    if proxy.get('configured') or tls.get('suspected'):
        ok = False

    return jsonify({
        'ok': ok,
        'software': software,
        'proxy': proxy,
        'tls': tls,
        'listeners': listeners,
        'outbound': outbound,
    })

@app.get("/api/info")
def info():
    private_ip = _private_ip()
    return jsonify({"device_id": _DEVICE_ID, "device_name": socket.gethostname(), "public_ip": _public_ip(), "private_ip": private_ip})

def _run_job(jid):
    # Use enhanced targets from Excel configuration
    targets = copy.deepcopy(DEFAULT_TARGETS)

    try:
        enhanced = get_enhanced_targets()
        if isinstance(enhanced, dict):
            for k, v in enhanced.items():
                if k not in targets:
                    continue

                if k in ("dns", "ping") and isinstance(v, list):
                    existing = set(targets.get(k, []))
                    for item in v:
                        if item not in existing:
                            targets[k].append(item)
                            existing.add(item)
                elif k in ("tcp", "quic", "https") and isinstance(v, list):
                    def _sig(item):
                        if not isinstance(item, dict):
                            return ("_invalid", str(item))
                        return tuple(sorted(item.items()))

                    existing = set(_sig(x) for x in targets.get(k, []))
                    for item in v:
                        s = _sig(item)
                        if s not in existing:
                            targets[k].append(item)
                            existing.add(s)
                elif k == "ntp" and isinstance(v, str) and v.strip():
                    targets[k] = v.strip()
    except Exception:
        pass
    
    runner = StepRunner(targets)
    total = runner.steps

    proxy = _proxy_info()
    tls = _tls_probe()
    snapshot = _network_snapshot()

    results = {
        "dns": [],
        "tcp": [],
        "https": [],
        "quic": [],
        "ping": [],
        "ntp": None,
        "speedtest": None,
        "_meta": {
            "device_id": _DEVICE_ID,
            "device_name": socket.gethostname(),
            "public_ip": _public_ip(),
            "private_ip": _private_ip(),
            "security": {
                "proxy_configured": bool(proxy.get('configured')),
                "tls_inspection_suspected": bool(tls.get('suspected')),
            },
            "network_snapshot": snapshot,
        },
    }
    done = 0
    for t, r in runner.run():
        if t=="dns": results["dns"].append(r)
        elif t=="tcp": results["tcp"].append(r)
        elif t=="https": results["https"].append(r)
        elif t=="quic": results["quic"].append(r)
        elif t=="ping": results["ping"].append(r)
        elif t=="ntp": results["ntp"]=r
        elif t=="speedtest": results["speedtest"]=r
        done += 1
        with _lock:
            _jobs[jid]["progress"] = int(done*100/max(total,1))
            _jobs[jid]["results"] = results
    with _lock:
        _jobs[jid]["done"] = True
        # Store results globally for export/databricks push
        global test_results
        test_results = results
        
        # Save to test history
        try:
            save_test_history(results)
        except Exception as e:
            print(f"Failed to save test history: {e}")
        
        # Auto-push to Databricks if configured
        try:
            config = load_config()
            if config.get('databricks', {}).get('enabled', False) and config.get('databricks', {}).get('auto_push', False):
                push_to_databricks(results, config['databricks'])
        except Exception as e:
            print(f"Auto Databricks push failed: {e}")

        # Auto-export if configured
        try:
            config = load_config()
            if config.get('auto_export_enabled', False):
                fmt = (config.get('auto_export_format') or 'pdf').lower()
                ts = int(time.time())
                outdir = EXPORTS
                if fmt == 'csv':
                    path = export_csv(results, outdir, ts)
                elif fmt == 'json':
                    path = export_json(results, outdir, ts)
                else:
                    path = export_pdf(results, outdir, ts)
                results.setdefault('_meta', {})
                results['_meta']['auto_export_file'] = os.path.basename(path)
        except Exception as e:
            print(f"Auto export failed: {e}")

        # Write back meta update
        _jobs[jid]["results"] = results

@app.post("/api/start")
def start():
    jid = f"job-{int(time.time())}"
    with _lock:
        _jobs[jid] = {"progress":0,"done":False,"results":None,"started": time.time()}
    threading.Thread(target=_run_job, args=(jid,), daemon=True).start()
    return jsonify({"job_id": jid})

@app.get("/api/status/<jid>")
def status(jid):
    with _lock:
        j=_jobs.get(jid,{})
    return jsonify({"progress": j.get("progress",0), "done": j.get("done", False), "results": j.get("results")})

@app.route('/api/export/<format>', methods=['GET','POST'])
def export_results(format):
    global test_results
    if not test_results:
        return jsonify({"error": "No results to export"}), 400
    
    try:
        outdir = "exports"
        ts = int(time.time())

        site_label = request.args.get('site_label')
        if site_label:
            try:
                test_results.setdefault('_meta', {})
                test_results['_meta']['site_label'] = site_label
            except Exception:
                pass
        
        if format == "csv":
            path = export_csv(test_results, outdir, ts)
        elif format == "json":
            path = export_json(test_results, outdir, ts)
        elif format == "pdf":
            path = export_pdf(test_results, outdir, ts)
        else:
            return jsonify({"error": "Invalid format"}), 400
        
        # Auto-push to cloud if configured
        config = load_config()
        if config.get('cloud_push', {}).get('enabled', False):
            push_to_cloud(test_results, os.path.basename(path), config['cloud_push'])
        
        # Auto-push to Databricks if configured
        if config.get('databricks', {}).get('enabled', False) and config.get('databricks', {}).get('auto_push', False):
            push_to_databricks(test_results, config['databricks'])
        
        name = os.path.basename(path)
        return jsonify({"success": True, "file": name, "filename": name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings')
def get_settings():
    """Get current system settings with real Pi data"""
    config_file = 'config.json'
    default_settings = {
        'auto_test_enabled': False,
        'max_auto_tests': 3,
        'test_interval_seconds': 300,
        'auto_export_enabled': False,
        'auto_export_format': 'pdf',
        'webhook_enabled': False,
        'webhook_url': '',
        'web_port': 5001,
        'allow_remote_admin': False,
        'cloud_push': {
            'enabled': False,
            'api_url': '',
            'api_key': '',
            'site_label': ''
        },
        'databricks': {
            'enabled': False,
            'workspace_url': '',
            'access_token': '',
            'warehouse_id': '',
            'database': 'network_tests',
            'table': 'test_results',
            'auto_push': False
        },
        'targets': {
            'dns': ['skydio.com', 'cloud.skydio.com', 'google.com', '8.8.8.8'],
            'tcp': [
                {'host': 'skydio.com', 'port': 443, 'label': 'Skydio Main HTTPS'},
                {'host': 'cloud.skydio.com', 'port': 443, 'label': 'Skydio Cloud HTTPS'}
            ],
            'quic': [
                {'host': 'skydio.com', 'port': 443, 'label': 'Skydio Main QUIC'},
                {'host': 'cloud.skydio.com', 'port': 443, 'label': 'Skydio Cloud QUIC'}
            ],
            'ping': ['skydio.com', '8.8.8.8', '1.1.1.1'],
            'ntp': 'time.skydio.com'
        }
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return jsonify(settings)
        else:
            return jsonify(default_settings)
    except Exception as e:
        return jsonify(default_settings)

@app.route('/api/settings/test', methods=['POST'])
@local_only
def save_test_settings():
    """Save test configuration settings"""
    try:
        config = request.get_json()
        config_file = 'config.json'
        
        # Load existing config or create new
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
        
        # Update test-related settings
        existing_config.update({
            'auto_test_enabled': config.get('auto_test_enabled', False),
            'max_auto_tests': config.get('max_auto_tests', 3),
            'test_interval_seconds': config.get('test_interval_seconds', 300),
            'targets': config.get('targets', {})
        })
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/cloud', methods=['POST'])
@local_only
def save_cloud_settings():
    """Save Cloud Push configuration settings"""
    try:
        payload = request.get_json() or {}
        config_file = 'config.json'

        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)

        existing_config['cloud_push'] = {
            'enabled': bool(payload.get('enabled', False)),
            'api_url': (payload.get('api_url') or '').strip(),
            'api_key': (payload.get('api_key') or '').strip(),
            'site_label': (payload.get('site_label') or '').strip(),
        }

        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/cloud/test-direct')
@local_only
def test_cloud_connection_direct():
    """Test an arbitrary Cloud API endpoint without requiring it to be saved/enabled."""
    try:
        data = request.get_json() or {}
        url = (data.get('api_url') or '').strip()
        api_key = (data.get('api_key') or '').strip()

        if not url:
            return jsonify({'error': 'No API URL provided'}), 400

        test_payload = {
            'test': True,
            'timestamp': int(time.time()),
            'message': 'Connection test from Skydio Network Tester'
        }

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        response = requests.post(url, json=test_payload, headers=headers, timeout=10)
        return jsonify({
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'response': (response.text or '')[:200]
        })
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Connection timeout'}), 408
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection failed'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/api', methods=['POST'])
@local_only
def save_api_settings():
    """Save API key + web auth settings to config.json."""
    try:
        payload = request.get_json() or {}
        config_file = 'config.json'

        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)

        existing_config['api_enabled'] = bool(payload.get('api_enabled', False))
        existing_config['api_key'] = (payload.get('api_key') or '').strip()
        existing_config['web_auth_enabled'] = bool(payload.get('web_auth_enabled', False))
        existing_config['web_username'] = (payload.get('web_username') or '').strip()
        existing_config['web_password'] = (payload.get('web_password') or '').strip()
        existing_config['allow_remote_admin'] = bool(payload.get('allow_remote_admin', existing_config.get('allow_remote_admin', False)))

        # Port change requires a service restart; we just persist it.
        try:
            web_port = int(payload.get('web_port', existing_config.get('web_port', 5001)))
            existing_config['web_port'] = web_port
        except Exception:
            pass

        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({'success': True, 'message': 'API settings saved. Restart service to apply port/auth changes.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/system/update')
@local_only
def system_update_placeholder():
    """Non-destructive placeholder to keep UI honest."""
    return jsonify({
        'success': False,
        'message': 'System update is not supported from the web UI. Run: sudo apt update && sudo apt upgrade -y'
    }), 501


@app.route('/api/webhook/test', methods=['POST'])
@local_only
def test_webhook_compat():
    """Compatibility endpoint for settings.js"""
    try:
        data = request.get_json(silent=True) or {}
        url = data.get('url')
        if not url:
            cfg = load_config()
            url = (cfg.get('webhook_url') or '').strip()
        if not url:
            return jsonify({'error': 'Webhook URL required'}), 400
        req = {'url': url}
        with app.test_request_context(json=req):
            return test_webhook()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/export', methods=['POST'])
@local_only
def save_export_settings():
    """Save export configuration settings"""
    try:
        config = request.get_json()
        config_file = 'config.json'
        
        # Load existing config or create new
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
        
        # Update export-related settings
        existing_config.update({
            'auto_export_enabled': config.get('auto_export_enabled', False),
            'auto_export_format': config.get('auto_export_format', 'pdf'),
            'webhook_enabled': config.get('webhook_enabled', False),
            'webhook_url': config.get('webhook_url', ''),
            'webhook_auth': config.get('webhook_auth', ''),
            'ftp_enabled': config.get('ftp_enabled', False),
            'ftp_config': config.get('ftp_config', {})
        })
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-status')
def get_system_status():
    """Get current system status information"""
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        # Format uptime
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{days}d {hours}h {minutes}m"
        
        return jsonify({
            'cpu_usage': round(cpu_percent, 1),
            'memory_usage': round(memory.percent, 1),
            'disk_usage': round(disk.percent, 1),
            'uptime': uptime_str
        })
    except Exception as e:
        return jsonify({
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A', 
            'disk_usage': 'N/A',
            'uptime': 'N/A'
        })

@app.route('/api/system/hostname', methods=['POST'])
@local_only
def set_hostname():
    """Update system hostname"""
    try:
        data = request.get_json()
        hostname = data.get('hostname', '').strip()
        
        if not hostname:
            return jsonify({'error': 'Hostname cannot be empty'}), 400
        
        # Update hostname (requires sudo)
        subprocess.run(['sudo', 'hostnamectl', 'set-hostname', hostname], check=True)
        
        return jsonify({'success': True})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Failed to update hostname. Check permissions.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/reboot', methods=['POST'])
@local_only
def reboot_system():
    """Reboot the system"""
    try:
        # Schedule reboot in 5 seconds
        subprocess.Popen(['sudo', 'shutdown', '-r', '+1'])
        return jsonify({'success': True, 'message': 'System will reboot in 1 minute'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-webhook', methods=['POST'])
@local_only
def test_webhook():
    """Test webhook connectivity"""
    try:
        data = request.get_json()
        webhook_url = data.get('url', '').strip()
        
        if not webhook_url:
            return jsonify({'error': 'Webhook URL required'}), 400
        
        # Send test payload
        import requests
        test_payload = {
            'test': True,
            'message': 'Webhook test from Skydio Network Tester',
            'timestamp': time.time()
        }
        
        response = requests.post(webhook_url, json=test_payload, timeout=10)
        
        if response.status_code < 400:
            return jsonify({'success': True, 'status_code': response.status_code})
        else:
            return jsonify({'error': f'Webhook returned status {response.status_code}'}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection failed: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/network/save', methods=['POST'])
@local_only
def save_network_settings():
    """Persist network configuration data to config.json (does not apply OS changes)."""
    try:
        config = request.get_json() or {}
        config_file = 'config.json'

        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)

        existing_config['network_config'] = config

        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({'success': True, 'message': 'Network configuration saved.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/download', methods=['POST'])
@local_only
def download_logs():
    """Create a log bundle in exports and return filename for download."""
    try:
        os.makedirs(EXPORTS, exist_ok=True)
        ts = int(time.time())
        filename = f"system_logs_{ts}.log"
        out_path = os.path.join(EXPORTS, filename)

        result = subprocess.run(['journalctl', '-n', '500', '--no-pager'], capture_output=True, text=True, timeout=10)
        with open(out_path, 'w') as f:
            f.write(result.stdout or '')
            if result.stderr:
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)

        return jsonify({'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/factory-reset', methods=['POST'])
@local_only
def factory_reset_compat():
    """Compatibility endpoint for older settings.js"""
    return factory_reset()

@app.route('/api/logs')
@local_only
def view_logs():
    """View system logs"""
    try:
        # Get recent system logs
        result = subprocess.run(['journalctl', '-n', '100', '--no-pager'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return f"<pre>{result.stdout}</pre>", 200, {'Content-Type': 'text/html'}
        else:
            return "Unable to retrieve system logs", 500
    except Exception as e:
        return f"Error retrieving logs: {str(e)}", 500

@app.route('/api/backup-config')
@local_only
def backup_config():
    """Download configuration backup"""
    try:
        config_file = 'config.json'
        if os.path.exists(config_file):
            return send_file(config_file, as_attachment=True, 
                           download_name=f'skydio-tester-config-{int(time.time())}.json')
        else:
            return jsonify({'error': 'No configuration file found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restore-config', methods=['POST'])
@local_only
def restore_config():
    """Restore configuration from backup"""
    try:
        if 'config' not in request.files:
            return jsonify({'error': 'No config file provided'}), 400
        
        file = request.files['config']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate JSON
        config_data = json.loads(file.read().decode('utf-8'))
        
        # Save to config file
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return jsonify({'success': True})
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON file'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/factory-reset', methods=['POST'])
@local_only
def system_factory_reset():
    """Factory reset the system"""
    try:
        # Remove config file
        if os.path.exists('config.json'):
            os.remove('config.json')
        
        # Clear exports directory
        if os.path.exists('exports'):
            import shutil
            shutil.rmtree('exports')
            os.makedirs('exports')
        
        return jsonify({'success': True, 'message': 'Factory reset completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get("/download/<name>")
def dl(name):
    return send_file(os.path.join(EXPORTS, name), as_attachment=True)

def push_to_cloud(results, filename, cloud_config):
    """Push test results to cloud API endpoint"""
    try:
        import requests
        import json
        
        url = cloud_config.get('api_url')
        api_key = cloud_config.get('api_key')
        
        if not url:
            return
            
        # Prepare payload
        payload = {
            'timestamp': results.get('timestamp'),
            'device_info': results.get('device_info', {}),
            'test_results': results,
            'filename': filename,
            'site_label': cloud_config.get('site_label', '')
        }
        
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            
        # Send to cloud
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Successfully pushed results to cloud: {response.status_code}")
        
    except Exception as e:
        print(f"Failed to push to cloud: {e}")

@app.post("/api/cloud/test")
@local_only
def test_cloud_connection():
    """Test cloud API connection"""
    try:
        config = load_config()
        cloud_config = config.get('cloud_push', {})
        
        if not cloud_config.get('enabled', False):
            return jsonify({'error': 'Cloud push not enabled'}), 400
            
        url = cloud_config.get('api_url')
        api_key = cloud_config.get('api_key')
        
        if not url:
            return jsonify({'error': 'No API URL configured'}), 400
            
        # Test payload
        test_payload = {
            'test': True,
            'timestamp': int(time.time()),
            'message': 'Connection test from Skydio Network Tester'
        }
        
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            
        response = requests.post(url, json=test_payload, headers=headers, timeout=10)
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'response': response.text[:200]  # Limit response size
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Connection timeout'}), 408
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection failed'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_config():
    """Load configuration from file"""
    config_file = 'config.json'
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def push_to_databricks(results, databricks_config):
    """Push test results to Databricks"""
    try:
        client = create_databricks_client({'databricks': databricks_config})
        if not client:
            print("Failed to create Databricks client")
            return
        
        database = databricks_config.get('database', 'network_tests')
        table = databricks_config.get('table', 'test_results')
        
        # Create table if it doesn't exist
        table_result = client.create_table_if_not_exists(database, table)
        if not table_result.get('success'):
            print(f"Failed to create table: {table_result.get('error')}")
            return
        
        # Insert results
        insert_result = client.insert_test_results(database, table, results)
        if insert_result.get('success'):
            print(f"Successfully pushed results to Databricks: {insert_result.get('test_id')}")
        else:
            print(f"Failed to push to Databricks: {insert_result.get('error')}")
            
    except Exception as e:
        print(f"Databricks push failed: {e}")

@app.route('/api/databricks/test', methods=['POST'])
def test_databricks_connection():
    """Test Databricks connection"""
    try:
        data = request.get_json()
        workspace_url = data.get('workspace_url', '').strip()
        access_token = data.get('access_token', '').strip()
        warehouse_id = data.get('warehouse_id', '').strip()
        
        if not workspace_url or not access_token:
            return jsonify({'error': 'Workspace URL and access token are required'}), 400
        
        from databricks_integration import DatabricksIntegration
        client = DatabricksIntegration(
            workspace_url=workspace_url,
            access_token=access_token,
            cluster_id=warehouse_id if warehouse_id else None
        )
        
        result = client.test_connection()
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/databricks/push', methods=['POST'])
def manual_databricks_push():
    """Manually push latest test results to Databricks"""
    try:
        global test_results
        if not test_results:
            return jsonify({'error': 'No test results available to push'}), 400
        
        config = load_config()
        databricks_config = config.get('databricks', {})
        
        if not databricks_config.get('enabled', False):
            return jsonify({'error': 'Databricks integration not enabled'}), 400
        
        client = create_databricks_client(config)
        if not client:
            return jsonify({'error': 'Failed to create Databricks client'}), 500
        
        database = databricks_config.get('database', 'network_tests')
        table = databricks_config.get('table', 'test_results')
        
        # Create table if needed
        table_result = client.create_table_if_not_exists(database, table)
        if not table_result.get('success'):
            return jsonify({'error': f'Failed to create table: {table_result.get("error")}'}), 500
        
        # Insert results
        insert_result = client.insert_test_results(database, table, test_results)
        
        if insert_result.get('success'):
            return jsonify({
                'success': True,
                'test_id': insert_result.get('test_id'),
                'message': 'Results successfully pushed to Databricks'
            })
        else:
            return jsonify({'error': insert_result.get('error')}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/databricks', methods=['POST'])
def save_databricks_settings():
    """Save Databricks configuration settings"""
    try:
        config = request.get_json()
        config_file = 'config.json'
        
        # Load existing config
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
        
        # Update Databricks settings
        existing_config['databricks'] = {
            'enabled': config.get('enabled', False),
            'workspace_url': config.get('workspace_url', ''),
            'access_token': config.get('access_token', ''),
            'warehouse_id': config.get('warehouse_id', ''),
            'database': config.get('database', 'network_tests'),
            'table': config.get('table', 'test_results'),
            'auto_push': config.get('auto_push', False)
        }
        
        # Save config
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Global variable to store latest test results
test_results = None

def save_test_history(results):
    """Save test results to history file"""
    try:
        timestamp = int(time.time())
        history_entry = {
            'timestamp': timestamp,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
            'device_name': results.get('_meta', {}).get('device_name', 'unknown'),
            'private_ip': results.get('_meta', {}).get('private_ip', 'unknown'),
            'public_ip': results.get('_meta', {}).get('public_ip', 'unknown'),
            'results': results
        }
        
        # Save individual test file
        filename = f"test_{timestamp}.json"
        filepath = os.path.join(HISTORY_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(history_entry, f, indent=2)
        
        # Update history index
        index_file = os.path.join(HISTORY_DIR, 'index.json')
        history_index = []
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                history_index = json.load(f)
        
        # Add new entry to index
        history_index.append({
            'timestamp': timestamp,
            'datetime': history_entry['datetime'],
            'device_name': history_entry['device_name'],
            'private_ip': history_entry['private_ip'],
            'public_ip': history_entry['public_ip'],
            'filename': filename,
            'summary': get_test_summary(results)
        })
        
        # Keep only last 100 tests
        history_index = sorted(history_index, key=lambda x: x['timestamp'], reverse=True)[:100]
        
        with open(index_file, 'w') as f:
            json.dump(history_index, f, indent=2)
            
    except Exception as e:
        print(f"Error saving test history: {e}")

def get_test_summary(results):
    """Generate a summary of test results"""
    summary = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # Count DNS tests
    for test in results.get('dns', []):
        summary['total_tests'] += 1
        if test.get('status') == 'PASS':
            summary['passed'] += 1
        elif test.get('status') == 'FAIL':
            summary['failed'] += 1
        elif test.get('status') == 'WARN':
            summary['warnings'] += 1
    
    # Count TCP tests
    for test in results.get('tcp', []):
        summary['total_tests'] += 1
        if test.get('status') == 'PASS':
            summary['passed'] += 1
        elif test.get('status') == 'FAIL':
            summary['failed'] += 1
    
    # Count QUIC tests
    for test in results.get('quic', []):
        summary['total_tests'] += 1
        if test.get('status') == 'PASS':
            summary['passed'] += 1
        elif test.get('status') == 'FAIL':
            summary['failed'] += 1
    
    # Count Ping tests
    for test in results.get('ping', []):
        summary['total_tests'] += 1
        if test.get('status') == 'PASS':
            summary['passed'] += 1
        elif test.get('status') == 'FAIL':
            summary['failed'] += 1
    
    # Count NTP test
    if results.get('ntp'):
        summary['total_tests'] += 1
        if results['ntp'].get('status') == 'PASS':
            summary['passed'] += 1
        elif results['ntp'].get('status') == 'FAIL':
            summary['failed'] += 1
    
    # Count Speed test
    if results.get('speedtest'):
        summary['total_tests'] += 1
        if results['speedtest'].get('status') == 'PASS':
            summary['passed'] += 1
        elif results['speedtest'].get('status') == 'FAIL':
            summary['failed'] += 1
        elif results['speedtest'].get('status') == 'WARN':
            summary['warnings'] += 1
    
    return summary

@app.route('/api/history')
def get_test_history():
    """Get test history index"""
    try:
        index_file = os.path.join(HISTORY_DIR, 'index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                history = json.load(f)
            return jsonify(history)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<timestamp>')
def get_test_details(timestamp):
    """Get detailed test results for a specific timestamp"""
    try:
        filename = f"test_{timestamp}.json"
        filepath = os.path.join(HISTORY_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                test_data = json.load(f)
            return jsonify(test_data)
        else:
            return jsonify({'error': 'Test not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<timestamp>', methods=['DELETE'])
@local_only
def delete_test_history(timestamp):
    """Delete a test from history"""
    try:
        filename = f"test_{timestamp}.json"
        filepath = os.path.join(HISTORY_DIR, filename)
        
        # Delete the test file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Update index
        index_file = os.path.join(HISTORY_DIR, 'index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                history_index = json.load(f)
            
            # Remove entry from index
            history_index = [entry for entry in history_index if str(entry['timestamp']) != timestamp]
            
            with open(index_file, 'w') as f:
                json.dump(history_index, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/clear', methods=['POST'])
@local_only
def clear_test_history():
    """Clear all test history"""
    try:
        # Remove all test files
        if os.path.exists(HISTORY_DIR):
            import shutil
            shutil.rmtree(HISTORY_DIR)
            os.makedirs(HISTORY_DIR)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/scan', methods=['GET'])
@local_only
def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        # Use nmcli to scan for WiFi networks
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return jsonify({'error': 'Failed to scan WiFi networks'}), 500
        
        networks = []
        seen_ssids = set()
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 3:
                ssid = parts[0].strip()
                signal = parts[1].strip()
                security = parts[2].strip()
                
                # Skip duplicates and empty SSIDs
                if ssid and ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    networks.append({
                        'ssid': ssid,
                        'signal': int(signal) if signal.isdigit() else 0,
                        'security': security,
                        'secured': bool(security and security != '--')
                    })
        
        # Sort by signal strength
        networks.sort(key=lambda x: x['signal'], reverse=True)
        
        return jsonify({'networks': networks})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'WiFi scan timeout'}), 408
    except FileNotFoundError:
        return jsonify({'error': 'nmcli not found. NetworkManager may not be installed.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/current', methods=['GET'])
def get_current_wifi():
    """Get currently connected WiFi network"""
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 3 and parts[0] == 'yes':
                    return jsonify({
                        'connected': True,
                        'ssid': parts[1],
                        'signal': int(parts[2]) if parts[2].isdigit() else 0
                    })
        
        return jsonify({'connected': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/network/status', methods=['GET'])
def network_status():
    try:
        status = {
            'hostname': socket.gethostname(),
            'private_ip': _private_ip(),
            'public_ip': _public_ip(),
            'active_interface': None,
            'connection_type': None,
            'gateway': None,
            'dns_servers': [],
            'wifi': {
                'connected': False,
                'ssid': None,
                'signal': None,
            },
        }

        try:
            r = subprocess.run(['ip', '-4', 'route', 'show', 'default'], capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                line = (r.stdout.strip().split('\n')[0] if r.stdout.strip() else '')
                if line:
                    parts = line.split()
                    if 'via' in parts:
                        status['gateway'] = parts[parts.index('via') + 1]
                    if 'dev' in parts:
                        status['active_interface'] = parts[parts.index('dev') + 1]
        except Exception:
            pass

        if status['active_interface']:
            if status['active_interface'].startswith('wl') or status['active_interface'] == 'wlan0':
                status['connection_type'] = 'WiFi'
            elif status['active_interface'].startswith('en') or status['active_interface'].startswith('eth'):
                status['connection_type'] = 'Ethernet'
            else:
                status['connection_type'] = status['active_interface']

        try:
            dns = []
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('nameserver'):
                        p = line.split()
                        if len(p) >= 2:
                            dns.append(p[1])
            status['dns_servers'] = dns
        except Exception:
            status['dns_servers'] = []

        try:
            w = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'], capture_output=True, text=True, timeout=5)
            if w.returncode == 0:
                for line in w.stdout.strip().split('\n'):
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[0] == 'yes':
                        status['wifi'] = {
                            'connected': True,
                            'ssid': parts[1],
                            'signal': int(parts[2]) if parts[2].isdigit() else None,
                        }
                        break
        except Exception:
            pass

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get('/api/network/interfaces')
def network_interfaces():
    """Return detected interface state for Ethernet/WiFi in a UI-friendly shape."""
    try:
        return jsonify({
            'eth0': _get_device_details('eth0'),
            'wlan0': _get_device_details('wlan0'),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/network/interface/<ifname>/config')
@local_only
def apply_interface_config(ifname):
    """Apply DHCP/static config to an interface using NetworkManager."""
    try:
        if ifname not in ('eth0', 'wlan0'):
            return jsonify({'error': 'Unsupported interface'}), 400

        payload = request.get_json() or {}
        mode = (payload.get('mode') or '').strip().lower()
        ip = (payload.get('ip') or '').strip()
        netmask = (payload.get('netmask') or '').strip()
        gateway = (payload.get('gateway') or '').strip()
        dns = (payload.get('dns') or '').strip()

        conn = _get_active_connection_for_device(ifname)
        if not conn:
            return jsonify({'error': f'No active connection profile found for {ifname}'}), 400

        cmds = []
        if mode == 'dhcp':
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.method', 'auto'])
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.addresses', ''])
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.gateway', ''])
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.dns', ''])
        elif mode == 'static':
            prefix = None
            if netmask:
                prefix = _mask_to_prefix(netmask)
            if prefix is None:
                prefix = payload.get('prefix')
            try:
                prefix = int(prefix)
            except Exception:
                prefix = None

            if not ip or prefix is None:
                return jsonify({'error': 'Static config requires ip + netmask or prefix'}), 400

            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.method', 'manual'])
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.addresses', f'{ip}/{prefix}'])
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.gateway', gateway])

            dns_list = [d.strip() for d in dns.split(',') if d.strip()] if dns else []
            cmds.append(['nmcli', 'con', 'mod', conn, 'ipv4.dns', ','.join(dns_list)])
        else:
            return jsonify({'error': 'Invalid mode. Use dhcp or static.'}), 400

        for c in cmds:
            code, out, err = _run(c, timeout=10)
            if code != 0:
                return jsonify({'error': err.strip() or 'nmcli failed'}), 500

        # Bring connection up to apply changes
        code, out, err = _run(['nmcli', 'con', 'up', conn], timeout=20)
        if code != 0:
            return jsonify({'error': err.strip() or 'Failed to apply connection'}), 500

        return jsonify({'success': True, 'message': f'Applied {mode} config to {ifname}', 'connection': conn})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/network', methods=['POST'])
@local_only
def save_network_config():
    """Save network configuration (WiFi credentials)"""
    try:
        config = request.get_json()
        wlan_config = config.get('wlan0', {})
        ssid = wlan_config.get('ssid', '').strip()
        password = wlan_config.get('password', '').strip()
        
        if not ssid:
            return jsonify({'error': 'SSID is required'}), 400
        
        # Use nmcli to connect to WiFi network
        cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
        if password:
            cmd.extend(['password', password])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Successfully connected to {ssid}'
            })
        else:
            error_msg = result.stderr.strip() if result.stderr else 'Connection failed'
            return jsonify({'error': error_msg}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Connection timeout'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/disconnect', methods=['POST'])
@local_only
def disconnect_wifi():
    """Disconnect from current WiFi network"""
    try:
        result = subprocess.run(
            ['nmcli', 'dev', 'disconnect', 'wlan0'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Disconnected from WiFi'})
        else:
            return jsonify({'error': 'Failed to disconnect'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/saved', methods=['GET'])
@local_only
def get_saved_networks():
    """Get list of saved WiFi networks"""
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            networks = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 2 and parts[1] == '802-11-wireless':
                    networks.append({'name': parts[0]})
            return jsonify({'networks': networks})
        else:
            return jsonify({'networks': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/forget/<network_name>', methods=['DELETE'])
@local_only
def forget_wifi_network(network_name):
    """Forget a saved WiFi network"""
    try:
        result = subprocess.run(
            ['nmcli', 'connection', 'delete', network_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Forgot network {network_name}'})
        else:
            return jsonify({'error': 'Failed to forget network'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host="0.0.0.0")
