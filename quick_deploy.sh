#!/bin/bash
 
PI_HOST="skydio-nt.local"
PI_USER="pi"
REMOTE_DIR="/home/$PI_USER/skydio-network-tester"

echo "Run these commands to deploy:"
echo ""
echo "scp templates/settings.html $PI_USER@$PI_HOST:$REMOTE_DIR/templates/"
echo "ssh $PI_USER@$PI_HOST 'sudo systemctl restart skydio-network-tester.service'"
echo ""
echo "Then refresh browser with Cmd+Shift+R"
