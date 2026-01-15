#!/bin/bash
# Installation script for Skydio Network Readiness Tester on Raspberry Pi

set -e

echo "Installing Skydio Network Readiness Tester..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git curl speedtest-cli network-manager

sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager

sudo usermod -aG netdev pi || true

# Set application directory to current directory
APP_DIR="$(pwd)"
echo "Installing in: $APP_DIR"

# Ensure proper ownership
sudo chown -R pi:pi $APP_DIR

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install netifaces (may need compilation)
pip install netifaces

# Create exports directory
mkdir -p exports

# Set up systemd service
sudo cp systemd/skydio-network-tester.service /etc/systemd/system/

# Set up one-time hostname configuration (runs as root at boot)
sudo cp systemd/skydio-network-tester-set-hostname.sh /usr/local/sbin/skydio-network-tester-set-hostname
sudo chmod +x /usr/local/sbin/skydio-network-tester-set-hostname
sudo cp systemd/skydio-network-tester-hostname.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable skydio-network-tester.service
sudo systemctl enable skydio-network-tester-hostname.service

# Create default configuration
cat > config.json << EOF
{
  "auto_test_enabled": true,
  "max_auto_tests": 3,
  "test_interval_seconds": 300,
  "network_check_interval": 10,
  "auto_export_enabled": true,
  "auto_export_format": "pdf",
  "webhook_enabled": false,
  "webhook_url": "",
  "webhook_auth": "",
  "web_port": 5001,
  "api_key": "",
  "targets": {
    "dns": ["cloud.skydio.com", "time.skydio.com", "google.com", "u-blox.com"],
    "tcp": [
      {"host": "cloud.skydio.com", "port": 443, "label": "Skydio Cloud HTTPS"},
      {"host": "cloud.skydio.com", "port": 322, "label": "WebRTC TCP 322"},
      {"host": "cloud.skydio.com", "port": 7881, "label": "WebRTC TCP 7881"},
      {"host": "www.google.com", "port": 443, "label": "Generic HTTPS"},
      {"host": "time.skydio.com", "port": 123, "label": "Skydio NTP"}
    ],
    "ping": ["8.8.8.8", "1.1.1.1", "cloud.skydio.com"],
    "ntp": "time.skydio.com"
  }
}
EOF

# Set permissions
chmod +x auto_network_tester.py
chmod +x app.py
chmod 644 config.json
chown pi:pi config.json

echo "Installation complete!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start skydio-network-tester"
echo ""
echo "To check status:"
echo "  sudo systemctl status skydio-network-tester"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u skydio-network-tester -f"
echo ""
echo "Web interface will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "For manual testing:"
echo "  cd $APP_DIR"
echo "  source .venv/bin/activate"
echo "  python3 auto_network_tester.py --single-test"
