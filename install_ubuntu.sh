#!/bin/bash
echo "=========================================="
echo " IPAM Enterprise - Ubuntu Installation"
echo "=========================================="

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install_ubuntu.sh)"
  exit
fi

# 1. Update and install dependencies
echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv sqlite3

# 2. Setup Virtual Environment
echo "Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create Systemd Service for CherryPy Web Server
echo "Creating Web Server Systemd Service..."
cat << 'EOF' > /etc/systemd/system/ipam-web.service
[Unit]
Description=IPAM Enterprise Web Server (CherryPy)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=C:\Users\Administrator\Desktop\IPAM
ExecStart=C:\Users\Administrator\Desktop\IPAM/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 4. Create Systemd Service for Background Scanner
echo "Creating Background Scanner Systemd Service..."
cat << 'EOF' > /etc/systemd/system/ipam-scanner.service
[Unit]
Description=IPAM Enterprise Background Scanner
After=network.target ipam-web.service

[Service]
Type=simple
User=root
WorkingDirectory=C:\Users\Administrator\Desktop\IPAM
ExecStart=C:\Users\Administrator\Desktop\IPAM/venv/bin/python manage.py auto_scan
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# 5. Apply and Start Services
echo "Enabling and Starting Services..."
systemctl daemon-reload
systemctl enable ipam-web.service
systemctl enable ipam-scanner.service
systemctl start ipam-web.service
systemctl start ipam-scanner.service

echo "=========================================="
echo " Installation Complete!"
echo " Web Server is running on port 80."
echo " Check status with: systemctl status ipam-web"
echo "=========================================="
