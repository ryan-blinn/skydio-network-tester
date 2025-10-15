import os, csv, json, time
from fpdf import FPDF

def _safe(s): 
    if not s: return "unknown"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    return ''.join(ch for ch in str(s) if ch in allowed) or "unknown"

def _base(ts, meta):
    ip = _safe((meta or {}).get("public_ip"))
    site = (meta or {}).get("site_label")
    base = f"skydio-readiness-{ip}-{ts}"
    if site: base += f"-{_safe(site)}"
    return base

def export_csv(data, outdir, ts):
    os.makedirs(outdir, exist_ok=True)
    meta = data.get("_meta") or {}
    path = os.path.join(outdir, _base(ts, meta)+".csv")
    with open(path,"w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["Skydio Network Readiness Report"])
        w.writerow([f"Device: {meta.get('device_name','unknown')}  Private IP: {meta.get('private_ip','unknown')}  Public IP: {meta.get('public_ip','unknown')}  Site: {meta.get('site_label','-')}"])
        w.writerow([]); w.writerow(["Section","Target","Status","Notes"])
        for r in data.get("dns",[]): w.writerow(["DNS", r.get("target"), r.get("status"), r.get("ip") or r.get("error","")])
        for r in data.get("tcp",[]): w.writerow(["TCP", r.get("target"), r.get("status"), r.get("label","") or r.get("error","")])
        for r in data.get("ping",[]): w.writerow(["PING", r.get("target"), r.get("status"), r.get("output","") or r.get("error","")])
        if data.get("ntp"): n=data["ntp"]; w.writerow(["NTP", n.get("target"), n.get("status"), str(n.get("offset_ms") or n.get("error",""))])
        st = data.get("speedtest") or {}
        if st: w.writerow(["SPEEDTEST", "Ookla/Cloudflare", st.get("status","FAIL"), f"Down {st.get('download_mbps','-')} Mbps - Up {st.get('upload_mbps','-')} Mbps"])
    return path

def export_json(data, outdir, ts):
    os.makedirs(outdir, exist_ok=True)
    meta = data.get("_meta") or {}
    path = os.path.join(outdir, _base(ts, meta)+".json")
    with open(path,"w") as f: json.dump(data,f,indent=2)
    return path

def export_pdf(data, outdir, ts):
    os.makedirs(outdir, exist_ok=True)
    meta = data.get("_meta") or {}
    path = os.path.join(outdir, _base(ts, meta)+".pdf")
    pdf=FPDF(); pdf.add_page(); pdf.set_font("Arial","B",16); pdf.cell(0,10,"Skydio Network Readiness Report",ln=True)
    pdf.set_font("Arial", size=12); pdf.ln(4)
    pdf.cell(0, 10, f"Device: {meta.get('device_name','unknown')}  Private IP: {meta.get('private_ip','unknown')}", ln=True)
    pdf.cell(0, 10, f"Public IP: {meta.get('public_ip','unknown')}  Site: {meta.get('site_label','-')}", ln=True)
    pdf.ln(2)
    def line(label, target, status, notes=""): pdf.cell(0,8,f"{label:<14} | {target:<42} | {status:<5} | {notes}",ln=True)
    for r in data.get("dns",[]): line("DNS", r.get("target"), r.get("status"), r.get("ip") or r.get("error",""))
    for r in data.get("tcp",[]): line("TCP", r.get("target"), r.get("status"), r.get("label","") or r.get("error",""))
    for r in data.get("ping",[]): line("PING", r.get("target"), r.get("status"), r.get("output","") or r.get("error",""))
    if data.get("ntp"): n=data["ntp"]; line("NTP", n.get("target"), n.get("status"), str(n.get("offset_ms") or n.get("error","")))
    st = data.get("speedtest") or {}
    if st: line("SPEEDTEST", "Ookla/Cloudflare", st.get("status","FAIL"), f"Down {st.get('download_mbps','-')} Mbps - Up {st.get('upload_mbps','-')} Mbps")
    pdf.output(path); return path
