# Skydio Network Tester - User Installation Guide

Simple installation instructions for end users.

## One-Line Installation (Easiest)

SSH into your Raspberry Pi and run:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash
```

**That's it!** The installer will:
- Download the network tester
- Install all dependencies
- Configure the service
- Offer to set up kiosk mode

## What You Need

- Raspberry Pi 3/4/5 (or Zero 2 W)
- Raspberry Pi OS installed
- Internet connection
- SSH access (or keyboard/monitor)

## After Installation

### Access the Network Tester

**Standard Mode:**
- Open browser: `http://raspberrypi.local:5001`
- Or use IP: `http://192.168.1.XXX:5001`

**Mobile UI (for small screens):**
- Open browser: `http://raspberrypi.local:5001/mobile`

### Run Your First Test

1. Click "Start Network Test"
2. Wait for tests to complete (2-3 minutes)
3. Review results
4. Export report if needed

## Kiosk Mode (3.5" Display)

If you have a 3.5" touchscreen display:

```bash
cd ~/skydio-network-tester
sudo ./setup_display_drivers.sh  # Install display drivers
sudo ./setup_kiosk.sh            # Configure kiosk mode
sudo reboot                       # Reboot to start kiosk mode
```

After reboot, the network tester will automatically display on the touchscreen.

## Manual Installation

If you prefer to install manually:

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/skydio-network-tester.git
cd skydio-network-tester

# Run installation
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh

# Enable service
sudo systemctl enable skydio-network-tester.service
sudo systemctl start skydio-network-tester.service
```

## Troubleshooting

**Can't access web UI:**
```bash
# Check service status
sudo systemctl status skydio-network-tester.service

# View logs
sudo journalctl -u skydio-network-tester.service -n 50

# Restart service
sudo systemctl restart skydio-network-tester.service
```

**Display not working (kiosk mode):**
```bash
# Check display driver
lsmod | grep fbtft

# Check X server
DISPLAY=:0 xrandr
```

**Need to update:**
```bash
cd ~/skydio-network-tester
git pull
sudo systemctl restart skydio-network-tester.service
```

## Getting Help

- Check logs: `sudo journalctl -u skydio-network-tester.service -f`
- Review documentation in the installation directory
- Verify network connectivity
- Ensure Raspberry Pi OS is up to date

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop skydio-network-tester.service
sudo systemctl disable skydio-network-tester.service

# Remove files
rm -rf ~/skydio-network-tester

# Remove service file
sudo rm /etc/systemd/system/skydio-network-tester.service
sudo systemctl daemon-reload
```

---

**Need more help?** See the full documentation in the repository.
