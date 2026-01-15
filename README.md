# Skydio Network Readiness Tester v2.0

A comprehensive network testing tool for validating Skydio Dock network requirements. Features enhanced testing that matches actual Dock/External Radio communication patterns, plus kiosk mode support for Raspberry Pi with 3.5" touchscreen displays.

## 🆕 Version 2.0 Highlights

- **🖥️ Kiosk Mode**: Auto-boot to network tester on 3.5" touchscreen displays
- **📱 Mobile UI**: Touch-optimized interface for small screens (480x320)
- **🔒 Enhanced Testing**: TLS validation, HTTPS checks, and QUIC protocol testing
- **🎯 1:1 Dock Matching**: Tests replicate actual Dock communication patterns
- **📊 Accurate Validation**: Uses Skydio's official bandwidth and latency requirements

## Features

### Testing Capabilities
- **Enhanced TLS Validation**: Verifies SSL/TLS handshakes and certificates like Dock does
- **Full HTTPS Testing**: Complete HTTP/HTTPS validation with certificate checking
- **QUIC Protocol**: Proper QUIC v1 packet format for accurate livestreaming tests
- **UDP Port Ranges**: Tests WebRTC port ranges (40000-41000, 50000-60000)
- **Bandwidth Testing**: Uses Skydio-specific thresholds (20/80 Mbps recommended)
- **Comprehensive Coverage**: All 14 network rules from Skydio documentation

### User Interface
- **Desktop UI**: Full-featured web interface for configuration and detailed results
- **Mobile UI**: Touch-friendly interface optimized for 3.5" displays
- **Real-time Progress**: Live updates with visual progress indicators
- **Export Options**: PDF, CSV, and JSON report formats
- **Test History**: Track results over time

### Deployment Options
- **Standard Mode**: Web-based testing via browser
- **Kiosk Mode**: Auto-boot fullscreen on Raspberry Pi with touchscreen
- **Headless Mode**: API-based testing for automation
- **Service Mode**: Runs as systemd service on boot

## Quick Start

### Option A: Standard Installation (Web UI)

```bash
curl -fsSL https://raw.githubusercontent.com/ryan-blinn/skydio-network-tester/main/scripts/bootstrap_pi.sh | bash
```

```bash
cd ~/skydio-network-tester
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh

# Start the service
sudo systemctl enable skydio-network-tester.service
sudo systemctl start skydio-network-tester.service

# Access at http://<pi-ip>:5001
```

### Option B: Kiosk Mode (3.5" Touchscreen)

```bash
# 1. Install display drivers (if needed)
sudo chmod +x setup_display_drivers.sh
sudo ./setup_display_drivers.sh

# 2. Install application
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh

# 3. Configure kiosk mode
sudo chmod +x setup_kiosk.sh
sudo ./setup_kiosk.sh

# 4. Enable and reboot
sudo systemctl enable skydio-network-tester.service
sudo reboot
```

**See [QUICK_START_KIOSK.md](QUICK_START_KIOSK.md) for detailed kiosk setup.**

Note: If you are using a GoodTFT MHS 3.5\" screen with the `goodtft/LCD-show` drivers (e.g. `MHS35-show`), Raspberry Pi OS **Bullseye (Legacy) 32-bit** is commonly the most reliable.

## Usage

### Web Interface
1. Access the dashboard at `http://<raspberry-pi-ip>:5001`
2. Desktop UI: `http://<raspberry-pi-ip>:5001/`
3. Mobile UI: `http://<raspberry-pi-ip>:5001/mobile`

### Running Tests
1. Click "Start Network Test" to begin
2. Watch real-time progress and results
3. Review categorized test results
4. Export reports in PDF, CSV, or JSON format

### Kiosk Mode
- Touch "▶ Start Test" on the 3.5" display
- Tests run automatically
- Results display in real-time
- System auto-boots to tester on power-up

## Test Types

This tool validates **all required network connectivity** for Skydio Dock operations with enhanced testing that matches actual Dock behavior:

### Enhanced Network Tests (v2.0)

- **DNS Resolution**: Tests connectivity to Skydio cloud services, AWS S3 buckets, u-blox GPS services, and DNS servers
- **TCP Connectivity with TLS Validation**: 
  - Verifies TCP connection establishment
  - Validates TLS handshake and certificates (like Dock does)
  - Tests ports: 443 (HTTPS), 322, 7881, 51334
- **HTTPS Full Validation** (NEW):
  - Complete HTTP/HTTPS request validation
  - Certificate verification (detects SSL inspection)
  - Tests Skydio Cloud, S3 buckets, u-blox services
- **QUIC Protocol** (Enhanced):
  - Proper QUIC v1 packet format
  - Tests UDP port 443 for livestreaming
  - Validates QUIC server responses
- **UDP Port Ranges** (NEW):
  - Tests WebRTC port ranges (40000-41000, 50000-60000)
  - Samples ports to detect firewall blocking
  - Note: Full validation requires active WebRTC session
- **Ping Tests**: Measures network latency and packet loss to Skydio infrastructure
- **NTP Sync**: Validates time synchronization with `time.skydio.com`
- **Speed Test**: Measures bandwidth using Skydio-specific thresholds
  - Minimum: 10 Mbps up / 20 Mbps down
  - Recommended: 20 Mbps up / 80 Mbps down

### Comprehensive Coverage

The tester validates connectivity for **14 network rules** from Skydio documentation:

| Rule | Protocol | Port | Purpose | Test Type |
|------|----------|------|---------|-----------|
| 1 | TCP | 443 | Skydio Cloud | HTTPS ✓ |
| 2 | TCP | 322 | Livestreaming | TCP ✓ |
| 3 | TCP | 7881 | Livestreaming | TCP ✓ |
| 5 | TCP | 443 | Dock to Cloud | HTTPS ✓ |
| 6 | TCP | 51334 | Dock Communication | TCP ✓ |
| 7 | UDP | 443 | QUIC/Livestreaming | QUIC ✓ |
| 9 | UDP | 40000-41000 | Dock WebRTC | UDP Range ✓ |
| 4 | UDP | 50000-60000 | Client WebRTC | UDP Range ✓ |
| 11 | TCP | 443 | AWS S3 | HTTPS ✓ |
| 12 | TCP | 443 | u-blox GPS | HTTPS ✓ |
| 13 | UDP | 53 | DNS | DNS ✓ |
| 14 | UDP | 123 | NTP | NTP ✓ |

**See [NETWORK_REQUIREMENTS.md](NETWORK_REQUIREMENTS.md) for complete endpoint details.**  
**See [ENHANCED_TESTING_GUIDE.md](ENHANCED_TESTING_GUIDE.md) for testing methodology.**

## Configuration

The tool tests comprehensive Skydio network requirements by default. Test targets can be customized in `config.json`:

```json
{
  "targets": {
    "dns": [
      "skydio.com",
      "cloud.skydio.com",
      "skydio-vehicle-data.s3-accelerate.amazonaws.com",
      "skydio-ota-updates.s3-accelerate.amazonaws.com",
      "online-live1.services.u-blox.com",
      "8.8.8.8"
    ],
    "tcp": [
      {"host": "44.237.178.82", "port": 443, "label": "Skydio Cloud IP"},
      {"host": "skydio.com", "port": 443, "label": "Skydio HTTPS"},
      {"host": "52.89.241.109", "port": 322, "label": "Livestream TCP 322"},
      {"host": "34.208.18.168", "port": 7881, "label": "Livestream TCP 7881"},
      {"host": "44.237.178.82", "port": 51334, "label": "Dock Cloud"},
      {"host": "online-live1.services.u-blox.com", "port": 443, "label": "u-blox GPS"}
    ],
    "quic": [
      {"host": "35.166.132.69", "port": 443, "label": "Livestream QUIC"},
      {"host": "skydio.com", "port": 443, "label": "Skydio QUIC"}
    ],
    "ping": ["8.8.8.8", "skydio.com", "44.237.178.82"],
    "ntp": "time.skydio.com"
  }
}
```

See `config.example.json` for the complete configuration template.

## Documentation

### Setup Guides
- **[QUICK_START_KIOSK.md](QUICK_START_KIOSK.md)** - Fast kiosk mode setup (30 minutes)
- **[KIOSK_MODE_SETUP.md](KIOSK_MODE_SETUP.md)** - Complete kiosk mode guide with troubleshooting
- **[RASPBERRY_PI_INSTALL.md](RASPBERRY_PI_INSTALL.md)** - Standard Raspberry Pi installation

### Testing Documentation
- **[ENHANCED_TESTING_GUIDE.md](ENHANCED_TESTING_GUIDE.md)** - Testing methodology and 1:1 Dock matching
- **[NETWORK_REQUIREMENTS.md](NETWORK_REQUIREMENTS.md)** - Complete network requirements and endpoints
- **[TEST_COVERAGE.md](TEST_COVERAGE.md)** - Test coverage details

### Reference
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and migration guide
- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Architecture and technical details

## File Structure

```
skydio-network-tester/
├── app.py                          # Main Flask application
├── network_tests.py                # Enhanced network testing logic
├── report_export.py                # Export functionality (PDF/CSV/JSON)
├── auto_network_tester.py          # Automatic testing on network changes
├── requirements.txt                # Python dependencies
├── config.example.json             # Configuration template
│
├── templates/
│   ├── index.html                  # Desktop UI
│   ├── mobile.html                 # Mobile UI (3.5" optimized)
│   ├── settings.html               # Configuration interface
│   └── history.html                # Test history viewer
│
├── static/                         # CSS, JS, images
│
├── systemd/
│   ├── skydio-network-tester.service        # Standard service
│   └── skydio-network-tester-kiosk.service  # Kiosk mode service
│
├── setup_kiosk.sh                  # Kiosk mode setup script
├── setup_display_drivers.sh        # Display driver installation
├── install_raspberry_pi.sh         # Standard installation script
│
└── Documentation (see above)
```

## Advanced Configuration

### Custom Test Targets

Edit `config.json` to customize test endpoints:

```json
{
  "targets": {
    "https": [
      {"url": "https://custom.example.com", "label": "Custom HTTPS"}
    ],
    "tcp": [
      {"host": "192.168.1.100", "port": 443, "label": "Internal Server", "verify_tls": true}
    ],
    "udp_ranges": [
      {"host": "10.0.0.1", "port_start": 40000, "port_end": 41000, "sample_size": 5, "label": "Custom UDP Range"}
    ]
  }
}
```

### TLS Validation

Enable TLS validation for specific TCP tests:

```json
{
  "tcp": [
    {"host": "cloud.skydio.com", "port": 443, "verify_tls": true, "label": "Skydio Cloud"}
  ]
}
```

### Bandwidth Thresholds

Modify speedtest thresholds in `network_tests.py`:

```python
# Adjust for multiple Dock deployments
if dl >= 80 and ul >= 20:  # 3 Docks
    status = "PASS"
```

## Troubleshooting

### Common Issues

**Tests fail with TLS errors:**
- Check system time (NTP must be working)
- Update CA certificates: `sudo apt-get install ca-certificates`
- Disable SSL inspection on network

**Kiosk mode not starting:**
- Check LightDM: `sudo systemctl status lightdm`
- View logs: `cat ~/.local/share/xorg/Xorg.0.log`
- Verify autostart: `cat ~/.config/openbox/autostart`

**Display not working:**
- SPI: `lsmod | grep fbtft`
- HDMI: `cat /boot/config.txt | grep hdmi`
- Test: `DISPLAY=:0 xrandr`

**Service not running:**
- Status: `sudo systemctl status skydio-network-tester.service`
- Logs: `sudo journalctl -u skydio-network-tester.service -n 50`
- Test manually: `cd ~/skydio-network-tester && source .venv/bin/activate && python3 app.py`

### Getting Help

1. Check relevant documentation in the `/docs` section above
2. Review logs: `sudo journalctl -u skydio-network-tester.service`
3. Verify network connectivity
4. Test individual components manually

## What's New in v2.0

- ✅ Kiosk mode with 3.5" display support
- ✅ Mobile-optimized touch UI
- ✅ Enhanced TLS/certificate validation
- ✅ Full HTTPS testing (detects SSL inspection)
- ✅ Proper QUIC v1 protocol testing
- ✅ UDP port range testing for WebRTC
- ✅ Skydio-specific bandwidth thresholds
- ✅ 1:1 Dock communication pattern matching

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## License

Internal Skydio tool - not for external distribution.
