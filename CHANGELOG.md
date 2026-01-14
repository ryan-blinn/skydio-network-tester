# Changelog

## Version 2.0 - January 2026

### Major Enhancements

#### 🖥️ Kiosk Mode Support
- **3.5" Display Support**: Optimized for Raspberry Pi 3.5" touchscreen displays
- **Auto-Boot**: System automatically boots into network tester on startup
- **Mobile UI**: Touch-friendly interface designed for small screens (480x320)
- **Fullscreen Kiosk**: Chromium browser launches in kiosk mode
- **Auto-Login**: Configured for unattended operation

#### 🔒 Enhanced Network Testing
- **TLS Validation**: TCP tests now verify TLS handshakes and certificates
- **HTTPS Full Check**: Complete HTTP/HTTPS validation matching Dock behavior
- **Enhanced QUIC**: Proper QUIC v1 packet format for accurate testing
- **UDP Port Ranges**: Tests WebRTC port ranges (40000-41000, 50000-60000)
- **Certificate Verification**: Validates SSL certificates like Dock does

#### 📊 Improved Test Accuracy
- **1:1 Dock Matching**: Tests replicate actual Dock/External Radio communication patterns
- **Skydio Thresholds**: Bandwidth tests use official Skydio requirements
  - Minimum: 10 Mbps up / 20 Mbps down
  - Recommended: 20 Mbps up / 80 Mbps down
- **Better QUIC Detection**: Sends proper QUIC Initial packets
- **Latency Requirements**: Tests against Skydio's documented latency thresholds

### New Features

#### Network Tests
- `https_full_check()`: Complete HTTPS validation with TLS and HTTP
- `udp_port_range_check()`: Sample UDP port ranges for WebRTC
- `tcp_check()` with `verify_tls`: Optional TLS handshake validation
- Enhanced `quic_check()`: Proper QUIC v1 packet format

#### User Interface
- `/mobile` route: Mobile-optimized UI for 3.5" displays
- Real-time progress updates with visual progress bar
- Summary dashboard with pass/warn/fail counts
- Categorized test results with latency information
- Touch-friendly buttons and controls

#### Installation Scripts
- `setup_kiosk.sh`: Automated kiosk mode configuration
- `setup_display_drivers.sh`: Display driver installation for common 3.5" screens
- `skydio-network-tester-kiosk.service`: Systemd service for kiosk mode

#### Documentation
- `KIOSK_MODE_SETUP.md`: Complete kiosk mode setup guide
- `ENHANCED_TESTING_GUIDE.md`: Detailed testing methodology
- `QUICK_START_KIOSK.md`: Quick setup guide
- `CHANGELOG.md`: Version history

### Technical Improvements

#### Network Testing
- TLS certificate validation using `ssl.create_default_context()`
- QUIC Initial packet with proper header format (0xc0 + version)
- UDP port sampling for efficient range testing
- Enhanced error reporting with specific failure reasons

#### Performance
- Optimized for Raspberry Pi hardware
- Efficient test execution with minimal resource usage
- Reduced memory footprint for embedded systems
- Fast UI rendering on low-power devices

#### Security
- Certificate validation prevents MITM attacks
- Detects SSL inspection and proxy interference
- Validates end-to-end encryption like Dock does

### Bug Fixes
- Fixed QUIC test reliability on slow networks
- Improved DNS resolution timeout handling
- Better error messages for TLS failures
- Corrected speedtest thresholds to match Skydio requirements

### Breaking Changes
- `StepRunner` now requires `https` and `udp_ranges` in targets config
- TCP tests with `verify_tls=True` may fail on networks with SSL inspection
- Speedtest thresholds changed to match Skydio documentation

### Migration Guide

#### From Version 1.x

1. **Update config.json** to include new test types:
```json
{
  "targets": {
    "https": [...],
    "udp_ranges": [...]
  }
}
```

2. **Update systemd service** if using custom configuration:
```bash
sudo systemctl daemon-reload
sudo systemctl restart skydio-network-tester.service
```

3. **Review test results** - some tests may now fail that previously passed due to enhanced validation

### Known Issues

- UDP port range tests cannot fully validate WebRTC without active session
- Some QUIC servers may not respond to probe packets (expected)
- TLS validation requires accurate system time (NTP must work)
- Kiosk mode requires X server (not compatible with headless-only setups)

### Upcoming Features (Roadmap)

- [ ] MTU size testing
- [ ] Flow control detection
- [ ] Traffic inspection detection
- [ ] Multi-dock bandwidth calculations
- [ ] Historical test comparison
- [ ] Email/webhook notifications for failures
- [ ] Remote management API

---

## Version 1.x - 2025

### Initial Release
- Basic network connectivity testing
- DNS, TCP, Ping, NTP, Speedtest
- Web UI for test execution
- PDF/CSV/JSON export
- Databricks integration
- Raspberry Pi support

---

**Version Numbering**: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes
