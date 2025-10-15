# Raspberry Pi Installation Guide
## Skydio Network Readiness Tester

This guide will help you install and configure the Skydio Network Readiness Tester on a Raspberry Pi for automated network testing.

## Prerequisites

- **Raspberry Pi 4** (recommended) or Pi 3B+ with Raspberry Pi OS
- **8GB+ SD card** with fresh Raspberry Pi OS installation
- **Network connection** (Ethernet or WiFi)
- **SSH access** enabled (for remote installation)

## Quick Installation

### Method 1: SCP Transfer from Mac (Recommended)

1. **Set Pi hostname** (makes access easier):
   ```bash
   # SSH to your Pi first
   ssh pi@192.168.1.100  # Replace with your Pi's IP
   sudo hostnamectl set-hostname skydiort01
   sudo reboot
   ```

2. **Transfer files from your Mac**:
   ```bash
   # From your Mac, in the project directory
   chmod +x deploy.sh
   ./deploy.sh skydiort01.local
   ```

3. **Install on Pi**:
   ```bash
   ssh pi@skydiort01.local
   cd skydio-network-tester
   chmod +x install_raspberry_pi.sh
   ./install_raspberry_pi.sh
   ```

4. **Start the service**:
   ```bash
   sudo systemctl start skydio-network-tester
   ```

5. **Access the web interface**:
   - Open browser to `http://skydiort01.local:5001`

### Method 2: Manual Installation

If you prefer to install manually or need to troubleshoot:

1. **Update system packages**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install dependencies**:
   ```bash
   sudo apt install -y python3 python3-pip python3-venv git curl speedtest-cli
   ```

3. **Create application directory**:
   ```bash
   sudo mkdir -p /home/pi/skydio-network-tester
   sudo chown pi:pi /home/pi/skydio-network-tester
   ```

4. **Copy project files** to `/home/pi/skydio-network-tester/`

5. **Set up Python environment**:
   ```bash
   cd /home/pi/skydio-network-tester
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Create directories**:
   ```bash
   mkdir -p exports
   ```

7. **Install systemd service**:
   ```bash
   sudo cp systemd/skydio-network-tester.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable skydio-network-tester.service
   sudo systemctl start skydio-network-tester.service
   ```

## Configuration

### Initial Setup

1. **Access the web interface** at `http://[PI_IP_ADDRESS]:5001`
2. **Click "Settings"** in the top-right corner
3. **Configure your preferences**:
   - **System**: Set hostname, view system status
   - **Network**: Configure WiFi/Ethernet settings
   - **Testing**: Enable auto-testing, set intervals
   - **Export**: Configure automatic exports, webhooks
   - **API**: Set up authentication if needed

### Key Settings

- **Auto Testing**: Enable to automatically run tests when network changes
- **Test Interval**: Time between automatic tests (default: 5 minutes)
- **Export Format**: Choose PDF, CSV, or JSON for automatic exports
- **Webhook URL**: Send results to external systems
- **Test Targets**: Customize which servers/ports to test

## Usage

### Web Interface
- **Manual Testing**: Click "Start Network Test" on main page
- **View Results**: Expandable test cards show detailed results
- **Export Results**: Download PDF, CSV, or JSON reports
- **Settings**: Configure all system parameters

### Automatic Operation
Once configured, the system will:
1. **Monitor network changes** (IP changes, new connections)
2. **Automatically run tests** when changes detected
3. **Export results** in your chosen format
4. **Send webhooks** if configured
5. **Limit test runs** to prevent excessive testing

## Service Management

### Control the Service
```bash
# Start the service
sudo systemctl start skydio-network-tester

# Stop the service
sudo systemctl stop skydio-network-tester

# Restart the service
sudo systemctl restart skydio-network-tester

# Check service status
sudo systemctl status skydio-network-tester

# Enable auto-start on boot
sudo systemctl enable skydio-network-tester

# Disable auto-start
sudo systemctl disable skydio-network-tester
```

### View Logs
```bash
# View recent logs
sudo journalctl -u skydio-network-tester -n 50

# Follow logs in real-time
sudo journalctl -u skydio-network-tester -f

# View all logs
sudo journalctl -u skydio-network-tester --no-pager
```

## Network Access

### Local Network Access
- **Web Interface**: `http://[PI_IP_ADDRESS]:5001`
- **Find Pi IP**: `hostname -I` or check your router's DHCP table

### Remote Access Setup
To access from outside your local network:

1. **Port Forwarding**: Forward port 5001 on your router to the Pi
2. **Dynamic DNS**: Use services like DuckDNS for consistent access
3. **VPN**: Set up VPN access to your network (most secure)

### Security Considerations
- **Change default credentials** if authentication is enabled
- **Use HTTPS** in production (requires additional setup)
- **Restrict network access** using firewall rules if needed
- **Keep system updated** regularly

## File Locations

- **Application**: `/home/pi/skydio-network-tester/`
- **Configuration**: `/home/pi/skydio-network-tester/config.json`
- **Exports**: `/home/pi/skydio-network-tester/exports/`
- **Logs**: `sudo journalctl -u skydio-network-tester`
- **Service**: `/etc/systemd/system/skydio-network-tester.service`

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status skydio-network-tester

# Check logs for errors
sudo journalctl -u skydio-network-tester -n 20

# Verify Python dependencies
cd /home/pi/skydio-network-tester
source .venv/bin/activate
python3 -c "import flask, requests, psutil, netifaces, ntplib, fpdf"
```

### Web Interface Not Accessible
```bash
# Check if service is running
sudo systemctl status skydio-network-tester

# Check if port 5001 is open
sudo netstat -tlnp | grep 5001

# Check firewall (if enabled)
sudo ufw status

# Test locally on Pi
curl http://localhost:5001
```

### Tests Failing
1. **Check network connectivity**: `ping google.com`
2. **Verify DNS resolution**: `nslookup cloud.skydio.com`
3. **Check speedtest**: `speedtest-cli`
4. **Review test targets** in Settings → Testing

### Permission Issues
```bash
# Fix ownership
sudo chown -R pi:pi /home/pi/skydio-network-tester

# Fix permissions
chmod +x /home/pi/skydio-network-tester/*.py
```

### Reset to Defaults
```bash
# Stop service
sudo systemctl stop skydio-network-tester

# Remove configuration
rm /home/pi/skydio-network-tester/config.json

# Restart service (will create default config)
sudo systemctl start skydio-network-tester
```

## Updates

To update the application:

```bash
# Stop service
sudo systemctl stop skydio-network-tester

# Backup configuration
cp /home/pi/skydio-network-tester/config.json ~/config-backup.json

# Update code (replace with your update method)
cd /home/pi/skydio-network-tester
git pull  # or copy new files

# Update dependencies if needed
source .venv/bin/activate
pip install -r requirements.txt

# Restore configuration
cp ~/config-backup.json /home/pi/skydio-network-tester/config.json

# Restart service
sudo systemctl start skydio-network-tester
```

## Support

For issues or questions:
1. **Check logs**: `sudo journalctl -u skydio-network-tester -f`
2. **Verify configuration**: Review settings in web interface
3. **Test manually**: Run individual components to isolate issues
4. **Check network**: Ensure Pi has proper network connectivity

The system is designed to be plug-and-play for Skydio dock installations, automatically detecting network changes and providing comprehensive readiness testing.
