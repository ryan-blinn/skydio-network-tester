# Skydio Network Readiness Tester

A comprehensive network diagnostic tool for validating network connectivity and performance for Skydio drone operations. Designed to run on Raspberry Pi devices with a modern web interface.

![Skydio Logo](static/images/skydio-logo-white.svg)

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi (3B+ or newer) or any Linux system
- Python 3.9 or higher
- Network connectivity
- Sudo privileges (for system commands)

### Installation

1. **Clone or download the project**:
   ```bash
   cd /opt
   sudo git clone <repository-url> skydio-tester
   cd skydio-tester
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Install system dependencies**:
   ```bash
   # For Raspberry Pi
   sudo apt update
   sudo apt install -y speedtest-cli ntpdate
   ```

4. **Set permissions**:
   ```bash
   sudo chmod +x deploy.sh
   sudo chmod 600 config.json  # Protect sensitive config
   ```

5. **Run the application**:
   ```bash
   python3 app.py
   ```

6. **Access the web interface**:
   - Local: http://localhost:5001
   - Network: http://<raspberry-pi-ip>:5001

### Quick Deploy (Systemd Service)

```bash
sudo ./deploy.sh
sudo systemctl enable skydio-tester
sudo systemctl start skydio-tester
sudo systemctl status skydio-tester
```

---

## 📋 Features

### Network Testing

- ✅ **DNS Resolution**: Test domain name lookups with latency measurement
- ✅ **TCP Connectivity**: Verify HTTPS connections to Skydio services
- ✅ **QUIC Protocol**: Test HTTP/3 connectivity
- ✅ **Ping Tests**: Measure network latency and packet loss
- ✅ **NTP Synchronization**: Verify time sync (critical for drones)
- ✅ **Speed Test**: Measure download/upload bandwidth

### User Interface

- 🎨 **Modern Dashboard**: Real-time test execution with progress tracking
- 📊 **Test History**: View and search past test results
- ⚙️ **Settings Panel**: Configure tests, exports, and integrations
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

### Data Management

- 💾 **Local Storage**: Automatic test history (last 100 tests)
- 📄 **Export Formats**: PDF, CSV, and JSON reports
- 🔄 **Auto-Export**: Automatic report generation after tests
- 📤 **Cloud Integration**: Push results to Databricks or webhooks

### System Features

- 🍓 **Raspberry Pi Optimized**: Lightweight and efficient
- 🔧 **System Control**: Reboot, hostname management, factory reset
- 📈 **Resource Monitoring**: CPU, memory, disk, and uptime tracking
- 🔐 **Network Info**: Display private and public IP addresses

---

## 🧪 Network Tests Explained

### 1. DNS Resolution
**What it tests**: Can the device resolve domain names to IP addresses?

**Why it matters**: Drones need to resolve Skydio cloud services to connect.

**Targets**:
- `skydio.com`
- `cloud.skydio.com`
- `google.com`
- `8.8.8.8`

**Pass criteria**: Domain resolves within 5 seconds

---

### 2. TCP Connectivity
**What it tests**: Can the device establish HTTPS connections?

**Why it matters**: Drones communicate with Skydio cloud over HTTPS (port 443).

**Targets**:
- `skydio.com:443`
- `cloud.skydio.com:443`

**Pass criteria**: Connection established within 5 seconds

---

### 3. QUIC Protocol
**What it tests**: Can the device use HTTP/3 (QUIC) protocol?

**Why it matters**: QUIC provides faster, more reliable connections for drone telemetry.

**Targets**:
- `skydio.com:443` (UDP)
- `cloud.skydio.com:443` (UDP)

**Pass criteria**: QUIC handshake successful

---

### 4. Ping Tests
**What it tests**: Network latency and packet loss to key endpoints.

**Why it matters**: High latency or packet loss can cause drone control issues.

**Targets**:
- `8.8.8.8` (Google DNS)
- `1.1.1.1` (Cloudflare DNS)
- `skydio.com`

**Pass criteria**: <100ms average latency, <5% packet loss

---

### 5. NTP Time Sync
**What it tests**: Can the device synchronize time with NTP servers?

**Why it matters**: Accurate time is critical for flight logs and GPS coordination.

**Target**:
- `time.skydio.com`

**Pass criteria**: Time offset <1000ms

---

### 6. Speed Test
**What it tests**: Available download and upload bandwidth.

**Why it matters**: Sufficient bandwidth needed for video streaming and telemetry.

**Thresholds**:
- **PASS**: ≥20 Mbps download
- **WARN**: 10-20 Mbps download
- **FAIL**: <10 Mbps download

**Methods**: Ookla Speedtest CLI (primary), Cloudflare API (fallback)

---

## 📁 Project Structure

```
skydio-tester/
├── app.py                      # Main Flask application
├── network_tests.py            # Network testing logic
├── report_export.py            # Export functionality
├── databricks_integration.py   # Databricks API client
├── excel_config_parser.py      # Configuration parser
├── auto_network_tester.py      # Automated testing daemon
├── config.json                 # Application configuration
├── requirements.txt            # Python dependencies
│
├── templates/                  # HTML templates
│   ├── index.html             # Main dashboard
│   ├── history.html           # Test history
│   └── settings.html          # Settings page
│
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript
│   └── images/                # Images and logos
│
├── test_history/              # Test result storage
│   ├── index.json            # History index
│   └── test_*.json           # Individual tests
│
├── exports/                   # Exported reports
│   ├── *.pdf                 # PDF reports
│   ├── *.csv                 # CSV reports
│   └── *.json                # JSON reports
│
└── systemd/                   # System service files
    └── skydio-tester.service # Systemd service
```

---

## ⚙️ Configuration

### Basic Configuration

Edit `config.json` to customize behavior:

```json
{
  "web_port": 5001,
  "auto_test_enabled": false,
  "auto_export_enabled": false,
  "auto_export_format": "pdf"
}
```

### Test Targets

Customize which endpoints to test:

```json
{
  "targets": {
    "dns": ["skydio.com", "cloud.skydio.com", "google.com"],
    "tcp": [
      {"host": "skydio.com", "port": 443, "label": "Skydio Main"}
    ],
    "ping": ["8.8.8.8", "1.1.1.1"],
    "ntp": "time.skydio.com"
  }
}
```

### Databricks Integration

Push test results to Databricks:

```json
{
  "databricks": {
    "enabled": true,
    "workspace_url": "https://your-workspace.cloud.databricks.com",
    "access_token": "your-token",
    "warehouse_id": "your-warehouse-id",
    "database": "network_tests",
    "table": "test_results",
    "auto_push": true
  }
}
```

### Webhook Integration

Send results to external services:

```json
{
  "webhook_enabled": true,
  "webhook_url": "https://your-server.com/webhook",
  "webhook_auth": "Bearer your-token"
}
```

---

## 🔒 Security Considerations

### Network Security

**Required Firewall Rules**:
```bash
# Outbound (required for tests)
ALLOW UDP 53        # DNS
ALLOW TCP 443       # HTTPS
ALLOW UDP 443       # QUIC
ALLOW ICMP          # Ping
ALLOW UDP 123       # NTP

# Inbound (web interface)
ALLOW TCP 5001      # Web UI (restrict to local network)
```

### Application Security

**Recommendations**:

1. **Restrict Web Access**:
   ```bash
   # Only allow local network
   sudo ufw allow from 192.168.1.0/24 to any port 5001
   ```

2. **Use Reverse Proxy** (Production):
   ```nginx
   server {
       listen 443 ssl;
       server_name tester.example.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Protect Configuration**:
   ```bash
   chmod 600 config.json
   chmod 700 test_history/
   chmod 700 exports/
   ```

4. **Run as Non-Root**:
   ```bash
   sudo useradd -r -s /bin/false skydio-tester
   sudo chown -R skydio-tester:skydio-tester /opt/skydio-tester
   ```

### Data Security

**Sensitive Data**:
- ⚠️ Private IP addresses
- ⚠️ Public IP addresses
- ⚠️ Network topology
- ⚠️ Databricks tokens
- ⚠️ Webhook credentials

**Protection**:
- Store credentials in environment variables
- Use secrets management (Vault, AWS Secrets Manager)
- Rotate tokens regularly
- Enable encryption at rest for sensitive deployments

---

## 🔧 API Reference

### Test Management

#### Start Test
```http
POST /api/start
Response: {"job_id": "job-1234567890"}
```

#### Get Test Status
```http
GET /api/status/<job_id>
Response: {
  "progress": 75,
  "done": false,
  "results": {...}
}
```

#### Export Results
```http
GET /api/export/pdf
GET /api/export/csv
GET /api/export/json
Response: {"success": true, "file": "report.pdf"}
```

### Test History

#### Get All History
```http
GET /api/history
Response: [
  {
    "timestamp": 1234567890,
    "datetime": "2025-10-15 07:00:00",
    "private_ip": "192.168.1.100",
    "public_ip": "1.2.3.4",
    "summary": {...}
  }
]
```

#### Get Test Details
```http
GET /api/history/<timestamp>
Response: {
  "timestamp": 1234567890,
  "results": {...}
}
```

#### Delete Test
```http
DELETE /api/history/<timestamp>
Response: {"success": true}
```

#### Clear All History
```http
POST /api/history/clear
Response: {"success": true}
```

### Device Information

#### Get Device Info
```http
GET /api/device-info
Response: {
  "hostname": "skydio-tester",
  "private_ip": "192.168.1.100",
  "public_ip": "1.2.3.4",
  "platform": "Linux-5.10.0",
  "cpu_usage": 15.2,
  "memory_usage": 45.8,
  "disk_usage": 32.1,
  "temperature": "45.5°C"
}
```

#### Get System Status
```http
GET /api/system-status
Response: {
  "cpu_usage": 15.2,
  "memory_usage": 45.8,
  "disk_usage": 32.1,
  "uptime": "5d 3h 22m"
}
```

---

## 📊 Report Formats

### PDF Report
- Professional formatted report
- Includes device info, test results, and timestamps
- Suitable for documentation and sharing

### CSV Report
- Tabular format with all test data
- Easy to import into Excel or databases
- Good for data analysis

### JSON Report
- Complete test data in structured format
- Includes all metadata and raw results
- Ideal for programmatic processing

**Report Contents**:
- Device name and hostname
- Private IP address
- Public IP address
- Site label (optional)
- Timestamp
- All test results with status and metrics

---

## 🐛 Troubleshooting

### Tests Fail with Timeout

**Symptoms**: All tests show FAIL with timeout errors

**Causes**:
- Firewall blocking outbound connections
- DNS not configured
- Network cable unplugged

**Solutions**:
```bash
# Check network connectivity
ping 8.8.8.8

# Check DNS
nslookup skydio.com

# Check firewall
sudo ufw status

# Test manually
curl -I https://skydio.com
```

---

### Speed Test Fails

**Symptoms**: Speed test shows FAIL or "Command not found"

**Causes**:
- Speedtest CLI not installed
- Cloudflare API unreachable

**Solutions**:
```bash
# Install Speedtest CLI
sudo apt install speedtest-cli

# Test manually
speedtest-cli --simple

# Check Cloudflare
curl https://speed.cloudflare.com
```

---

### NTP Sync Fails

**Symptoms**: NTP test shows FAIL

**Causes**:
- UDP port 123 blocked
- NTP server unreachable
- System time too far off

**Solutions**:
```bash
# Check NTP manually
ntpdate -q time.skydio.com

# Check firewall
sudo ufw allow 123/udp

# Sync time manually
sudo ntpdate time.skydio.com
```

---

### Permission Denied Errors

**Symptoms**: "Permission denied" when running system commands

**Causes**:
- Running as wrong user
- Sudo not configured
- File permissions incorrect

**Solutions**:
```bash
# Check current user
whoami

# Configure sudo (add to /etc/sudoers.d/skydio-tester)
skydio-tester ALL=(ALL) NOPASSWD: /usr/bin/hostnamectl
skydio-tester ALL=(ALL) NOPASSWD: /usr/sbin/shutdown

# Fix file permissions
sudo chown -R skydio-tester:skydio-tester /opt/skydio-tester
sudo chmod 755 /opt/skydio-tester
sudo chmod 600 /opt/skydio-tester/config.json
```

---

### Web Interface Not Loading

**Symptoms**: Cannot access http://localhost:5001

**Causes**:
- Application not running
- Port already in use
- Firewall blocking

**Solutions**:
```bash
# Check if running
ps aux | grep app.py

# Check port
sudo lsof -i :5001

# Start application
python3 app.py

# Check firewall
sudo ufw allow 5001/tcp

# Check logs
journalctl -u skydio-tester -f
```

---

## 📈 Performance

### Resource Requirements

**Minimum**:
- CPU: 1 GHz single-core
- RAM: 512 MB
- Disk: 1 GB free space
- Network: 1 Mbps

**Recommended**:
- CPU: 1.4 GHz quad-core (Raspberry Pi 4)
- RAM: 2 GB
- Disk: 8 GB free space
- Network: 10 Mbps

### Resource Usage

**Idle**:
- CPU: 5-10%
- Memory: 100 MB
- Disk I/O: Minimal

**During Test**:
- CPU: 30-50% (80% during speed test)
- Memory: 150 MB
- Network: Up to 1 GB (speed test)

### Optimization Tips

1. **Limit Test History**: Keep only 50-100 recent tests
2. **Schedule Tests**: Use cron for periodic testing instead of continuous
3. **Clean Exports**: Regularly delete old export files
4. **Disable Debug**: Set `debug=False` in production

---

## 🔄 Maintenance

### Daily Tasks
- ✅ Monitor test results
- ✅ Check system resources
- ✅ Review error logs

### Weekly Tasks
- ✅ Clean up old exports
- ✅ Review test history
- ✅ Update test targets if needed

### Monthly Tasks
- ✅ Update system packages
- ✅ Rotate credentials
- ✅ Review security logs
- ✅ Backup configuration

### Quarterly Tasks
- ✅ Update application code
- ✅ Review firewall rules
- ✅ Audit access logs
- ✅ Test disaster recovery

---

## 📝 Changelog

### Version 2.0 (Current)
- ✨ Added test history with local storage
- ✨ Added "More" dropdown navigation menu
- ✨ Display private IP address instead of hostname
- ✨ Changed icon to Raspberry Pi
- ✨ Private IP included in all exports
- ✨ Enhanced search functionality
- 🐛 Fixed various UI bugs

### Version 1.0
- 🎉 Initial release
- ✅ DNS, TCP, QUIC, Ping, NTP, Speed tests
- ✅ PDF, CSV, JSON exports
- ✅ Databricks integration
- ✅ Webhook support
- ✅ System control features

---

## 🤝 Contributing

This project is designed for Skydio network diagnostics. For issues or feature requests, contact the development team.

---

## 📄 License

Proprietary - Skydio, Inc.

---

## 📞 Support

For technical support or questions:
- Review the [Project Documentation](PROJECT_DOCUMENTATION.md)
- Check the [Troubleshooting](#-troubleshooting) section
- Contact your Skydio representative

---

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Font Awesome**: Icons
- **FPDF**: PDF generation
- **ntplib**: NTP client
- **netifaces**: Network interface detection
- **psutil**: System monitoring

---

**Made with ❤️ for Skydio drone operations**
