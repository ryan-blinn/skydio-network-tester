import os, time, json, threading, queue, socket
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_file
import socket
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


def _client_ip():
    xf = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    return xf or (request.remote_addr or '')


def _is_local_request():
    ip = _client_ip()
    return ip in ('127.0.0.1', '::1')


def _admin_token():
    config = load_config()
    return os.environ.get('SKYDIO_ADMIN_TOKEN') or config.get('admin_token')


def require_admin_for_remote(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _admin_token()
        if not token:
            return fn(*args, **kwargs)
        if _is_local_request():
            return fn(*args, **kwargs)

        provided = request.headers.get('X-Admin-Token') or request.args.get('admin_token')
        if provided == token:
            return fn(*args, **kwargs)

        return jsonify({'error': 'Remote changes require admin token'}), 403

    return wrapper

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
  "udp_ranges": [
    # Rule 9: Dock to Livestreaming UDP port ranges (WebRTC)
    {"host":"34.208.18.168","port_start":40000,"port_end":41000,"sample_size":5,"label":"Dock WebRTC Range 40000-41000"},
    # Rule 4: Client to Livestreaming UDP port ranges (WebRTC)
    {"host":"50.112.181.82","port_start":50000,"port_end":60000,"sample_size":5,"label":"Client WebRTC Range 50000-60000"}
  ],
  "ping": [
    # Core connectivity tests
    "8.8.8.8",
    "1.1.1.1",
    "skydio.com",
    "cloud.skydio.com",
    # Skydio Cloud IPs
    "44.237.178.82",
    "52.39.114.182",
    "35.84.246.249"
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

@app.route('/mobile/settings')
def mobile_settings():
    return render_template('mobile_settings.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

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

@app.get("/api/info")
def info():
    private_ip = _private_ip()
    return jsonify({"device_name": socket.gethostname(), "public_ip": _public_ip(), "private_ip": private_ip})

def _run_job(jid):
    # Use enhanced targets from Excel configuration
    try:
        targets = get_enhanced_targets()
    except Exception:
        targets = DEFAULT_TARGETS
    
    runner = StepRunner(targets)
    total = runner.steps
    results = {
        "dns": [],
        "tcp": [],
        "https": [],
        "quic": [],
        "udp_range": [],
        "ping": [],
        "ntp": None,
        "speedtest": None,
        "_meta": {"device_name": socket.gethostname(), "public_ip": _public_ip(), "private_ip": _private_ip()},
    }
    done = 0
    for t, r in runner.run():
        if t=="dns": results["dns"].append(r)
        elif t=="tcp": results["tcp"].append(r)
        elif t=="https": results["https"].append(r)
        elif t=="quic": results["quic"].append(r)
        elif t=="udp_range": results["udp_range"].append(r)
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

def _export_results_from_payload(payload, format):
    if not payload:
        return jsonify({"error": "No results to export"}), 400

    try:
        outdir = "exports"
        ts = int(time.time())

        site_label = request.args.get("site_label")
        if not site_label:
            try:
                body = request.get_json(silent=True) or {}
                site_label = body.get("site_label")
            except Exception:
                site_label = None
        if site_label:
            payload.setdefault("_meta", {})["site_label"] = site_label

        if format == "csv":
            path = export_csv(payload, outdir, ts)
        elif format == "json":
            path = export_json(payload, outdir, ts)
        elif format == "pdf":
            path = export_pdf(payload, outdir, ts)
        else:
            return jsonify({"error": "Invalid format"}), 400

        config = load_config()
        if config.get('cloud_push', {}).get('enabled', False):
            push_to_cloud(payload, os.path.basename(path), config['cloud_push'])

        if config.get('databricks', {}).get('enabled', False) and config.get('databricks', {}).get('auto_push', False):
            push_to_databricks(payload, config['databricks'])

        filename = os.path.basename(path)
        return jsonify({"success": True, "file": filename, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/<format>', methods=['GET', 'POST'])
def export_results(format):
    global test_results
    return _export_results_from_payload(test_results, format)


@app.route('/api/export/<format>/<jid>', methods=['GET', 'POST'])
def export_results_job(format, jid):
    with _lock:
        j = _jobs.get(jid, {})
        payload = j.get("results")
    return _export_results_from_payload(payload, format)

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
        'webhook_auth': '',
        'web_port': 5001,
        'web_auth_enabled': False,
        'web_username': 'admin',
        'web_password': '',
        'api_enabled': False,
        'api_key': '',
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
                settings['remote_write_requires_token'] = bool(_admin_token())
                return jsonify(settings)
        else:
            default_settings['remote_write_requires_token'] = bool(_admin_token())
            return jsonify(default_settings)
    except Exception as e:
        default_settings['remote_write_requires_token'] = bool(_admin_token())
        return jsonify(default_settings)

@app.route('/api/settings/test', methods=['POST'])
@require_admin_for_remote
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


@app.route('/api/settings/api', methods=['POST'])
@require_admin_for_remote
def save_api_settings():
    """Save web interface + API access configuration settings"""
    try:
        data = request.get_json() or {}
        config_file = 'config.json'

        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)

        existing_config.update({
            'web_port': int(data.get('web_port', existing_config.get('web_port', 5001) or 5001)),
            'web_auth_enabled': bool(data.get('web_auth_enabled', False)),
            'web_username': data.get('web_username', existing_config.get('web_username', 'admin') or 'admin'),
            'web_password': data.get('web_password', existing_config.get('web_password', '')),
            'api_enabled': bool(data.get('api_enabled', False)),
            'api_key': data.get('api_key', existing_config.get('api_key', '')),
        })

        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/export', methods=['POST'])
@require_admin_for_remote
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
@require_admin_for_remote
def update_hostname():
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
@require_admin_for_remote
def reboot_system():
    """Reboot the system"""
    try:
        # Schedule reboot in 5 seconds
        subprocess.Popen(['sudo', 'shutdown', '-r', '+1'])
        return jsonify({'success': True, 'message': 'System will reboot in 1 minute'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-webhook', methods=['POST'])
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

@app.route('/api/settings/network', methods=['POST'])
@require_admin_for_remote
def save_network_settings():
    """Save network configuration settings"""
    try:
        config = request.get_json()
        
        # For now, just save to config file - actual network config would require root
        config_file = 'config.json'
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
        
        existing_config['network_config'] = config
        
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Network configuration saved. Changes will take effect after reboot.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
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
@require_admin_for_remote
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
@require_admin_for_remote
def factory_reset():
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
@require_admin_for_remote
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=False, port=port, host="0.0.0.0", use_reloader=False)
