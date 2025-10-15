# SSH Deployment Guide - Skydio Network Readiness Tester

## Quick Deployment Instructions

### Step 1: Transfer Files to Raspberry Pi

From your Mac, in the project directory:

```bash
# Option 1: Using the deploy script (Recommended)
./deploy.sh skydiort01.local

# Option 2: Using rsync directly
rsync -av --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
    ./ pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Step 2: SSH into Raspberry Pi and Install

```bash
# SSH to your Pi
ssh pi@skydiort01.local

# Navigate to the project directory
cd /home/pi/skydio-network-tester

# Make install script executable
chmod +x install_raspberry_pi.sh

# Run installation
./install_raspberry_pi.sh
```

### Step 3: Verify Installation

```bash
# Check service status
sudo systemctl status skydio-network-tester

# View logs
sudo journalctl -u skydio-network-tester -f

# Access web interface
# Open browser to: http://skydiort01.local:5001
```

---

## Detailed Deployment Steps

### Prerequisites

1. **Raspberry Pi Setup**
   - Raspberry Pi with Raspberry Pi OS installed
   - SSH enabled (default on most Pi images)
   - Connected to network
   - Hostname set to `skydiort01` (optional but recommended)

2. **Mac Setup**
   - SSH client (built-in on macOS)
   - Network connection to Raspberry Pi

### Setting Pi Hostname (Optional)

```bash
# SSH to your Pi
ssh pi@<current-pi-ip>

# Set hostname
sudo hostnamectl set-hostname skydiort01

# Update hosts file
sudo nano /etc/hosts
# Change the line with old hostname to:
# 127.0.1.1    skydiort01

# Reboot to apply changes
sudo reboot
```

After reboot, access via: `ssh pi@skydiort01.local`

---

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

Use the included `deploy.sh` script:

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Deploy to Pi
./deploy.sh skydiort01.local

# Or use IP address
./deploy.sh 192.168.1.100
```

The script will:
- Create the project directory on Pi
- Transfer all necessary files
- Exclude development files (.venv, .git, etc.)
- Display next steps

### Method 2: Manual rsync

```bash
# Create directory on Pi
ssh pi@skydiort01.local "mkdir -p /home/pi/skydio-network-tester"

# Transfer files
rsync -av --progress \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    ./ pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Method 3: Manual SCP

```bash
# Transfer entire directory
scp -r . pi@skydiort01.local:/home/pi/skydio-network-tester/
```

---

## Installation on Raspberry Pi

### Automatic Installation

```bash
# SSH to Pi
ssh pi@skydiort01.local

# Navigate to project
cd /home/pi/skydio-network-tester

# Run installer
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

The installer will:
- Install system dependencies (Python, pip, etc.)
- Create Python virtual environment
- Install Python packages
- Set up systemd service
- Create config.json with proper permissions
- Start the service

### Manual Installation

If you prefer manual installation:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-venv speedtest-cli

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Create config file with proper permissions
cat > config.json << 'EOF'
{
  "auto_test_enabled": false,
  "max_auto_tests": 3,
  "test_interval_seconds": 300,
  "auto_export_enabled": false,
  "auto_export_format": "pdf",
  "webhook_enabled": false,
  "webhook_url": "",
  "web_port": 5001
}
EOF

# Set proper permissions
chmod 644 config.json
chown pi:pi config.json

# Install systemd service
sudo cp systemd/skydio-network-tester.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skydio-network-tester
sudo systemctl start skydio-network-tester
```

---

## Updating Existing Installation

To push updates to an already-installed Pi:

```bash
# From your Mac, in project directory
./deploy.sh skydiort01.local

# SSH to Pi and restart service
ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && sudo systemctl restart skydio-network-tester"
```

### One-Line Update Command

```bash
./deploy.sh skydiort01.local && ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && sudo systemctl restart skydio-network-tester"
```

---

## Troubleshooting

### Settings Not Editable

**Issue**: Settings page loads but changes don't save

**Solution**: Ensure config.json exists with proper permissions

```bash
# SSH to Pi
ssh pi@skydiort01.local
cd /home/pi/skydio-network-tester

# Check if config.json exists
ls -la config.json

# If missing, create it
cat > config.json << 'EOF'
{
  "auto_test_enabled": false,
  "max_auto_tests": 3,
  "test_interval_seconds": 300,
  "auto_export_enabled": false,
  "auto_export_format": "pdf",
  "webhook_enabled": false,
  "webhook_url": "",
  "web_port": 5001,
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
EOF

# Set proper permissions
chmod 644 config.json
chown pi:pi config.json

# Restart service
sudo systemctl restart skydio-network-tester
```

### Connection Issues

```bash
# Test SSH connection
ssh pi@skydiort01.local

# If hostname doesn't work, find Pi IP
ping skydiort01.local

# Or use IP directly
ssh pi@192.168.1.100
```

### Service Not Starting

```bash
# Check service status
sudo systemctl status skydio-network-tester

# View logs
sudo journalctl -u skydio-network-tester -n 50

# Check for errors
sudo journalctl -u skydio-network-tester -f
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R pi:pi /home/pi/skydio-network-tester

# Fix permissions
chmod 755 /home/pi/skydio-network-tester
chmod 644 /home/pi/skydio-network-tester/*.py
chmod 644 /home/pi/skydio-network-tester/config.json
```

### Port Already in Use

```bash
# Check what's using port 5001
sudo lsof -i :5001

# Kill process if needed
sudo kill <PID>

# Or change port in config.json
nano config.json
# Change "web_port": 5001 to another port

# Restart service
sudo systemctl restart skydio-network-tester
```

---

## Verification

### Check Service Status

```bash
# Service status
sudo systemctl status skydio-network-tester

# Should show: Active: active (running)
```

### Check Logs

```bash
# Recent logs
sudo journalctl -u skydio-network-tester -n 50

# Follow logs in real-time
sudo journalctl -u skydio-network-tester -f
```

### Test Web Interface

```bash
# From Pi
curl http://localhost:5001/health

# Should return: {"ok":true}

# From your Mac
curl http://skydiort01.local:5001/health
```

### Access Web Interface

Open browser to:
- `http://skydiort01.local:5001` (if hostname is set)
- `http://<pi-ip-address>:5001` (using IP)

---

## Common Commands

```bash
# Start service
sudo systemctl start skydio-network-tester

# Stop service
sudo systemctl stop skydio-network-tester

# Restart service
sudo systemctl restart skydio-network-tester

# Check status
sudo systemctl status skydio-network-tester

# View logs
sudo journalctl -u skydio-network-tester -f

# Enable auto-start on boot
sudo systemctl enable skydio-network-tester

# Disable auto-start
sudo systemctl disable skydio-network-tester
```

---

## Network Access

### From Same Network

Access the web interface from any device on the same network:
- `http://skydiort01.local:5001`
- `http://<pi-ip>:5001`

### Port Forwarding (Optional)

To access from outside your network:

1. Configure router port forwarding:
   - External port: 5001
   - Internal IP: Pi's IP address
   - Internal port: 5001

2. Access via: `http://<your-public-ip>:5001`

**Security Note**: Consider adding authentication if exposing to internet.

---

## Settings Configuration

Once deployed, you can configure settings through the web interface:

1. Navigate to Settings page
2. Configure test parameters
3. Set up export options
4. Configure Databricks integration (optional)
5. Click "Save" buttons to persist changes

**Note**: Settings will now save properly once the Pi is deployed with the correct config.json file and permissions.

---

## Quick Reference

```bash
# Deploy new version
./deploy.sh skydiort01.local && ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && sudo systemctl restart skydio-network-tester"

# Check status
ssh pi@skydiort01.local "sudo systemctl status skydio-network-tester"

# View logs
ssh pi@skydiort01.local "sudo journalctl -u skydio-network-tester -n 50"

# Restart service
ssh pi@skydiort01.local "sudo systemctl restart skydio-network-tester"

# Fix permissions
ssh pi@skydiort01.local "sudo chown -R pi:pi /home/pi/skydio-network-tester && chmod 644 /home/pi/skydio-network-tester/config.json"
```

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u skydio-network-tester -f`
2. Verify config.json exists and has proper permissions
3. Ensure all dependencies are installed
4. Check network connectivity
