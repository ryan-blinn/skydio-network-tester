# Skydio Network Readiness Tester - Project Documentation

## Overview

The Skydio Network Readiness Tester is a comprehensive network diagnostic tool designed to validate network connectivity and performance for Skydio drone operations. It runs on Raspberry Pi devices and provides real-time testing, historical tracking, and detailed reporting capabilities.

## Architecture

### Technology Stack

- **Backend**: Flask (Python 3.9+)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **UI Framework**: Font Awesome icons, custom CSS
- **Data Storage**: Local JSON files
- **Network Testing**: Native Python libraries (socket, subprocess, requests, ntplib, netifaces)
- **Report Generation**: FPDF for PDF, CSV module, JSON

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser (Client)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Main Dashboard│  │ Test History │  │   Settings   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/HTTPS (Port 5001)
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application Server                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    app.py (Main)                      │   │
│  │  - Route handlers                                     │   │
│  │  - API endpoints                                      │   │
│  │  - Job management                                     │   │
│  │  - History storage                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Network Testing Modules                  │   │
│  │  ┌────────────────┐  ┌────────────────┐             │   │
│  │  │ network_tests.py│  │report_export.py│             │   │
│  │  │ - DNS tests     │  │ - CSV export   │             │   │
│  │  │ - TCP tests     │  │ - JSON export  │             │   │
│  │  │ - QUIC tests    │  │ - PDF export   │             │   │
│  │  │ - Ping tests    │  └────────────────┘             │   │
│  │  │ - NTP sync      │                                  │   │
│  │  │ - Speed test    │                                  │   │
│  │  └────────────────┘                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Local File System                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ test_history/│  │   exports/   │  │  config.json │      │
│  │ - index.json │  │ - PDF files  │  │              │      │
│  │ - test_*.json│  │ - CSV files  │  │              │      │
│  │              │  │ - JSON files │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Skydio APIs  │  │ DNS Servers  │  │ NTP Servers  │      │
│  │ Speed Test   │  │ Public IPs   │  │ Webhooks     │      │
│  │ Databricks   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
windsurf-project/
├── app.py                          # Main Flask application
├── network_tests.py                # Network testing logic
├── report_export.py                # Export functionality (CSV, JSON, PDF)
├── excel_config_parser.py          # Configuration parser
├── databricks_integration.py       # Databricks API integration
├── auto_network_tester.py          # Automated testing daemon
├── config.json                     # Application configuration
├── requirements.txt                # Python dependencies
│
├── templates/                      # HTML templates
│   ├── index.html                  # Main dashboard
│   ├── history.html                # Test history page
│   └── settings.html               # Settings/configuration page
│
├── static/                         # Static assets
│   ├── css/
│   │   ├── styles.css              # Main styles
│   │   ├── settings.css            # Settings page styles
│   │   └── history.css             # History page styles
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── settings.js             # Settings page logic
│   │   └── history.js              # History page logic
│   └── images/
│       └── skydio-logo-white.svg   # Branding
│
├── test_history/                   # Test result storage
│   ├── index.json                  # History index
│   └── test_*.json                 # Individual test results
│
├── exports/                        # Exported reports
│   ├── *.pdf                       # PDF reports
│   ├── *.csv                       # CSV reports
│   └── *.json                      # JSON reports
│
└── systemd/                        # System service files
    └── skydio-tester.service       # Systemd service definition
```

## Network Testing Implementation

### 1. DNS Resolution Tests (`network_tests.py`)

**Purpose**: Verify DNS resolution for critical Skydio domains and public DNS servers.

**Test Targets**:
- `skydio.com`
- `cloud.skydio.com`
- `google.com`
- `8.8.8.8` (Google DNS)

**Implementation**:
```python
def test_dns(target):
    - Uses socket.getaddrinfo() for DNS lookups
    - Measures latency in milliseconds
    - Returns resolved IP address
    - Handles timeout (5 seconds)
```

**Data Collected**:
- Target domain/IP
- Resolved IP address
- Latency (ms)
- Status (PASS/FAIL)
- Error messages (if any)

**Network Path**: Client → Local DNS → Upstream DNS → Target Domain

---

### 2. TCP Connectivity Tests

**Purpose**: Verify TCP connection establishment to Skydio services.

**Test Targets**:
- `skydio.com:443` (HTTPS)
- `cloud.skydio.com:443` (HTTPS)

**Implementation**:
```python
def test_tcp(host, port):
    - Uses socket.create_connection()
    - Measures connection latency
    - Timeout: 5 seconds
    - Tests port 443 (HTTPS)
```

**Data Collected**:
- Host and port
- Connection status
- Latency (ms)
- Service label
- Error details

**Network Path**: Client → Firewall → Internet → Skydio Servers (Port 443)

---

### 3. QUIC Protocol Tests

**Purpose**: Verify HTTP/3 (QUIC) connectivity to Skydio services.

**Test Targets**:
- `skydio.com:443` (UDP)
- `cloud.skydio.com:443` (UDP)

**Implementation**:
```python
def test_quic(host, port):
    - Uses HTTP/3 requests
    - Tests UDP port 443
    - Fallback to HTTP/2 if unavailable
```

**Data Collected**:
- Host and port
- Protocol status
- Error details

**Network Path**: Client → Firewall (UDP 443) → Internet → Skydio Servers

---

### 4. Ping Tests

**Purpose**: Measure network latency and packet loss to key internet endpoints.

**Test Targets**:
- `8.8.8.8` (Google DNS)
- `1.1.1.1` (Cloudflare DNS)
- `skydio.com`

**Implementation**:
```python
def test_ping(target):
    - Uses subprocess to run system ping command
    - Sends 4 ICMP packets
    - Parses output for statistics
```

**Data Collected**:
- Average latency (ms)
- Minimum latency (ms)
- Maximum latency (ms)
- Packet loss percentage
- Raw ping output

**Network Path**: Client → Router → Internet → Target Host (ICMP)

---

### 5. NTP Time Synchronization

**Purpose**: Verify time synchronization with NTP servers (critical for drone operations).

**Test Target**:
- `time.skydio.com` (or configured NTP server)

**Implementation**:
```python
def test_ntp(server):
    - Uses ntplib.NTPClient()
    - Requests time from NTP server
    - Calculates offset from local time
```

**Data Collected**:
- NTP server address
- Time offset (ms)
- Sync status (PASS/FAIL)
- Error details

**Network Path**: Client → Firewall (UDP 123) → NTP Server

---

### 6. Speed Test

**Purpose**: Measure available bandwidth for data transfer.

**Implementation**:
```python
def test_speed():
    - Primary: Ookla Speedtest CLI
    - Fallback: Cloudflare Speed Test API
    - Tests download and upload speeds
```

**Thresholds**:
- **PASS**: ≥20 Mbps download
- **WARN**: 10-20 Mbps download
- **FAIL**: <10 Mbps download

**Data Collected**:
- Download speed (Mbps)
- Upload speed (Mbps)
- Test method used
- Status (PASS/WARN/FAIL)

**Network Path**: Client → ISP → Speed Test Server

---

## Data Flow

### Test Execution Flow

1. **User Initiates Test** (Web UI)
   - Click "Start Network Test" button
   - Frontend sends POST to `/api/start`

2. **Backend Creates Job**
   - Generates unique job ID
   - Creates background thread
   - Returns job ID to frontend

3. **Test Execution** (`_run_job()`)
   - Loads test targets from config
   - Creates `StepRunner` instance
   - Executes tests sequentially:
     - DNS tests (parallel for multiple targets)
     - TCP tests (parallel for multiple targets)
     - QUIC tests (parallel for multiple targets)
     - Ping tests (sequential)
     - NTP test
     - Speed test
   - Updates progress after each test
   - Stores results in memory

4. **Progress Polling** (Frontend)
   - Polls `/api/status/<job_id>` every 500ms
   - Updates progress bar
   - Displays results as they complete

5. **Test Completion**
   - Saves results to test history
   - Stores in `test_history/test_<timestamp>.json`
   - Updates history index
   - Auto-exports if configured
   - Auto-pushes to Databricks if configured

6. **Result Display**
   - Frontend renders test cards
   - Shows status indicators (PASS/FAIL/WARN)
   - Displays detailed metrics
   - Enables export options

---

## Security Considerations

### 1. Network Security

**Outbound Connections**:
- **DNS Queries**: UDP port 53 to configured DNS servers
- **HTTPS**: TCP port 443 to Skydio services
- **QUIC**: UDP port 443 to Skydio services
- **ICMP**: Ping packets to test targets
- **NTP**: UDP port 123 to time servers
- **Speed Test**: Various ports to speed test servers

**Firewall Requirements**:
```
ALLOW outbound UDP 53 (DNS)
ALLOW outbound TCP 443 (HTTPS)
ALLOW outbound UDP 443 (QUIC)
ALLOW outbound ICMP (Ping)
ALLOW outbound UDP 123 (NTP)
ALLOW outbound TCP 80, 443, 8080 (Speed tests)
```

**Inbound Connections**:
- **Web Interface**: TCP port 5001 (configurable)
- **Recommendation**: Restrict to local network only
- **Production**: Use reverse proxy with HTTPS (nginx/Apache)

---

### 2. Authentication & Authorization

**Current State**:
- ⚠️ **No authentication** on web interface by default
- ⚠️ **No API key** required for endpoints
- ⚠️ **No rate limiting** on API calls

**Recommendations**:

1. **Enable Basic Authentication**:
   ```python
   # In config.json
   {
     "web_auth_enabled": true,
     "web_username": "admin",
     "web_password": "hashed_password"
   }
   ```

2. **Use Reverse Proxy**:
   ```nginx
   # nginx configuration
   location / {
       auth_basic "Restricted";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://localhost:5001;
   }
   ```

3. **Network Isolation**:
   - Deploy on isolated management VLAN
   - Use VPN for remote access
   - Restrict access via firewall rules

---

### 3. Data Security

**Sensitive Data Stored**:
- ✅ Device hostnames
- ✅ Private IP addresses
- ✅ Public IP addresses
- ✅ Network topology information
- ⚠️ Databricks access tokens (if configured)
- ⚠️ Webhook URLs and auth tokens
- ⚠️ FTP credentials (if configured)

**Storage Locations**:
```
config.json           # Contains credentials (SENSITIVE)
test_history/         # Contains network topology data
exports/              # Contains test reports
```

**Security Measures**:

1. **File Permissions**:
   ```bash
   chmod 600 config.json
   chmod 700 test_history/
   chmod 700 exports/
   ```

2. **Credential Management**:
   - Store Databricks tokens in environment variables
   - Use secrets management system (HashiCorp Vault, AWS Secrets Manager)
   - Rotate credentials regularly

3. **Data Retention**:
   - Test history limited to 100 most recent tests
   - Automatic cleanup of old exports
   - Consider encryption at rest for sensitive deployments

---

### 4. Code Execution Risks

**Subprocess Calls**:
```python
# network_tests.py - Ping test
subprocess.run(['ping', '-c', '4', target], ...)

# app.py - System commands
subprocess.run(['sudo', 'hostnamectl', 'set-hostname', hostname], ...)
subprocess.run(['sudo', 'shutdown', '-r', '+1'], ...)
```

**Risks**:
- ⚠️ Command injection if user input not sanitized
- ⚠️ Requires sudo privileges for system commands
- ⚠️ Potential for privilege escalation

**Mitigations**:
1. **Input Validation**:
   - Whitelist allowed characters for hostnames
   - Validate IP addresses with regex
   - Sanitize all user inputs

2. **Sudo Configuration**:
   ```bash
   # /etc/sudoers.d/skydio-tester
   skydio ALL=(ALL) NOPASSWD: /usr/bin/hostnamectl
   skydio ALL=(ALL) NOPASSWD: /usr/sbin/shutdown
   ```

3. **Principle of Least Privilege**:
   - Run Flask app as non-root user
   - Only elevate for specific commands
   - Use systemd for service management

---

### 5. Third-Party Integrations

**External Services**:
- Databricks (SQL warehouse access)
- Webhooks (HTTP POST to arbitrary URLs)
- FTP servers (file uploads)
- Speed test services (Ookla, Cloudflare)

**Security Considerations**:

1. **Databricks**:
   - Uses personal access tokens (PAT)
   - Tokens stored in config.json
   - **Risk**: Token exposure if config compromised
   - **Mitigation**: Use short-lived tokens, rotate regularly

2. **Webhooks**:
   - Sends test results to configured URLs
   - **Risk**: Data exfiltration to malicious endpoints
   - **Mitigation**: Whitelist allowed webhook domains

3. **FTP**:
   - Stores credentials in plaintext
   - **Risk**: Credential theft
   - **Mitigation**: Use SFTP/FTPS, store credentials securely

---

### 6. Web Application Security

**Vulnerabilities to Consider**:

1. **Cross-Site Scripting (XSS)**:
   - ✅ No user-generated content displayed
   - ✅ All data sanitized before rendering
   - ⚠️ Test results could contain malicious data

2. **Cross-Site Request Forgery (CSRF)**:
   - ⚠️ No CSRF protection implemented
   - **Risk**: Unauthorized actions via malicious sites
   - **Mitigation**: Implement CSRF tokens

3. **Injection Attacks**:
   - ✅ No SQL database (uses JSON files)
   - ⚠️ Command injection possible in system calls
   - **Mitigation**: Input validation and sanitization

4. **Information Disclosure**:
   - ⚠️ Debug mode enabled by default
   - ⚠️ Detailed error messages exposed
   - **Mitigation**: Disable debug in production

---

### 7. Deployment Security

**Raspberry Pi Hardening**:

1. **Operating System**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Enable firewall
   sudo ufw enable
   sudo ufw allow 5001/tcp
   sudo ufw allow from 192.168.1.0/24 to any port 5001
   
   # Disable unnecessary services
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   ```

2. **SSH Security**:
   ```bash
   # Disable password authentication
   sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   
   # Use SSH keys only
   # Change default SSH port
   sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
   ```

3. **Application Security**:
   ```bash
   # Run as dedicated user
   sudo useradd -r -s /bin/false skydio-tester
   
   # Set file ownership
   sudo chown -R skydio-tester:skydio-tester /opt/skydio-tester
   
   # Restrict permissions
   sudo chmod 750 /opt/skydio-tester
   sudo chmod 600 /opt/skydio-tester/config.json
   ```

---

## Configuration

### config.json Structure

```json
{
  "auto_test_enabled": false,
  "max_auto_tests": 3,
  "test_interval_seconds": 300,
  "auto_export_enabled": false,
  "auto_export_format": "pdf",
  "webhook_enabled": false,
  "webhook_url": "",
  "web_port": 5001,
  "cloud_push": {
    "enabled": false,
    "api_url": "",
    "api_key": "",
    "site_label": ""
  },
  "databricks": {
    "enabled": false,
    "workspace_url": "",
    "access_token": "",
    "warehouse_id": "",
    "database": "network_tests",
    "table": "test_results",
    "auto_push": false
  },
  "targets": {
    "dns": ["skydio.com", "cloud.skydio.com", "google.com", "8.8.8.8"],
    "tcp": [
      {"host": "skydio.com", "port": 443, "label": "Skydio Main HTTPS"},
      {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud HTTPS"}
    ],
    "quic": [
      {"host": "skydio.com", "port": 443, "label": "Skydio Main QUIC"},
      {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud QUIC"}
    ],
    "ping": ["skydio.com", "8.8.8.8", "1.1.1.1"],
    "ntp": "time.skydio.com"
  }
}
```

---

## API Endpoints

### Test Management

- `POST /api/start` - Start new network test
- `GET /api/status/<job_id>` - Get test progress and results
- `GET /api/export/<format>` - Export results (csv/json/pdf)

### Device Information

- `GET /api/info` - Get device name and IPs
- `GET /api/device-info` - Get comprehensive device info
- `GET /api/system-status` - Get system resource usage

### Test History

- `GET /api/history` - Get all test history
- `GET /api/history/<timestamp>` - Get specific test details
- `DELETE /api/history/<timestamp>` - Delete specific test
- `POST /api/history/clear` - Clear all history

### Configuration

- `GET /api/settings` - Get current settings
- `POST /api/settings/test` - Update test configuration
- `POST /api/settings/export` - Update export configuration
- `POST /api/settings/databricks` - Update Databricks config

### System Control

- `POST /api/system/hostname` - Update hostname
- `POST /api/system/reboot` - Reboot system
- `POST /api/system/factory-reset` - Factory reset

---

## Performance Considerations

### Resource Usage

**CPU**:
- Idle: ~5-10%
- During test: ~30-50%
- Speed test: ~60-80%

**Memory**:
- Base: ~100 MB
- During test: ~150 MB
- With history: ~200 MB

**Disk**:
- Application: ~50 MB
- Test history (100 tests): ~10 MB
- Exports: Varies by format

**Network**:
- DNS tests: <1 KB per test
- TCP tests: <1 KB per test
- Ping tests: ~100 bytes per packet
- Speed test: Up to 1 GB (depending on connection)

### Optimization Tips

1. **Limit History**: Keep only recent tests (default: 100)
2. **Scheduled Tests**: Use cron instead of continuous polling
3. **Export Cleanup**: Regularly delete old export files
4. **Database**: Consider SQLite for large deployments

---

## Troubleshooting

### Common Issues

1. **Tests Fail with Timeout**:
   - Check firewall rules
   - Verify DNS resolution
   - Test network connectivity manually

2. **Speed Test Fails**:
   - Install Ookla CLI: `sudo apt install speedtest-cli`
   - Check Cloudflare API availability
   - Verify sufficient bandwidth

3. **NTP Sync Fails**:
   - Check UDP port 123 is open
   - Verify NTP server is reachable
   - Try alternative NTP servers

4. **Permission Denied Errors**:
   - Check file permissions
   - Verify sudo configuration
   - Run as correct user

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor test results
- Check system resources
- Review error logs

**Weekly**:
- Clean up old exports
- Review test history
- Update test targets if needed

**Monthly**:
- Update system packages
- Rotate credentials
- Review security logs
- Backup configuration

**Quarterly**:
- Update application code
- Review and update firewall rules
- Audit access logs
- Test disaster recovery

---

## License & Support

**Project**: Skydio Network Readiness Tester
**Purpose**: Network diagnostics for Skydio drone operations
**Platform**: Raspberry Pi (Debian/Ubuntu Linux)
**Python Version**: 3.9+

For issues or questions, refer to the project repository or contact the development team.
