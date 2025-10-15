# Skydio Network Readiness Tester

A modern, intuitive dashboard for testing network readiness on Raspberry Pi devices. This tool replaces older dock hardware methods by providing a comprehensive web-based interface for network connectivity testing.

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

- **DNS Resolution**: Tests connectivity to Skydio cloud services and common DNS servers
- **TCP Connectivity**: Verifies specific ports are accessible (HTTPS, WebRTC)
- **Ping Tests**: Measures network latency to key servers
- **NTP Sync**: Checks time synchronization capability
- **Speed Test**: Measures available bandwidth

## Configuration

Default test targets are defined in `app.py`:

```python
DEFAULT_TARGETS = {
  "dns": ["cloud.skydio.com","time.skydio.com","google.com","u-blox.com"],
  "tcp": [
    {"host":"cloud.skydio.com","port":443,"label":"Skydio Cloud HTTPS"},
    {"host":"cloud.skydio.com","port":322,"label":"WebRTC TCP 322"},
    {"host":"cloud.skydio.com","port":7881,"label":"WebRTC TCP 7881"},
    {"host":"www.google.com","port":443,"label":"Generic HTTPS"}
  ],
  "ping": ["8.8.8.8","1.1.1.1","cloud.skydio.com"],
  "ntp": "time.skydio.com"
}
```

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
