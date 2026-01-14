#!/bin/bash
# Skydio Network Tester - Quick Install Script
# One-line installer for easy deployment
# Usage: curl -sSL https://raw.githubusercontent.com/YOUR_ORG/skydio-network-tester/main/quick_install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/YOUR_ORG/skydio-network-tester"
INSTALL_DIR="$HOME/skydio-network-tester"
BRANCH="main"

echo ""
echo "=========================================="
echo "  Skydio Network Tester - Quick Install"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    echo "This installer is optimized for Raspberry Pi. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

# Check for required commands
echo -e "${BLUE}Checking prerequisites...${NC}"
for cmd in git python3 pip3; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        echo "Please install $cmd first:"
        echo "  sudo apt-get update && sudo apt-get install -y $cmd"
        exit 1
    fi
done
echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Installation directory already exists${NC}"
    echo "Would you like to:"
    echo "  1) Update existing installation"
    echo "  2) Remove and reinstall"
    echo "  3) Cancel"
    read -r choice
    
    case $choice in
        1)
            echo -e "${BLUE}Updating existing installation...${NC}"
            cd "$INSTALL_DIR"
            git pull origin $BRANCH
            ;;
        2)
            echo -e "${BLUE}Removing existing installation...${NC}"
            rm -rf "$INSTALL_DIR"
            echo -e "${BLUE}Cloning repository...${NC}"
            git clone -b $BRANCH "$REPO_URL" "$INSTALL_DIR"
            cd "$INSTALL_DIR"
            ;;
        *)
            echo "Installation cancelled."
            exit 0
            ;;
    esac
else
    echo -e "${BLUE}Cloning repository...${NC}"
    git clone -b $BRANCH "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo -e "${GREEN}✓ Repository ready${NC}"
echo ""

# Make scripts executable
chmod +x *.sh

# Run installation
echo -e "${BLUE}Running installation script...${NC}"
./install_raspberry_pi.sh

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "What would you like to do next?"
echo ""
echo "  1) Start service now (standard mode)"
echo "  2) Setup kiosk mode (3.5\" display)"
echo "  3) Just install, I'll configure later"
echo ""
read -r next_step

case $next_step in
    1)
        echo -e "${BLUE}Enabling and starting service...${NC}"
        sudo systemctl enable skydio-network-tester.service
        sudo systemctl start skydio-network-tester.service
        
        # Get IP address
        IP=$(hostname -I | awk '{print $1}')
        
        echo ""
        echo -e "${GREEN}✓ Service started!${NC}"
        echo ""
        echo "Access the network tester:"
        echo "  Desktop UI: http://$IP:5001"
        echo "  Mobile UI:  http://$IP:5001/mobile"
        echo ""
        echo "Check status:"
        echo "  sudo systemctl status skydio-network-tester.service"
        ;;
    2)
        echo ""
        echo -e "${YELLOW}Kiosk Mode Setup${NC}"
        echo ""
        echo "Do you need to install display drivers? (y/n)"
        read -r display_response
        
        if [[ "$display_response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Running display driver setup...${NC}"
            sudo ./setup_display_drivers.sh
        fi
        
        echo -e "${BLUE}Running kiosk mode setup...${NC}"
        sudo ./setup_kiosk.sh
        
        echo ""
        echo -e "${GREEN}✓ Kiosk mode configured!${NC}"
        echo ""
        echo "Reboot now to start in kiosk mode? (y/n)"
        read -r reboot_response
        
        if [[ "$reboot_response" =~ ^[Yy]$ ]]; then
            echo "Rebooting in 5 seconds..."
            sleep 5
            sudo reboot
        else
            echo "Reboot later with: sudo reboot"
        fi
        ;;
    3)
        echo ""
        echo "Installation complete. To configure:"
        echo ""
        echo "Standard mode:"
        echo "  sudo systemctl enable skydio-network-tester.service"
        echo "  sudo systemctl start skydio-network-tester.service"
        echo ""
        echo "Kiosk mode:"
        echo "  cd $INSTALL_DIR"
        echo "  sudo ./setup_kiosk.sh"
        echo "  sudo reboot"
        ;;
esac

echo ""
echo "Documentation:"
echo "  Quick Start: $INSTALL_DIR/QUICK_START_KIOSK.md"
echo "  Full Guide:  $INSTALL_DIR/KIOSK_MODE_SETUP.md"
echo ""
