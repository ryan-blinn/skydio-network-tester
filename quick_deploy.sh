#!/bin/bash
# Quick deployment script with password authentication

PI_HOST="skydio-nt.local"
PI_USER="pi"
PI_PASS="Rylie101013!"
REMOTE_DIR="/home/$PI_USER/skydio-network-tester"

echo "Deploying to $PI_HOST..."

# Use expect to handle password
expect << EOF
set timeout 30
spawn scp templates/settings.html $PI_USER@$PI_HOST:$REMOTE_DIR/templates/
expect {
    "password:" { send "$PI_PASS\r"; exp_continue }
    eof
}

spawn ssh $PI_USER@$PI_HOST "sudo systemctl restart skydio-network-tester.service"
expect {
    "password:" { send "$PI_PASS\r"; exp_continue }
    eof
}
EOF

echo "✓ Deployed! Refresh browser with Cmd+Shift+R"
