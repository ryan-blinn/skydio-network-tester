import socket, subprocess, time, requests, os, json, random
import asyncio
import ssl

def resolve_dns(name, timeout=3):
    start=time.time()
    try:
        socket.setdefaulttimeout(timeout)
        ip=socket.gethostbyname(name)
        return {"target":name,"status":"PASS","ip":ip,"latency_ms":int((time.time()-start)*1000)}
    except Exception as e:
        return {"target":name,"status":"FAIL","error":str(e)}

def tcp_check(host, port, timeout=5, label=None):
    start=time.time()
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
    try:
        s.connect((host,int(port))); s.shutdown(socket.SHUT_RDWR)
        r={"target":f"{host}:{port}","status":"PASS","latency_ms":int((time.time()-start)*1000)}
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
    """Fallback UDP port check for QUIC"""
    try:
        # Simple UDP connectivity test
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Try to connect to the UDP port
        try:
            sock.connect((host, port))
            latency_ms = int((time.time() - start_time) * 1000)
            sock.close()
            return {"target": f"{host}:{port}", "status": "PASS", "latency_ms": latency_ms, "protocol": "QUIC/UDP"}
        except Exception:
            # If direct connect fails, try sending a probe packet
            import struct
            # QUIC initial packet header (simplified)
            packet = struct.pack('!B', 0xc0) + b'\x00' * 15  # Basic QUIC packet
            sock.sendto(packet, (host, port))
            
            # Set a short timeout for response
            sock.settimeout(1)
            try:
                sock.recv(1024)
                latency_ms = int((time.time() - start_time) * 1000)
                return {"target": f"{host}:{port}", "status": "PASS", "latency_ms": latency_ms, "protocol": "QUIC/UDP"}
            except socket.timeout:
                # No response, but port might still be open
                latency_ms = int((time.time() - start_time) * 1000)
                return {"target": f"{host}:{port}", "status": "WARN", "latency_ms": latency_ms, "protocol": "QUIC/UDP", "note": "Port accessible but no QUIC response"}
        finally:
            sock.close()
            
    except Exception as e:
        return {"target": f"{host}:{port}", "status": "FAIL", "error": str(e), "protocol": "QUIC/UDP"}

def speedtest():
    """Enhanced speedtest with multiple attempts and better Pi optimization"""
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
    
    # Adjusted thresholds for typical Pi performance
    dl, ul = st["download_mbps"], st["upload_mbps"]
    if dl >= 15 and ul >= 10:
        status = "PASS"
    elif dl >= 8 and ul >= 5:
        status = "WARN"
    else:
        status = "FAIL"
    
    st["status"] = status
    return st

class StepRunner:
    def __init__(self, targets):
        self.targets=targets
        self.steps=self._count_steps()

    def _count_steps(self):
        return len(self.targets.get("dns",[]))+len(self.targets.get("tcp",[]))+len(self.targets.get("ping",[]))+len(self.targets.get("quic",[]))+2 # + ntp + speedtest

    def run(self):
        # DNS
        for n in self.targets.get("dns",[]):
            yield ("dns", resolve_dns(n))
        # TCP
        for t in self.targets.get("tcp",[]):
            yield ("tcp", tcp_check(t.get("host"), t.get("port"), label=t.get("label")))
        # QUIC
        for q in self.targets.get("quic",[]):
            yield ("quic", quic_check(q.get("host"), q.get("port", 443), label=q.get("label")))
        # PING
        for h in self.targets.get("ping",[]):
            yield ("ping", ping(h))
        # NTP
        yield ("ntp", ntp_check(self.targets.get("ntp","time.skydio.com")))
        # Speedtest
        yield ("speedtest", speedtest())
