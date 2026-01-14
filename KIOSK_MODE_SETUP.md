# Skydio Network Tester - Kiosk Mode Setup Guide

This guide explains how to configure your Raspberry Pi to automatically boot into the Skydio Network Tester on a 3.5" touchscreen display in kiosk mode.

## Overview

Kiosk mode configures the Raspberry Pi to:
- Auto-login on boot
- Start the network tester Flask application
- Launch Chromium browser in fullscreen kiosk mode
- Display the mobile-optimized UI on the 3.5" screen
- Hide mouse cursor and disable screen blanking

## Hardware Requirements

- Raspberry Pi 3/4/5 (or Zero 2 W)
- 3.5" TFT touchscreen display (SPI or HDMI)
- MicroSD card (16GB+ recommended)
- Power supply (5V 3A recommended for Pi 4/5)
- Network connection (Ethernet or WiFi)

## Supported 3.5" Displays

1. **Waveshare 3.5" RPi LCD (A/B/C)** - 480x320 SPI
2. **Generic 3.5" SPI TFT displays** - 480x320
3. **3.5" HDMI displays** - 480x320

## Installation Steps

### Step 1: Install Raspberry Pi OS

1. Flash Raspberry Pi OS Lite (32-bit) or Desktop to your SD card
2. Enable SSH (create empty `ssh` file in boot partition)
3. Configure WiFi if needed (`wpa_supplicant.conf` in boot partition)
4. Boot the Raspberry Pi and SSH in

```bash
ssh pi@raspberrypi.local
# Default password: raspberry
```

### Step 2: Install Display Drivers (if needed)

For SPI displays (Waveshare, etc.):

```bash
cd ~/skydio-network-tester
sudo chmod +x setup_display_drivers.sh
sudo ./setup_display_drivers.sh
```

Follow the prompts to select your display type. The system will reboot after installation.

For HDMI displays, the script will configure `/boot/config.txt` automatically.

### Step 3: Install Network Tester Application

```bash
# Clone or transfer the application
cd ~
git clone <repository-url> skydio-network-tester
# OR use SCP to transfer files

cd skydio-network-tester

# Run installation script
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

This will:
- Install Python dependencies
- Create virtual environment
- Install system packages
- Set up the systemd service

### Step 4: Configure Kiosk Mode

```bash
cd ~/skydio-network-tester
sudo chmod +x setup_kiosk.sh
sudo ./setup_kiosk.sh
```

This script will:
- Install Chromium browser and X server components
- Configure auto-login for the `pi` user
- Set up Openbox window manager
- Create kiosk startup script
- Configure display settings
- Disable screen blanking and power management

### Step 5: Enable and Start Services

```bash
# Enable the network tester service
sudo systemctl enable skydio-network-tester.service
sudo systemctl start skydio-network-tester.service

# Check service status
sudo systemctl status skydio-network-tester.service

# View logs
sudo journalctl -u skydio-network-tester.service -f
```

### Step 6: Reboot into Kiosk Mode

```bash
sudo reboot
```

After reboot, the system should:
1. Auto-login as user `pi`
2. Start X server
3. Launch the network tester Flask app
4. Open Chromium in kiosk mode displaying the mobile UI

## Configuration Files

### Kiosk Startup Script
Location: `~/.config/openbox/autostart`

This script controls what happens when X starts:
- Disables screen blanking
- Hides mouse cursor
- Launches Chromium in kiosk mode

### Systemd Service
Location: `/etc/systemd/system/skydio-network-tester.service`

Controls the Flask application:
- Auto-starts on boot
- Restarts on failure
- Runs on port 5001

### Display Configuration
Location: `/boot/config.txt` (for HDMI displays)

HDMI display settings for 480x320 resolution.

## Mobile UI Features

The mobile-optimized interface (`/mobile`) includes:

- **Compact Design**: Optimized for 480x320 or 320x480 resolution
- **Touch-Friendly**: Large buttons and touch targets
- **Real-Time Updates**: Live test progress and results
- **Summary Dashboard**: Quick overview of pass/warn/fail counts
- **Categorized Results**: Tests grouped by type (DNS, TCP, HTTPS, QUIC, etc.)
- **Auto-Refresh**: Device info updates automatically

## Network Tests Performed

The enhanced network tester validates all Skydio Dock requirements:

### 1. DNS Resolution
- Skydio Cloud domains
- AWS S3 bucket endpoints
- u-blox GPS assistance services

### 2. TCP Connectivity
- Port 443 (HTTPS) - Skydio Cloud, S3, u-blox
- Port 322 - Livestreaming services
- Port 7881 - Additional livestreaming
- Port 51334 - Dock-to-cloud communication

### 3. HTTPS Validation (NEW)
- Full TLS handshake verification
- Certificate validation (matches Dock behavior)
- HTTP response validation

### 4. QUIC Protocol
- UDP port 443 connectivity
- QUIC packet exchange
- Livestreaming infrastructure

### 5. UDP Port Ranges (NEW)
- Ports 40000-41000 (Dock WebRTC)
- Ports 50000-60000 (Client WebRTC)
- Sampled testing (cannot fully validate without active session)

### 6. Network Latency (Ping)
- Google DNS (8.8.8.8)
- Cloudflare DNS (1.1.1.1)
- Skydio Cloud IPs

### 7. NTP Time Synchronization
- time.skydio.com
- Time offset measurement

### 8. Bandwidth Test
- Download speed (minimum 20 Mbps, recommended 80 Mbps)
- Upload speed (minimum 10 Mbps, recommended 20 Mbps)
- Skydio-specific thresholds

## Troubleshooting

### Display Not Working

**SPI Display:**
```bash
# Check if display driver is loaded
lsmod | grep fbtft

# View display configuration
cat /boot/config.txt | grep -i spi

# Test display
DISPLAY=:0 xrandr
```

**HDMI Display:**
```bash
# Check HDMI configuration
cat /boot/config.txt | grep hdmi

# Test HDMI output
tvservice -s
```

### Kiosk Mode Not Starting

```bash
# Check LightDM status
sudo systemctl status lightdm

# View X server logs
cat ~/.local/share/xorg/Xorg.0.log

# Check autostart script
cat ~/.config/openbox/autostart
```

### Network Tester Not Running

```bash
# Check service status
sudo systemctl status skydio-network-tester.service

# View recent logs
sudo journalctl -u skydio-network-tester.service -n 50

# Test manually
cd ~/skydio-network-tester
source .venv/bin/activate
python3 app.py
```

### Chromium Not Loading

```bash
# Test Chromium manually
DISPLAY=:0 chromium-browser --version

# Check if Flask app is running
curl http://localhost:5001/mobile

# View Chromium process
ps aux | grep chromium
```

### Touch Screen Not Responding

```bash
# Check input devices
xinput list

# Calibrate touchscreen (if needed)
sudo apt-get install xinput-calibrator
DISPLAY=:0 xinput_calibrator
```

## Manual Testing

To test the mobile UI without kiosk mode:

```bash
# Start the Flask app
cd ~/skydio-network-tester
source .venv/bin/activate
python3 app.py

# Access from another device on the network
# http://<raspberry-pi-ip>:5001/mobile
```

## Customization

### Change Display Resolution

Edit `~/.config/openbox/autostart` and add before Chromium launch:

```bash
xrandr --output HDMI-1 --mode 480x320
```

### Change Kiosk URL

Edit `~/.config/openbox/autostart` and modify the Chromium command:

```bash
chromium-browser --kiosk http://localhost:5001/mobile
```

### Disable Kiosk Mode

```bash
# Disable auto-login
sudo rm /etc/lightdm/lightdm.conf.d/autologin.conf

# Stop LightDM
sudo systemctl stop lightdm
sudo systemctl disable lightdm
```

## Performance Optimization

### For Raspberry Pi Zero/3

Add to `~/.config/openbox/autostart` before Chromium:

```bash
# Reduce GPU memory
sudo raspi-config
# Advanced Options -> Memory Split -> Set to 128MB

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
```

### For Better Touch Response

```bash
# Install touch-friendly packages
sudo apt-get install matchbox-keyboard
```

## Security Considerations

- Change default `pi` user password
- Configure firewall if exposed to network
- Disable SSH if not needed: `sudo systemctl disable ssh`
- Keep system updated: `sudo apt-get update && sudo apt-get upgrade`

## Accessing the System

### Via SSH (if enabled)

```bash
ssh pi@<raspberry-pi-ip>
```

### Via Console

Connect keyboard to Raspberry Pi and press:
- `Ctrl+Alt+F1` to switch to console
- `Ctrl+Alt+F7` to return to X server

### Exit Kiosk Mode Temporarily

Press `Alt+F4` to close Chromium (will restart automatically)

## Updates and Maintenance

### Update Network Tester

```bash
cd ~/skydio-network-tester
git pull  # or transfer new files
sudo systemctl restart skydio-network-tester.service
```

### Update System

```bash
sudo apt-get update
sudo apt-get upgrade
sudo reboot
```

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Waveshare LCD Wiki](https://www.waveshare.com/wiki/Main_Page)
- [Chromium Kiosk Mode](https://www.chromium.org/for-testers/enable-logging/)

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u skydio-network-tester.service`
2. Verify network connectivity
3. Test display configuration
4. Review this troubleshooting guide

---

**Version**: 2.0  
**Last Updated**: January 2026  
**Compatible with**: Raspberry Pi OS Bullseye/Bookworm
