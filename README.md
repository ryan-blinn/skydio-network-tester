# Skydio Network Readiness Tester

A modern, intuitive dashboard for testing network readiness on Raspberry Pi devices. This tool aims to replace C93 testing methods by providing a comprehensive web-based interface for network connectivity testing.

## Features

- **Modern UI**: Clean, Skydio-branded interface with intuitive pass/fail indicators
- **Real-time Testing**: Live progress updates and expandable test result details
- **Comprehensive Tests**: DNS resolution, TCP connectivity, ping tests, NTP sync, and speed tests
- **Export Options**: Results can be exported in PDF, CSV, and JSON formats
- **Responsive Design**: Works on desktop and mobile devices
- **Raspberry Pi Optimized**: Designed specifically for Raspberry Pi deployment

## Installation

1. **Clone or copy the project files to your Raspberry Pi**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create necessary directories:**
   ```bash
   mkdir -p /opt/skydio-readiness/exports
   ```

4. **Update the app.py paths if needed:**
   - Modify `APP_ROOT`, `TEMPLATES`, `STATIC`, and `EXPORTS` paths in `app.py` to match your deployment location

## Usage

1. **Start the Flask application:**
   ```bash
   python app.py
   ```

2. **Access the dashboard:**
   - Open your browser to `http://localhost:5000` (or your Raspberry Pi's IP address)

3. **Run network tests:**
   - Click "Start Network Test" to begin comprehensive network testing
   - Watch real-time progress and results
   - Click on test cards to expand and view detailed results
   - Export results in your preferred format

## Test Types

This tool validates **all required network connectivity** for Skydio Dock operations:

- **DNS Resolution**: Tests connectivity to Skydio cloud services, AWS S3 buckets, u-blox GPS services, and DNS servers
- **TCP Connectivity**: Verifies access to:
  - Skydio Cloud (port 443)
  - Livestreaming services (ports 322, 7881, 51334)
  - AWS S3 storage buckets (port 443)
  - u-blox AssistNow GPS assistance (port 443)
- **QUIC Protocol**: Tests HTTP/3 connectivity for livestreaming (UDP port 443)
- **Ping Tests**: Measures network latency and packet loss to Skydio infrastructure
- **NTP Sync**: Validates time synchronization with `time.skydio.com`
- **Speed Test**: Measures available bandwidth (≥20 Mbps recommended)

### Comprehensive Coverage

The tester validates connectivity for **14 network rules** including:
- ✅ Client workstations to Skydio Cloud
- ✅ Livestreaming infrastructure (TCP 322, 7881)
- ✅ Dock to Skydio Cloud (TCP 443, 51334)
- ✅ QUIC/WebRTC livestreaming (UDP 443)
- ✅ AWS S3 buckets (vehicle data, flight data, OTA updates, media)
- ✅ u-blox GPS AssistNow services
- ✅ DNS resolution (UDP 53)
- ✅ NTP time synchronization (UDP 123)

**See [NETWORK_REQUIREMENTS.md](NETWORK_REQUIREMENTS.md) for complete details on all tested endpoints.**

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

## File Structure

```
skydio-readiness-tester/
├── app.py                 # Main Flask application
├── network_tests.py       # Network testing logic
├── report_export.py       # Export functionality
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main dashboard template
├── static/
│   ├── css/
│   │   └── styles.css    # Skydio-branded styling
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file
```

## Customization

- **Branding**: Modify CSS variables in `styles.css` to adjust colors and styling
- **Test Targets**: Update `DEFAULT_TARGETS` in `app.py` to change test endpoints
- **Export Formats**: Extend `report_export.py` to add new export formats
- **UI Layout**: Modify `templates/index.html` to adjust the dashboard layout

## Raspberry Pi Deployment

For production deployment on Raspberry Pi:

1. **Install as a service** (optional):
   ```bash
   sudo systemctl enable skydio-readiness
   sudo systemctl start skydio-readiness
   ```

2. **Configure firewall** to allow access on port 5000

3. **Set up auto-start** on boot if needed

## Troubleshooting

- Ensure all required Python packages are installed
- Check that the export directory has write permissions
- Verify network connectivity for external test targets
- Check Flask logs for detailed error information

## License

Internal Skydio tool - not for external distribution.
