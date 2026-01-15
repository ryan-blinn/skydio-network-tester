#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_URL_DEFAULT="https://github.com/ryan-blinn/skydio-network-tester"
BRANCH_DEFAULT="main"
INSTALL_DIR_DEFAULT="$HOME/skydio-network-tester"

INPUT_FD=0
if ! [ -t 0 ] && [ -r /dev/tty ]; then
  exec 3</dev/tty
  INPUT_FD=3
fi

read_from_input() {
  local __var_name="$1"
  if [ "$INPUT_FD" -eq 0 ]; then
    read -r "$__var_name" || true
  else
    read -r -u "$INPUT_FD" "$__var_name" || true
  fi
}

print_header() {
  echo ""
  echo "=========================================="
  echo "  Skydio Network Tester - Pi Installer"
  echo "=========================================="
  echo ""
}

prompt_yes_no() {
  local prompt="$1"
  local default="$2" # y or n
  local ans

  while true; do
    if [ "$default" = "y" ]; then
      printf "%s [Y/n]: " "$prompt"
    else
      printf "%s [y/N]: " "$prompt"
    fi

    read_from_input ans
    ans="${ans:-$default}"

    case "$ans" in
      y|Y) return 0 ;;
      n|N) return 1 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_apt_packages() {
  local pkgs=("$@")

  echo -e "${BLUE}Updating package lists...${NC}"
  sudo apt update -y

  echo -e "${BLUE}Installing system packages...${NC}"
  sudo apt install -y "${pkgs[@]}"
}

ensure_networkmanager() {
  echo -e "${BLUE}Configuring NetworkManager (nmcli)...${NC}"

  sudo systemctl enable NetworkManager
  sudo systemctl start NetworkManager

  local user
  user="${SUDO_USER:-$(whoami)}"
  sudo usermod -aG netdev "$user" || true
}

os_codename() {
  if [ -r /etc/os-release ]; then
    . /etc/os-release
    echo "${VERSION_CODENAME:-}"
  fi
}

dpkg_arch() {
  dpkg --print-architecture 2>/dev/null || true
}

install_goodtft_mhs35_driver() {
  echo ""
  echo -e "${YELLOW}3.5\" LCD Driver (GoodTFT/LCD-show)${NC}"

  local codename
  local arch
  codename="$(os_codename)"
  arch="$(dpkg_arch)"

  if [ "$codename" = "bookworm" ]; then
    echo -e "${YELLOW}Warning:${NC} LCD-show is widely reported as unreliable on Raspberry Pi OS Bookworm."
    echo "Recommended OS for this screen is Raspberry Pi OS Bullseye (Legacy)."
    if ! prompt_yes_no "Continue anyway?" "n"; then
      return 1
    fi
  fi

  if [ "$arch" = "arm64" ]; then
    echo -e "${YELLOW}Warning:${NC} LCD-show has known compatibility issues on 64-bit (arm64) Raspberry Pi OS."
    echo "If this fails, use Raspberry Pi OS 32-bit (armhf) Bullseye (Legacy)."
    if ! prompt_yes_no "Continue anyway?" "n"; then
      return 1
    fi
  fi

  echo -e "${BLUE}Installing LCD driver...${NC}"
  sudo apt update -y
  sudo apt install -y git

  if [ -d /boot/firmware ]; then
    if [ -f /boot/firmware/config.txt ]; then
      ts="$(date +%Y%m%d-%H%M%S)"
      sudo cp -a /boot/firmware/config.txt "/boot/firmware/config.txt.skydio-backup.${ts}" || true
    fi

    if [ ! -e /boot/config.txt ] && [ -f /boot/firmware/config.txt ]; then
      sudo ln -s /boot/firmware/config.txt /boot/config.txt
    fi

    if [ ! -e /boot/overlays ] && [ -d /boot/firmware/overlays ]; then
      sudo ln -s /boot/firmware/overlays /boot/overlays
    fi
  fi

  sudo rm -rf /tmp/LCD-show
  git clone https://github.com/goodtft/LCD-show.git /tmp/LCD-show
  sudo chmod -R 755 /tmp/LCD-show
  (cd /tmp/LCD-show && sudo ./MHS35-show)

  return 0
}

clone_or_update_repo() {
  local repo_url="$1"
  local branch="$2"
  local install_dir="$3"

  if [ -d "$install_dir/.git" ]; then
    echo -e "${YELLOW}Existing installation found at ${install_dir}${NC}"
    echo "What would you like to do?"
    echo "  1) Update existing installation"
    echo "  2) Remove and reinstall"
    echo "  3) Cancel"
    printf "Enter choice [1-3]: "
    read_from_input choice

    case "$choice" in
      1)
        echo -e "${BLUE}Updating existing installation...${NC}"
        git -C "$install_dir" fetch origin "$branch"
        git -C "$install_dir" checkout "$branch"
        git -C "$install_dir" pull --ff-only origin "$branch"
        ;;
      2)
        echo -e "${BLUE}Removing existing installation...${NC}"
        rm -rf "$install_dir"
        echo -e "${BLUE}Cloning repository...${NC}"
        git clone -b "$branch" "$repo_url" "$install_dir"
        ;;
      *)
        echo "Installation cancelled."
        exit 0
        ;;
    esac
  elif [ -d "$install_dir" ] && [ "$(ls -A "$install_dir" 2>/dev/null | wc -l | tr -d ' ')" != "0" ]; then
    echo -e "${RED}Error:${NC} ${install_dir} exists but is not a git repo."
    echo "Please move it aside or choose a different install directory."
    exit 1
  else
    echo -e "${BLUE}Cloning repository...${NC}"
    git clone -b "$branch" "$repo_url" "$install_dir"
  fi

  echo -e "${GREEN}✓ Repository ready${NC}"
  echo ""
}

run_app_installer() {
  local install_dir="$1"

  echo -e "${BLUE}Running application installer...${NC}"
  chmod +x "$install_dir"/*.sh || true
  (cd "$install_dir" && ./install_raspberry_pi.sh)
}

start_standard_mode() {
  echo -e "${BLUE}Enabling and starting service...${NC}"
  sudo systemctl enable skydio-network-tester.service
  sudo systemctl start skydio-network-tester.service

  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"

  echo ""
  echo -e "${GREEN}✓ Service started${NC}"
  echo ""
  echo "Open the web UI:"
  if [ -n "$ip" ]; then
    echo "  Desktop UI: http://$ip:5001"
    echo "  Mobile UI:  http://$ip:5001/mobile"
  else
    echo "  Desktop UI: http://<pi-ip>:5001"
    echo "  Mobile UI:  http://<pi-ip>:5001/mobile"
  fi
  echo ""
  echo "Check logs: sudo journalctl -u skydio-network-tester.service -f"
}

setup_kiosk_mode() {
  local install_dir="$1"

  echo ""
  echo -e "${YELLOW}Kiosk Mode Setup${NC}"
  echo ""

  sudo "$install_dir/setup_kiosk.sh"

  echo ""
  echo -e "${GREEN}✓ Kiosk mode configured${NC}"
  echo ""

  if prompt_yes_no "Install GoodTFT MHS 3.5\" LCD driver (MHS35-show)?" "n"; then
    if install_goodtft_mhs35_driver; then
      echo ""
      echo -e "${GREEN}✓ LCD driver installation triggered${NC}"
    else
      echo ""
      echo -e "${YELLOW}LCD driver installation skipped${NC}"
    fi
  else
    if prompt_yes_no "Install other display drivers (Waveshare/generic) via setup_display_drivers.sh?" "n"; then
      sudo "$install_dir/setup_display_drivers.sh"
    fi
  fi

  if prompt_yes_no "Reboot now to start kiosk mode?" "y"; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
  else
    echo "Reboot later with: sudo reboot"
  fi
}

post_install_reboot_hint() {
  local user
  user="${SUDO_USER:-$(whoami)}"

  echo ""
  echo -e "${YELLOW}Note:${NC} NetworkManager permission changes may require a reboot or re-login."
  echo "If WiFi management in Settings fails, reboot the Pi: sudo reboot"
  echo "(User $user was added to the netdev group.)"
}

main() {
  print_header

  if ! need_cmd sudo; then
    echo -e "${RED}Error:${NC} sudo is required."
    exit 1
  fi

  echo -e "${BLUE}Preflight checks...${NC}"

  if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning:${NC} this doesn't appear to be a Raspberry Pi."
    if ! prompt_yes_no "Continue anyway?" "n"; then
      exit 0
    fi
  fi

  local repo_url="$REPO_URL_DEFAULT"
  local branch="$BRANCH_DEFAULT"
  local install_dir="$INSTALL_DIR_DEFAULT"

  echo ""
  echo "Install directory: $install_dir"
  if prompt_yes_no "Use a different install directory?" "n"; then
    printf "Enter install directory: "
    read_from_input install_dir
    install_dir="${install_dir:-$INSTALL_DIR_DEFAULT}"
  fi

  echo ""
  echo -e "${BLUE}Installing prerequisites...${NC}"
  ensure_apt_packages python3 python3-pip python3-venv git curl speedtest-cli network-manager

  ensure_networkmanager

  echo ""
  clone_or_update_repo "$repo_url" "$branch" "$install_dir"

  run_app_installer "$install_dir"

  echo ""
  echo "=========================================="
  echo -e "${GREEN}Installation Complete${NC}"
  echo "=========================================="

  post_install_reboot_hint

  echo ""
  echo "What would you like to do next?"
  echo "  1) Start service now (standard mode)"
  echo "  2) Setup kiosk mode (3.5\" display)"
  echo "  3) Just install, I'll configure later"
  printf "Enter choice [1-3]: "
  read_from_input next_step

  case "$next_step" in
    1)
      start_standard_mode
      ;;
    2)
      setup_kiosk_mode "$install_dir"
      ;;
    *)
      echo ""
      echo "To start later:"
      echo "  sudo systemctl enable --now skydio-network-tester.service"
      echo ""
      echo "Install directory: $install_dir"
      ;;
  esac

  echo ""
  echo "Done."
}

main "$@"
