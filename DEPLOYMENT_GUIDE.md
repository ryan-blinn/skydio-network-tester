# Deployment Guide - Skydio Network Tester

This guide covers how to deploy the network tester to Raspberry Pi devices and distribute it to other users.

## Table of Contents

1. [Initial Deployment (Your First Pi)](#initial-deployment)
2. [Easy Distribution for Others](#easy-distribution)
3. [GitHub Setup](#github-setup)
4. [Alternative Distribution Methods](#alternative-distribution)
5. [Update Existing Installations](#updates)

---

## Initial Deployment (Your First Pi)

### Prerequisites

**On your Mac/PC:**
- Git repository with the network tester code
- SSH access to Raspberry Pi
- `rsync` installed (comes with macOS)

**On Raspberry Pi:**
- Raspberry Pi OS installed
- SSH enabled
- Network connectivity
- User account (default: `pi`)

### Method 1: Automated Deployment Script (Recommended)

```bash
# From your Mac, in the project directory
cd ~/CascadeProjects/skydio-network-tester

# Make deployment script executable
chmod +x deploy_to_pi.sh

# Deploy to your Pi
./deploy_to_pi.sh raspberrypi.local
# or with IP address
./deploy_to_pi.sh 192.168.1.100

# With custom username
./deploy_to_pi.sh 192.168.1.100 myuser
```

The script will:
1. Test SSH connection
2. Create remote directory
3. Sync all files (excluding .git, .venv, etc.)
4. Set script permissions
5. Optionally run installation
6. Optionally enable the service

### Method 2: Manual SCP/Rsync

```bash
# Create directory on Pi
ssh pi@raspberrypi.local "mkdir -p ~/skydio-network-tester"

# Sync files
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    ./ pi@raspberrypi.local:~/skydio-network-tester/

# SSH into Pi and install
ssh pi@raspberrypi.local
cd ~/skydio-network-tester
chmod +x *.sh
./install_raspberry_pi.sh
```

### Method 3: Git Clone Directly on Pi

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Clone repository
git clone https://github.com/YOUR_ORG/skydio-network-tester.git
cd skydio-network-tester

# Install
chmod +x *.sh
./install_raspberry_pi.sh
```

---

## Easy Distribution for Others

### Option A: One-Line Installer (Easiest for Users)

After setting up GitHub (see below), users can install with a single command:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash
```

Or with wget:

```bash
wget -qO- https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash
```

**What it does:**
- Checks prerequisites
- Clones repository
- Runs installation
- Offers to configure kiosk mode
- Starts the service

### Option B: Release Packages

Create distributable packages:

```bash
# Create release package
chmod +x prepare_release.sh
./prepare_release.sh 2.0

# This creates:
# releases/skydio-network-tester-v2.0.tar.gz
# releases/skydio-network-tester-v2.0.tar.gz.sha256
```

Users download and install:

```bash
# On Raspberry Pi
wget https://YOUR_SERVER/skydio-network-tester-v2.0.tar.gz
tar xzf skydio-network-tester-v2.0.tar.gz
cd skydio-network-tester-v2.0
./install_raspberry_pi.sh
```

### Option C: Pre-Configured SD Card Image

For multiple deployments, create a master SD card image:

1. Set up one Pi completely (including kiosk mode)
2. Create SD card image using:
   - **macOS**: Disk Utility or `dd`
   - **Windows**: Win32DiskImager
   - **Linux**: `dd`
3. Distribute image file
4. Users flash image to SD card

**Advantages:**
- Fastest deployment
- Consistent configuration
- No internet required on Pi

**Disadvantages:**
- Large file size (~4-16GB)
- Harder to update

---

## GitHub Setup

### 1. Create GitHub Repository

```bash
# Initialize git (if not already done)
cd ~/CascadeProjects/skydio-network-tester
git init

# Add all files
git add .

# Create .gitignore
cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
*.pyo
.DS_Store
exports/
test_history/
*.log
releases/
config.json
EOF

# Commit
git commit -m "Initial commit - Skydio Network Tester v2.0"

# Create GitHub repo (via GitHub website or CLI)
# Then add remote and push
git remote add origin https://github.com/YOUR_ORG/skydio-network-tester.git
git branch -M main
git push -u origin main
```

### 2. Update quick_install.sh

Edit `quick_install.sh` and update:

```bash
REPO_URL="https://github.com/YOUR_ORG/skydio-network-tester"
```

### 3. Create GitHub Release

```bash
# Create release package
./prepare_release.sh 2.0

# Upload to GitHub Releases:
# 1. Go to GitHub repo → Releases → Create new release
# 2. Tag: v2.0
# 3. Title: Skydio Network Tester v2.0
# 4. Upload: releases/skydio-network-tester-v2.0.tar.gz
# 5. Upload: releases/skydio-network-tester-v2.0.tar.gz.sha256
# 6. Add release notes from CHANGELOG.md
```

### 4. Share Installation Instructions

Create a simple README for users:

```markdown
# Skydio Network Tester - Installation

## Quick Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash
```

## Manual Install

```bash
git clone https://github.com/YOUR_ORG/skydio-network-tester.git
cd skydio-network-tester
./install_raspberry_pi.sh
```

## Access

- Desktop UI: http://raspberrypi.local:5001
- Mobile UI: http://raspberrypi.local:5001/mobile
```

---

## Alternative Distribution Methods

### Internal File Server

If GitHub isn't an option:

1. **Set up internal web server:**
   ```bash
   # On your server
   mkdir -p /var/www/html/skydio
   cp releases/skydio-network-tester-v2.0.tar.gz /var/www/html/skydio/
   cp quick_install.sh /var/www/html/skydio/
   ```

2. **Update quick_install.sh:**
   ```bash
   REPO_URL="http://your-server.local/skydio/skydio-network-tester-v2.0.tar.gz"
   ```

3. **Users install:**
   ```bash
   curl -sSL http://your-server.local/skydio/quick_install.sh | bash
   ```

### USB Drive Distribution

1. **Prepare USB drive:**
   ```bash
   ./prepare_release.sh 2.0
   cp releases/skydio-network-tester-v2.0.tar.gz /Volumes/USB_DRIVE/
   cp DEPLOYMENT_GUIDE.md /Volumes/USB_DRIVE/README.txt
   ```

2. **Users install from USB:**
   ```bash
   # On Raspberry Pi
   cp /media/usb/skydio-network-tester-v2.0.tar.gz ~/
   cd ~
   tar xzf skydio-network-tester-v2.0.tar.gz
   cd skydio-network-tester-v2.0
   ./install_raspberry_pi.sh
   ```

### Network Share (SMB/NFS)

1. **Place package on network share**
2. **Users mount and install:**
   ```bash
   sudo mount -t cifs //server/share /mnt/share
   cp /mnt/share/skydio-network-tester-v2.0.tar.gz ~/
   cd ~
   tar xzf skydio-network-tester-v2.0.tar.gz
   cd skydio-network-tester-v2.0
   ./install_raspberry_pi.sh
   ```

---

## Update Existing Installations

### Method 1: Automated Update Script

Create `update.sh` on Pi:

```bash
#!/bin/bash
cd ~/skydio-network-tester
git pull origin main
sudo systemctl restart skydio-network-tester.service
```

### Method 2: Re-run Deployment Script

From your Mac:

```bash
./deploy_to_pi.sh raspberrypi.local
# Select option to update existing installation
```

### Method 3: Manual Update

```bash
# SSH into Pi
ssh pi@raspberrypi.local
cd ~/skydio-network-tester

# Pull latest changes
git pull

# Restart service
sudo systemctl restart skydio-network-tester.service
```

---

## Deployment Checklist

### Before Deployment

- [ ] Test all functionality locally
- [ ] Update VERSION file
- [ ] Update CHANGELOG.md
- [ ] Commit all changes to git
- [ ] Create release package
- [ ] Test installation on clean Pi

### Initial Deployment

- [ ] Deploy to first Pi using `deploy_to_pi.sh`
- [ ] Verify web UI accessible
- [ ] Run network tests
- [ ] Check service status
- [ ] Test kiosk mode (if applicable)

### Distribution Setup

- [ ] Push to GitHub (or internal repo)
- [ ] Update quick_install.sh with correct URLs
- [ ] Test one-line installer
- [ ] Create GitHub release (if using)
- [ ] Document installation instructions
- [ ] Share with users

### User Support

- [ ] Provide installation command
- [ ] Share documentation links
- [ ] Set up support channel
- [ ] Monitor for issues

---

## Troubleshooting Deployment

### SSH Connection Issues

```bash
# Test connection
ssh -v pi@raspberrypi.local

# If hostname doesn't resolve, use IP
ssh pi@192.168.1.100

# Set up SSH keys for passwordless access
ssh-copy-id pi@raspberrypi.local
```

### Permission Denied

```bash
# Ensure scripts are executable
chmod +x deploy_to_pi.sh
chmod +x prepare_release.sh

# On Pi, fix permissions
ssh pi@raspberrypi.local
cd ~/skydio-network-tester
chmod +x *.sh
```

### Rsync Not Found

```bash
# macOS (should be pre-installed)
which rsync

# If missing, install with Homebrew
brew install rsync

# Linux
sudo apt-get install rsync
```

### Git Clone Fails

```bash
# Check if git is installed on Pi
ssh pi@raspberrypi.local "git --version"

# Install if missing
ssh pi@raspberrypi.local "sudo apt-get update && sudo apt-get install -y git"
```

---

## Best Practices

### Version Control

- Tag releases: `git tag -a v2.0 -m "Version 2.0"`
- Use semantic versioning: MAJOR.MINOR.PATCH
- Keep CHANGELOG.md updated

### Security

- Don't commit sensitive data (API keys, passwords)
- Use `.gitignore` properly
- Consider private repository for internal tools
- Change default Pi password

### Testing

- Test on clean Raspberry Pi OS installation
- Verify both standard and kiosk modes
- Test update process
- Document any manual steps required

### Documentation

- Keep installation instructions simple
- Provide troubleshooting section
- Include screenshots/videos if helpful
- Document network requirements

---

## Quick Reference Commands

```bash
# Deploy to Pi
./deploy_to_pi.sh raspberrypi.local

# Create release package
./prepare_release.sh 2.0

# One-line install (for users)
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash

# Check service status
ssh pi@raspberrypi.local 'sudo systemctl status skydio-network-tester.service'

# View logs
ssh pi@raspberrypi.local 'sudo journalctl -u skydio-network-tester.service -f'

# Restart service
ssh pi@raspberrypi.local 'sudo systemctl restart skydio-network-tester.service'
```

---

## Support

For issues or questions:
- Check documentation in repository
- Review logs: `sudo journalctl -u skydio-network-tester.service`
- Test network connectivity
- Verify Raspberry Pi OS version compatibility

---

**Last Updated**: January 2026  
**Version**: 2.0
