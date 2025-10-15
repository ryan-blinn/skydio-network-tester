# Quick Deploy Reference Card

## 🚀 Deploy New Version (One Command)

```bash
./deploy.sh skydiort01.local && ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && sudo systemctl restart skydio-network-tester"
```

---

## 📋 Step-by-Step Deployment

### 1. Transfer Files
```bash
./deploy.sh skydiort01.local
```

### 2. Install/Update on Pi
```bash
ssh pi@skydiort01.local
cd /home/pi/skydio-network-tester
./install_raspberry_pi.sh
```

### 3. Start Service
```bash
sudo systemctl start skydio-network-tester
```

---

## 🔍 Common Commands

### Check Status
```bash
ssh pi@skydiort01.local "sudo systemctl status skydio-network-tester"
```

### View Logs
```bash
ssh pi@skydiort01.local "sudo journalctl -u skydio-network-tester -f"
```

### Restart Service
```bash
ssh pi@skydiort01.local "sudo systemctl restart skydio-network-tester"
```

### Fix Permissions (if settings won't save)
```bash
ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && chmod 644 config.json && chown pi:pi config.json && sudo systemctl restart skydio-network-tester"
```

---

## 🌐 Access Web Interface

- **By hostname**: http://skydiort01.local:5001
- **By IP**: http://192.168.1.XXX:5001

---

## ⚠️ Troubleshooting

### Settings Won't Save
```bash
# Ensure config.json exists with proper permissions
ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && ls -la config.json"

# If missing or wrong permissions, fix it:
ssh pi@skydiort01.local "cd /home/pi/skydio-network-tester && chmod 644 config.json && chown pi:pi config.json"
```

### Service Won't Start
```bash
# Check logs for errors
ssh pi@skydiort01.local "sudo journalctl -u skydio-network-tester -n 50"
```

### Can't Connect
```bash
# Test SSH connection
ssh pi@skydiort01.local

# If hostname fails, use IP
ssh pi@192.168.1.XXX
```

---

## 📝 Notes

- **Default Port**: 5001
- **Config File**: `/home/pi/skydio-network-tester/config.json`
- **Service Name**: `skydio-network-tester`
- **User**: `pi`

---

## 🔧 First Time Setup

```bash
# 1. Deploy files
./deploy.sh skydiort01.local

# 2. SSH and install
ssh pi@skydiort01.local
cd /home/pi/skydio-network-tester
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh

# 3. Service starts automatically after install
# Access at: http://skydiort01.local:5001
```
