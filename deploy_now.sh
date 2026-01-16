#!/bin/bash
# Simple deployment - copy this command and run it manually

echo "Run these commands to deploy:"
echo ""
echo "cd ~/CascadeProjects/skydio-network-tester"
echo "scp templates/settings.html pi@skydio-nt.local:~/skydio-network-tester/templates/"
echo "ssh pi@skydio-nt.local 'sudo systemctl restart skydio-network-tester.service'"
echo ""
echo "Then refresh browser with Cmd+Shift+R"
