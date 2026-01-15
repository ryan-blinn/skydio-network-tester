#!/bin/bash
# Skydio Network Tester - Quick Install Script
# One-line installer for easy deployment
# Usage: curl -fsSL https://raw.githubusercontent.com/ryan-blinn/skydio-network-tester/main/quick_install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BOOTSTRAP_URL="https://raw.githubusercontent.com/ryan-blinn/skydio-network-tester/main/scripts/bootstrap_pi.sh"

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

echo -e "${BLUE}Starting installer...${NC}"
curl -fsSL "$BOOTSTRAP_URL" | bash
