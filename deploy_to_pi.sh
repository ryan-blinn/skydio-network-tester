#!/bin/bash
# Deploy Skydio Network Tester to Raspberry Pi
# Usage: ./deploy_to_pi.sh <pi-hostname-or-ip> [username]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PI_USER="${2:-pi}"
PI_HOST="${1:-skydio-nt.local}"
REMOTE_DIR="/home/$PI_USER/skydio-network-tester"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if hostname provided
if [ -z "$PI_HOST" ]; then
    echo -e "${RED}Error: Raspberry Pi hostname or IP required${NC}"
    echo "Usage: $0 [pi-hostname-or-ip] [username]"
    echo "Example: $0 skydio-nt.local"
    echo "Example: $0 192.168.1.100 pi"
    echo "Default: $0 (uses skydio-nt.local and pi)"
    exit 1
fi

echo "=========================================="
echo "Skydio Network Tester - Deploy to Pi"
echo "=========================================="
echo ""
echo "Target: $PI_USER@$PI_HOST"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
echo "Attempting to connect to $PI_USER@$PI_HOST"
echo "(You may be prompted for a password)"
echo ""
if ! ssh -o ConnectTimeout=10 "$PI_USER@$PI_HOST" "echo 'Connection test successful'" 2>/dev/null; then
    echo -e "${RED}Cannot connect to $PI_USER@$PI_HOST${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Verify Pi is powered on: ping $PI_HOST"
    echo "  2. Check SSH is enabled on Pi"
    echo "  3. Verify username is correct (current: $PI_USER)"
    echo "  4. Try connecting manually: ssh $PI_USER@$PI_HOST"
    echo ""
    echo "To set up passwordless SSH (recommended):"
    echo "  ssh-copy-id $PI_USER@$PI_HOST"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"
echo ""

# Create remote directory
echo -e "${YELLOW}Creating remote directory...${NC}"
ssh "$PI_USER@$PI_HOST" "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✓ Directory created${NC}"
echo ""

# Sync files using rsync
echo -e "${YELLOW}Syncing files to Raspberry Pi...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='exports/*' \
    --exclude='test_history/*' \
    --exclude='*.log' \
    "$LOCAL_DIR/" "$PI_USER@$PI_HOST:$REMOTE_DIR/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Files synced successfully${NC}"
else
    echo -e "${RED}✗ File sync failed${NC}"
    exit 1
fi
echo ""

# Make scripts executable
echo -e "${YELLOW}Setting script permissions...${NC}"
ssh "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && chmod +x *.sh"
echo -e "${GREEN}✓ Scripts made executable${NC}"
echo ""

# Ask if user wants to run installation
echo -e "${YELLOW}Would you like to run the installation script now? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Running installation script...${NC}"
    ssh -t "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && ./install_raspberry_pi.sh"
    
    echo ""
    echo -e "${YELLOW}Would you like to enable the service? (y/n)${NC}"
    read -r service_response
    if [[ "$service_response" =~ ^[Yy]$ ]]; then
        ssh -t "$PI_USER@$PI_HOST" "sudo systemctl enable skydio-network-tester.service && sudo systemctl start skydio-network-tester.service"
        echo -e "${GREEN}✓ Service enabled and started${NC}"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Access web UI: http://$PI_HOST:5001"
echo "  2. Mobile UI: http://$PI_HOST:5001/mobile"
echo ""
echo "For kiosk mode setup:"
echo "  ssh $PI_USER@$PI_HOST"
echo "  cd $REMOTE_DIR"
echo "  sudo ./setup_kiosk.sh"
echo ""
echo "To check service status:"
echo "  ssh $PI_USER@$PI_HOST 'sudo systemctl status skydio-network-tester.service'"
echo ""
echo "To view logs:"
echo "  ssh $PI_USER@$PI_HOST 'sudo journalctl -u skydio-network-tester.service -f'"
echo ""
