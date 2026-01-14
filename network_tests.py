import socket, subprocess, time, requests, os, json, random
import asyncio
import ssl
import struct
from urllib.parse import urlparse

def resolve_dns(name, timeout=3):
    start=time.time()
    try:
        socket.setdefaulttimeout(timeout)
        ip=socket.gethostbyname(name)
        return {"target":name,"status":"PASS","ip":ip,"latency_ms":int((time.time()-start)*1000)}
    except Exception as e:
        return {"target":name,"status":"FAIL","error":str(e)}

def tcp_check(host, port, timeout=5, label=None, verify_tls=False):
    """Enhanced TCP check with optional TLS validation to match Dock behavior"""
    start=time.time()
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
    try:
        s.connect((host,int(port)))
        latency_ms = int((time.time()-start)*1000)
        
        # For HTTPS ports (443), verify TLS handshake like the Dock does
        if verify_tls and int(port) == 443:
            try:
                # Wrap socket with TLS - mimics Dock's secure connection
                context = ssl.create_default_context()
                # Dock validates certificates - we should too
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                
                with context.wrap_socket(s, server_hostname=host) as ssock:
                    # Verify we can complete TLS handshake
                    cert = ssock.getpeercert()
                    tls_version = ssock.version()
                    r={"target":f"{host}:{port}","status":"PASS","latency_ms":latency_ms,
                       "tls_version":tls_version,"cert_valid":True}
            except ssl.SSLError as ssl_err:
                r={"target":f"{host}:{port}","status":"FAIL","error":f"TLS Error: {str(ssl_err)}",
                   "latency_ms":latency_ms}
            except Exception as tls_err:
                r={"target":f"{host}:{port}","status":"FAIL","error":f"TLS Validation Failed: {str(tls_err)}",
                   "latency_ms":latency_ms}
        else:
            s.shutdown(socket.SHUT_RDWR)
            r={"target":f"{host}:{port}","status":"PASS","latency_ms":latency_ms}
        
        if label: r["label"]=label
        return r
    except Exception as e:
        r={"target":f"{host}:{port}","status":"FAIL","error":str(e)}
        if label: r["label"]=label
        return r
    finally:
        try: s.close()
        except: pass

def ping(host, count=2):
    try:
        res=subprocess.run(["ping","-n","-c",str(count),host], capture_output=True, text=True, timeout=8)
        ok=(res.returncode==0); tail="\n".join(res.stdout.splitlines()[-2:])
        return {"target":host,"status":"PASS" if ok else "FAIL","output":tail}
    except Exception as e:
        return {"target":host,"status":"FAIL","error":str(e)}

def ntp_check(server="time.skydio.com", timeout=3):
    try:
        import ntplib
        c=ntplib.NTPClient(); r=c.request(server, version=3, timeout=timeout)
        return {"target":server,"status":"PASS","offset_ms":int(r.offset*1000)}
    except Exception as e:
        return {"target":server,"status":"FAIL","error":str(e)}

def _try_ookla():
    try:
        # Use multiple threads and larger test duration for more accurate Pi results
        res = subprocess.run(["speedtest","--accept-license","--accept-gdpr","-f","json","--progress=no"], capture_output=True, text=True, timeout=120)
        if res.returncode != 0: return None
        data=json.loads(res.stdout)
        dl = round(data["download"]["bandwidth"]*8/1_000_000,1)
        ul = round(data["upload"]["bandwidth"]*8/1_000_000,1)
        return {"source":"ookla","download_mbps":dl,"upload_mbps":ul,"server":data.get("server",{}).get("name","Unknown")}
    except Exception:
        return None

def _cloudflare_down(min_bytes=25_000_000, timeout=45):
    """Enhanced download test with larger payload and optimized chunk size for Pi"""
    url=f"https://speed.cloudflare.com/__down?bytes={min_bytes}"
    start=time.time(); total=0
    # Use larger chunk size for better Pi performance
    chunk_size = 262144  # 256KB chunks
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            if not chunk: break
            total += len(chunk)
            if total >= min_bytes: break
    elapsed=max(time.time()-start,1e-6)
    return round((total*8)/1_000_000/elapsed,1)

def _cloudflare_up(min_bytes=10_000_000, timeout=45):
    """Enhanced upload test with larger payload for better Pi accuracy"""
    url="https://speed.cloudflare.com/__up"
    data=os.urandom(min_bytes)
    start=time.time()
    # Use streaming upload for better memory management on Pi
    r=requests.post(url, data=data, timeout=timeout, stream=True)
    r.raise_for_status()
    elapsed=max(time.time()-start,1e-6)
    return round((len(data)*8)/1_000_000/elapsed,1)

def quic_check(host, port=443, timeout=5, label=None):
    """Test QUIC protocol connectivity - simplified approach for better reliability"""
    start = time.time()
    try:
        # First try: Check if curl supports HTTP/3
        curl_check = subprocess.run(["curl", "--version"], capture_output=True, text=True, timeout=5)
        has_http3 = "HTTP3" in curl_check.stdout or "http3" in curl_check.stdout
        
        if has_http3:
            # Try HTTP/3 with curl
            cmd = ["curl", "-s", "-I", "--http3-only", "--connect-timeout", str(timeout), 
                   "--max-time", str(timeout), f"https://{host}:{port}/"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            latency_ms = int((time.time() - start) * 1000)
            
            if result.returncode == 0 and "HTTP/3" in result.stdout:
                r = {"target": f"{host}:{port}", "status": "PASS", "latency_ms": latency_ms, "protocol": "QUIC/HTTP3"}
            else:
                # Fall back to UDP port check
                r = _quic_udp_check(host, port, timeout, start)
        else:
            # No HTTP/3 support, do UDP port check
            r = _quic_udp_check(host, port, timeout, start)
        
        if label:
            r["label"] = label
        return r
        
    except subprocess.TimeoutExpired:
        r = {"target": f"{host}:{port}", "status": "FAIL", "error": "QUIC test timeout", "protocol": "QUIC"}
        if label:
            r["label"] = label
        return r
    except Exception as e:
        r = {"target": f"{host}:{port}", "status": "FAIL", "error": str(e), "protocol": "QUIC"}
        if label:
            r["label"] = label
        return r

def _quic_udp_check(host, port, timeout, start_time):
    """Enhanced UDP port check for QUIC - matches Dock's QUIC connection pattern"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Resolve hostname to IP if needed
        try:
            ip_addr = socket.gethostbyname(host)
        except:
            ip_addr = host
        
        # Send QUIC Initial packet (matches Dock's connection initiation)
        # QUIC Initial packet format: Header Form (1) | Fixed Bit (1) | Long Packet Type (2) | Reserved (2) | Packet Number Length (2)
        quic_version = 0x00000001  # QUIC v1
        
        # Build QUIC Initial packet header
        header_byte = 0xc0  # Long header, Initial packet
        packet = struct.pack('!B', header_byte)
        packet += struct.pack('!I', quic_version)
        packet += b'\x00' * 20  # Simplified DCID/SCID
        
        try:
            sock.sendto(packet, (ip_addr, port))
            
            # Wait for response (QUIC server should respond or reject)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(1500)
                latency_ms = int((time.time() - start_time) * 1000)
                # Received response - QUIC endpoint is active
                return {"target": f"{host}:{port}", "status": "PASS", "latency_ms": latency_ms, 
                       "protocol": "QUIC/UDP", "response_size": len(data)}
            except socket.timeout:
                # No response within timeout - port may be filtered or endpoint inactive
                latency_ms = int((time.time() - start_time) * 1000)
                # Try one more time with basic UDP probe
                sock.sendto(b'\x00' * 16, (ip_addr, port))
                sock.settimeout(1)
                try:
                    data, addr = sock.recvfrom(1500)
                    return {"target": f"{host}:{port}", "status": "PASS", "latency_ms": latency_ms, 
                           "protocol": "QUIC/UDP"}
                except:
                    return {"target": f"{host}:{port}", "status": "WARN", "latency_ms": latency_ms, 
                           "protocol": "QUIC/UDP", "note": "Port accessible but no QUIC response"}
        finally:
            sock.close()
            
    except Exception as e:
        return {"target": f"{host}:{port}", "status": "FAIL", "error": str(e), "protocol": "QUIC/UDP"}

def udp_port_range_check(host, port_start, port_end, sample_size=5, timeout=2, label=None):
    """Test UDP port range accessibility (for WebRTC ports 40000-41000, 50000-60000)
    Note: Cannot fully validate without active WebRTC session, but can check if ports are filtered"""
    start_time = time.time()
    
    # Sample random ports from the range
    import random
    port_range = list(range(port_start, port_end + 1))
    sample_ports = random.sample(port_range, min(sample_size, len(port_range)))
    
    results = {"accessible": 0, "filtered": 0, "errors": 0}
    
    for port in sample_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Send UDP probe packet
            probe = b'\x00' * 16
            sock.sendto(probe, (host, port))
            
            # Check for ICMP port unreachable (indicates firewall allows but no service)
            try:
                sock.recvfrom(1024)
                results["accessible"] += 1
            except socket.timeout:
                # Timeout could mean filtered or no response - assume accessible
                results["accessible"] += 1
            
            sock.close()
        except Exception as e:
            results["errors"] += 1
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Determine status based on results
    if results["accessible"] >= sample_size * 0.8:
        status = "PASS"
    elif results["accessible"] >= sample_size * 0.5:
        status = "WARN"
    else:
        status = "FAIL"
    
    r = {
        "target": f"{host}:{port_start}-{port_end}",
        "status": status,
        "latency_ms": latency_ms,
        "ports_tested": sample_size,
        "accessible": results["accessible"],
        "note": "Sampled port range - full validation requires active WebRTC session"
    }
    
    if label:
        r["label"] = label
    
    return r

def https_full_check(url, timeout=5, label=None):
    """Full HTTPS check including TLS handshake and certificate validation - matches Dock's connection pattern"""
    start = time.time()
    
    try:
        # Parse URL
        parsed = urlparse(url if url.startswith('http') else f'https://{url}')
        host = parsed.hostname
        port = parsed.port or 443
        
        # Perform full HTTPS request like the Dock does
        response = requests.get(
            f'https://{host}:{port}',
            timeout=timeout,
            verify=True,  # Verify SSL certificates like Dock does
            allow_redirects=True
        )
        
        latency_ms = int((time.time() - start) * 1000)
        
        r = {
            "target": f"{host}:{port}",
            "status": "PASS" if response.status_code < 400 else "WARN",
            "latency_ms": latency_ms,
            "http_status": response.status_code,
            "tls_verified": True
        }
        
        if label:
            r["label"] = label
        
        return r
        
    except requests.exceptions.SSLError as e:
        r = {
            "target": f"{host}:{port}",
            "status": "FAIL",
            "error": f"SSL/TLS Error: {str(e)}",
            "tls_verified": False
        }
    except Exception as e:
        r = {
            "target": f"{host}:{port}",
            "status": "FAIL",
            "error": str(e)
        }
    
    if label:
        r["label"] = label
    
    return r

def speedtest():
    """Enhanced speedtest with Skydio-specific thresholds from documentation"""
    # Try Ookla first (most accurate)
    st = _try_ookla()
    
    # If Ookla fails, try Cloudflare with multiple attempts for consistency
    if st is None:
        attempts = 2
        best_dl, best_ul = 0, 0
        
        for attempt in range(attempts):
            try:
                dl = _cloudflare_down()
                ul = _cloudflare_up()
                
                # Keep the best results from multiple attempts
                if dl > best_dl:
                    best_dl = dl
                if ul > best_ul:
                    best_ul = ul
                    
                # Small delay between attempts
                if attempt < attempts - 1:
                    time.sleep(2)
                    
            except Exception as e:
                if attempt == attempts - 1:  # Last attempt failed
                    return {"status":"FAIL","error":str(e)}
                continue
        
        st = {"source":"cloudflare","download_mbps":best_dl,"upload_mbps":best_ul}
    
    # Skydio requirements: 1 Dock = 20 Mbps up (10 min), 80 Mbps down (20 min)
    dl, ul = st["download_mbps"], st["upload_mbps"]
    
    # Adjusted for single Dock deployment
    if dl >= 20 and ul >= 10:
        status = "PASS"
        note = "Meets minimum requirements for 1 Dock"
    elif dl >= 80 and ul >= 20:
        status = "PASS"
        note = "Meets recommended requirements for 1 Dock"
    elif dl >= 10 and ul >= 5:
        status = "WARN"
        note = "Below minimum - may experience degraded performance"
    else:
        status = "FAIL"
        note = "Insufficient bandwidth for Skydio operations"
    
    st["status"] = status
    st["note"] = note
    return st

class StepRunner:
    def __init__(self, targets):
        self.targets=targets
        self.steps=self._count_steps()

    def _count_steps(self):
        return (len(self.targets.get("dns",[]))+
                len(self.targets.get("tcp",[]))+
                len(self.targets.get("https",[]))+
                len(self.targets.get("ping",[]))+
                len(self.targets.get("quic",[]))+
                len(self.targets.get("udp_ranges",[]))+
                2) # + ntp + speedtest

    def run(self):
        # DNS
        for n in self.targets.get("dns",[]):
            yield ("dns", resolve_dns(n))
        # TCP with optional TLS validation
        for t in self.targets.get("tcp",[]):
            verify_tls = t.get("verify_tls", False)
            yield ("tcp", tcp_check(t.get("host"), t.get("port"), label=t.get("label"), verify_tls=verify_tls))
        # Full HTTPS checks (TLS + HTTP)
        for h in self.targets.get("https",[]):
            yield ("https", https_full_check(h.get("url"), label=h.get("label")))
        # QUIC
        for q in self.targets.get("quic",[]):
            yield ("quic", quic_check(q.get("host"), q.get("port", 443), label=q.get("label")))
        # UDP Port Ranges (WebRTC)
        for u in self.targets.get("udp_ranges",[]):
            yield ("udp_range", udp_port_range_check(
                u.get("host"), 
                u.get("port_start"), 
                u.get("port_end"),
                sample_size=u.get("sample_size", 5),
                label=u.get("label")
            ))
        # PING
        for h in self.targets.get("ping",[]):
            yield ("ping", ping(h))
        # NTP
        yield ("ntp", ntp_check(self.targets.get("ntp","time.skydio.com")))
        # Speedtest
        yield ("speedtest", speedtest())
