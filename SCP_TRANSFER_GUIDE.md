# SCP File Transfer Guide - Mac to Raspberry Pi

This guide shows how to transfer files from your Mac to a Raspberry Pi using SCP (Secure Copy Protocol).

## Prerequisites

- **SSH enabled** on Raspberry Pi (usually enabled by default)
- **Network connection** between Mac and Pi
- **Pi hostname set** to `skydiort01` (or use IP address)

## Setting Pi Hostname to skydiort01

First, set your Pi's hostname for easier access:

```bash
# SSH to your Pi
ssh pi@192.168.1.100  # Replace with your Pi's current IP

# Set hostname
sudo hostnamectl set-hostname skydiort01

# Update hosts file
sudo nano /etc/hosts
# Change the line with old hostname to:
# 127.0.1.1    skydiort01

# Reboot to apply changes
sudo reboot
```

After reboot, you can access your Pi using:
```bash
ssh pi@skydiort01.local
```

## SCP Transfer Methods

### Method 1: Transfer Single File
```bash
# Basic syntax
scp /path/to/local/file pi@skydiort01.local:/path/to/remote/destination

# Example: Transfer a config file
scp config.json pi@skydiort01.local:/home/pi/

# Example: Transfer to specific directory
scp requirements.txt pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Method 2: Transfer Multiple Files
```bash
# Transfer multiple specific files
scp file1.py file2.py config.json pi@skydiort01.local:/home/pi/skydio-network-tester/

# Transfer all Python files
scp *.py pi@skydiort01.local:/home/pi/skydio-network-tester/

# Transfer all files in current directory
scp * pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Method 3: Transfer Entire Directory
```bash
# Transfer entire project directory (recursive)
scp -r . pi@skydiort01.local:/home/pi/skydio-network-tester/

# Transfer specific directory
scp -r static/ pi@skydiort01.local:/home/pi/skydio-network-tester/

# Transfer with exclusions (better to use rsync for this)
scp -r --exclude='.venv' --exclude='.git' . pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Method 4: Using Rsync (Recommended for Projects)
```bash
# Rsync with exclusions (more efficient than scp for directories)
rsync -av --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
    ./ pi@skydiort01.local:/home/pi/skydio-network-tester/

# Rsync with progress display
rsync -av --progress --exclude='.venv' --exclude='.git' \
    ./ pi@skydiort01.local:/home/pi/skydio-network-tester/
```

## Complete Deployment Example

Here's the complete process to deploy the Skydio Network Tester:

### Step 1: Prepare Pi
```bash
# SSH to Pi and create directory
ssh pi@skydiort01.local
mkdir -p /home/pi/skydio-network-tester
exit
```

### Step 2: Transfer Files from Mac
```bash
# From your Mac, in the project directory
rsync -av --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
    ./ pi@skydiort01.local:/home/pi/skydio-network-tester/
```

### Step 3: Install on Pi
```bash
# SSH back to Pi
ssh pi@skydiort01.local

# Navigate to project and install
cd /home/pi/skydio-network-tester
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

### Step 4: Start Service
```bash
# Start the network tester service
sudo systemctl start skydio-network-tester

# Check status
sudo systemctl status skydio-network-tester

# Access web interface
echo "Web interface: http://skydiort01.local:5001"
```

## Using the Deploy Script

The included deploy script automates the transfer:

```bash
# Make script executable
chmod +x deploy.sh

# Deploy to Pi using hostname
./deploy.sh skydiort01.local

# Or deploy using IP address
./deploy.sh 192.168.1.100
```

## Common SCP Options

- **`-r`**: Recursive (for directories)
- **`-p`**: Preserve timestamps and permissions
- **`-v`**: Verbose output
- **`-P port`**: Specify SSH port (if not 22)
- **`-i keyfile`**: Use specific SSH key

## Troubleshooting

### Connection Issues
```bash
# Test SSH connection first
ssh pi@skydiort01.local

# If hostname doesn't work, use IP
ssh pi@192.168.1.100

# Check if SSH is enabled on Pi
sudo systemctl status ssh
```

### Permission Issues
```bash
# Ensure destination directory exists and is writable
ssh pi@skydiort01.local "mkdir -p /home/pi/skydio-network-tester"

# Fix permissions if needed
ssh pi@skydiort01.local "sudo chown -R pi:pi /home/pi/skydio-network-tester"
```

### Large File Transfers
```bash
# Use compression for large transfers
scp -C large-file.zip pi@skydiort01.local:/home/pi/

# Resume interrupted transfers (use rsync)
rsync -av --partial --progress file.zip pi@skydiort01.local:/home/pi/
```

## Security Notes

- **SSH Keys**: Consider using SSH keys instead of passwords for automated transfers
- **Firewall**: Ensure SSH port (22) is open on both Mac and Pi
- **Network**: Both devices should be on the same network or have routing configured

## Quick Reference

```bash
# Single file
scp file.txt pi@skydiort01.local:/home/pi/

# Multiple files
scp *.py pi@skydiort01.local:/home/pi/project/

# Directory (recursive)
scp -r project/ pi@skydiort01.local:/home/pi/

# With progress and exclusions (rsync)
rsync -av --progress --exclude='.git' ./ pi@skydiort01.local:/home/pi/project/

# Using deploy script
./deploy.sh skydiort01.local
```

The hostname `skydiort01.local` will work once you've set the Pi's hostname and both devices are on the same network with mDNS/Bonjour enabled (default on most networks).
