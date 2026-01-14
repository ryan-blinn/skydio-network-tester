#!/bin/bash
# Skydio Network Tester - 3.5" Display Driver Setup
# This script installs and configures drivers for common 3.5" TFT displays

set -e

echo "=========================================="
echo "3.5 Inch Display Driver Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "This script supports the following 3.5\" displays:"
echo "  1. Waveshare 3.5\" RPi LCD (A) - 480x320"
echo "  2. Waveshare 3.5\" RPi LCD (B) - 480x320"
echo "  3. Waveshare 3.5\" RPi LCD (C) - 480x320"
echo "  4. Generic 3.5\" SPI TFT - 480x320"
echo "  5. HDMI 3.5\" Display - 480x320"
echo "  6. Skip driver installation (already configured)"
echo ""

read -p "Select your display type (1-6): " DISPLAY_TYPE

case $DISPLAY_TYPE in
    1|2|3|4)
        echo ""
        echo "Installing SPI TFT drivers..."
        
        # Install required packages
        apt-get update
        apt-get install -y git cmake
        
        # Clone LCD-show repository (common for Waveshare displays)
        cd /tmp
        if [ -d "LCD-show" ]; then
            rm -rf LCD-show
        fi
        
        git clone https://github.com/waveshare/LCD-show.git
        cd LCD-show
        chmod +x *.sh
        
        case $DISPLAY_TYPE in
            1)
                echo "Installing Waveshare 3.5\" LCD (A) driver..."
                ./LCD35-show
                ;;
            2)
                echo "Installing Waveshare 3.5\" LCD (B) driver..."
                ./LCD35B-show
                ;;
            3)
                echo "Installing Waveshare 3.5\" LCD (C) driver..."
                ./LCD35C-show
                ;;
            4)
                echo "Installing Generic 3.5\" SPI driver..."
                ./LCD35-show
                ;;
        esac
        
        echo ""
        echo "Driver installation complete!"
        echo "The system will reboot to apply changes."
        ;;
        
    5)
        echo ""
        echo "Configuring HDMI 3.5\" display..."
        
        # Configure /boot/config.txt for HDMI display
        CONFIG_FILE="/boot/config.txt"
        
        # Backup config
        cp $CONFIG_FILE ${CONFIG_FILE}.backup
        
        # Add HDMI configuration
        cat >> $CONFIG_FILE << 'EOF'

# 3.5" HDMI Display Configuration
hdmi_group=2
hdmi_mode=87
hdmi_cvt=480 320 60 6 0 0 0
hdmi_drive=2
EOF
        
        echo "HDMI configuration added to $CONFIG_FILE"
        echo "Backup saved to ${CONFIG_FILE}.backup"
        echo ""
        echo "Please reboot to apply changes: sudo reboot"
        ;;
        
    6)
        echo ""
        echo "Skipping driver installation."
        echo "Assuming display is already configured."
        ;;
        
    *)
        echo "Invalid selection. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Display Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. If not rebooted automatically, run: sudo reboot"
echo "  2. After reboot, run: sudo ./setup_kiosk.sh"
echo "  3. Configure the network tester service"
echo ""
