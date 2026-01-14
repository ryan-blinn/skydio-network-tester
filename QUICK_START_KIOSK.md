# Quick Start: Kiosk Mode Setup

Get your Raspberry Pi network tester running in kiosk mode with a 3.5" display in under 30 minutes.

## Prerequisites

- Raspberry Pi (3/4/5 or Zero 2 W)
- 3.5" touchscreen display
- MicroSD card with Raspberry Pi OS
- Network connection

## 5-Step Setup

### 1. Install Display Drivers (5 min)

```bash
cd ~/skydio-network-tester
sudo chmod +x setup_display_drivers.sh
sudo ./setup_display_drivers.sh
# Select your display type and reboot
```

### 2. Install Network Tester (10 min)

```bash
cd ~/skydio-network-tester
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

### 3. Configure Kiosk Mode (5 min)

```bash
sudo chmod +x setup_kiosk.sh
sudo ./setup_kiosk.sh
```

### 4. Enable Service (2 min)

```bash
sudo systemctl enable skydio-network-tester.service
sudo systemctl start skydio-network-tester.service
```

### 5. Reboot (2 min)

```bash
sudo reboot
```

## What Happens After Reboot

1. ✅ System auto-logs in
2. ✅ Flask app starts on port 5001
3. ✅ Chromium opens in fullscreen
4. ✅ Mobile UI displays on 3.5" screen
5. ✅ Touch "Start Test" to begin

## Verify Installation

```bash
# Check service status
sudo systemctl status skydio-network-tester.service

# Test mobile UI from another device
curl http://<pi-ip>:5001/mobile
```

## Troubleshooting

**Display not working?**
```bash
lsmod | grep fbtft  # Check SPI driver
cat /boot/config.txt | grep hdmi  # Check HDMI config
```

**Kiosk not starting?**
```bash
sudo systemctl status lightdm
cat ~/.config/openbox/autostart
```

**Service not running?**
```bash
sudo journalctl -u skydio-network-tester.service -n 50
```

## Access Methods

- **Touch Screen**: Use the 3.5" display directly
- **Web Browser**: `http://<pi-ip>:5001/mobile`
- **SSH**: `ssh pi@<pi-ip>` (if enabled)
- **Console**: Press `Ctrl+Alt+F1` on connected keyboard

## Next Steps

- Review test results on the mobile UI
- Export reports (PDF/CSV/JSON)
- Configure custom test targets in `config.json`
- See `KIOSK_MODE_SETUP.md` for detailed configuration

## Support

For detailed troubleshooting, see:
- `KIOSK_MODE_SETUP.md` - Complete setup guide
- `ENHANCED_TESTING_GUIDE.md` - Testing methodology
- `NETWORK_REQUIREMENTS.md` - Network requirements

---

**Quick Reference Commands**

```bash
# Restart service
sudo systemctl restart skydio-network-tester.service

# View logs
sudo journalctl -u skydio-network-tester.service -f

# Exit kiosk mode
# Press Alt+F4 or Ctrl+Alt+F1

# Update application
cd ~/skydio-network-tester
git pull
sudo systemctl restart skydio-network-tester.service
```
