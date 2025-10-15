#!/bin/bash
# Quick deployment script for transferring files to Raspberry Pi

set -e

# Configuration
PI_USER="pi"
PI_HOST=""
PI_DIR="/home/pi/skydio-network-tester"

# Check if host is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <pi-hostname-or-ip>"
    echo "Example: $0 skydiort01.local"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

PI_HOST="$1"

echo "Deploying Skydio Network Tester to $PI_USER@$PI_HOST..."

# Create directory on Pi
ssh $PI_USER@$PI_HOST "mkdir -p $PI_DIR"

# Copy all files except .venv and .git
rsync -av --exclude='.venv' --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    ./ $PI_USER@$PI_HOST:$PI_DIR/

echo "Files copied successfully!"
echo ""
echo "Now run the installation on the Pi:"
echo "  ssh $PI_USER@$PI_HOST"
echo "  cd $PI_DIR"
echo "  chmod +x install_raspberry_pi.sh"
echo "  ./install_raspberry_pi.sh"
echo ""
echo "Or run the installation remotely:"
echo "  ssh $PI_USER@$PI_HOST 'cd $PI_DIR && chmod +x install_raspberry_pi.sh && ./install_raspberry_pi.sh'"
