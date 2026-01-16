#!/bin/bash
# Quick deploy script for WiFi configuration changes

set -e

PI_USER="pi"
PI_HOST="skydio-nt.local"
REMOTE_DIR="/home/$PI_USER/skydio-network-tester"

echo "Deploying WiFi configuration changes to $PI_HOST..."

# Copy updated files
echo "Copying app.py..."
scp app.py $PI_USER@$PI_HOST:$REMOTE_DIR/

echo "Copying settings.js..."
scp static/js/settings.js $PI_USER@$PI_HOST:$REMOTE_DIR/static/js/

echo "Copying settings.css..."
scp static/css/settings.css $PI_USER@$PI_HOST:$REMOTE_DIR/static/css/

echo "Copying settings.html..."
scp templates/settings.html $PI_USER@$PI_HOST:$REMOTE_DIR/templates/

echo ""
echo "Restarting Flask service..."
ssh $PI_USER@$PI_HOST 'sudo systemctl restart skydio-network-tester.service'

echo ""
echo "✓ Deployment complete!"
echo "Refresh your browser at http://skydio-nt.local:5001/settings"
