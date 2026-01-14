#!/bin/bash
# Skydio Network Tester - Kiosk Mode Setup Script
# This script configures a Raspberry Pi to boot directly into the network tester in kiosk mode

set -e

echo "=========================================="
echo "Skydio Network Tester - Kiosk Mode Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-pi}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "Setting up kiosk mode for user: $ACTUAL_USER"
echo "User home directory: $USER_HOME"
echo ""

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y \
    chromium-browser \
    unclutter \
    xdotool \
    x11-xserver-utils \
    xinit \
    openbox \
    lightdm

echo ""
echo "Configuring auto-login..."

# Configure LightDM for auto-login
mkdir -p /etc/lightdm/lightdm.conf.d/
cat > /etc/lightdm/lightdm.conf.d/autologin.conf << EOF
[Seat:*]
autologin-user=$ACTUAL_USER
autologin-user-timeout=0
EOF

echo ""
echo "Creating kiosk startup script..."

# Create kiosk startup script
cat > $USER_HOME/.config/openbox/autostart << 'EOF'
#!/bin/bash

# Disable screen blanking and power management
xset s off
xset s noblank
xset -dpms

# Hide mouse cursor when idle
unclutter -idle 0.1 &

# Wait for network to be ready
sleep 5

# Start Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-features=TranslateUI \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --check-for-update-interval=31536000 \
    --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT' \
    http://localhost:5001/mobile &

# Keep the script running
wait
EOF

# Create openbox config directory if it doesn't exist
mkdir -p $USER_HOME/.config/openbox
chown -R $ACTUAL_USER:$ACTUAL_USER $USER_HOME/.config/openbox
chmod +x $USER_HOME/.config/openbox/autostart

echo ""
echo "Configuring X session..."

# Create .xinitrc to start openbox
cat > $USER_HOME/.xinitrc << 'EOF'
#!/bin/bash
exec openbox-session
EOF

chown $ACTUAL_USER:$ACTUAL_USER $USER_HOME/.xinitrc
chmod +x $USER_HOME/.xinitrc

echo ""
echo "Configuring systemd service..."

# Update Flask app to use mobile interface by default
INSTALL_DIR="$USER_HOME/skydio-network-tester"

# Add route for /mobile in app.py if not already present
if [ -f "$INSTALL_DIR/app.py" ]; then
    if ! grep -q "@app.route('/mobile')" "$INSTALL_DIR/app.py"; then
        echo "Adding mobile route to app.py..."
        # This will be done via Python edit
    fi
fi

echo ""
echo "Setting up display configuration for 3.5 inch screen..."

# Create display configuration script
cat > /usr/local/bin/setup-display.sh << 'EOF'
#!/bin/bash
# Configure display for 3.5" screen
# Common resolutions: 480x320 or 320x480

# Try to detect display and set appropriate resolution
if xrandr | grep -q "connected"; then
    # Set to common 3.5" screen resolution
    xrandr --output HDMI-1 --mode 480x320 2>/dev/null || \
    xrandr --output HDMI-1 --mode 320x480 2>/dev/null || \
    echo "Using default resolution"
fi
EOF

chmod +x /usr/local/bin/setup-display.sh

echo ""
echo "Enabling services..."

# Enable LightDM
systemctl enable lightdm

echo ""
echo "=========================================="
echo "Kiosk Mode Setup Complete!"
echo "=========================================="
echo ""
echo "The system will now:"
echo "  1. Auto-login as user '$ACTUAL_USER'"
echo "  2. Start X server with Openbox"
echo "  3. Launch Chromium in kiosk mode"
echo "  4. Display the network tester on http://localhost:5001/mobile"
echo ""
echo "IMPORTANT: Make sure the network tester service is enabled:"
echo "  sudo systemctl enable skydio-network-tester.service"
echo "  sudo systemctl start skydio-network-tester.service"
echo ""
echo "To test without rebooting:"
echo "  sudo systemctl start lightdm"
echo ""
echo "Reboot to activate kiosk mode:"
echo "  sudo reboot"
echo ""
