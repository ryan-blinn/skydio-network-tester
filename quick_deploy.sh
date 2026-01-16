#!/bin/bash
# Quick deployment helper (uses your SSH auth: password prompt or SSH keys)

PI_HOST="skydio-nt.local"
PI_USER="pi"
REMOTE_DIR="/home/$PI_USER/skydio-network-tester"

echo "Deploying to $PI_HOST..."

scp templates/settings.html $PI_USER@$PI_HOST:$REMOTE_DIR/templates/
ssh $PI_USER@$PI_HOST "sudo systemctl restart skydio-network-tester.service"

echo "✓ Deployed! Refresh browser with Cmd+Shift+R"
