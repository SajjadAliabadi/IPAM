#!/bin/bash
echo "=========================================="
echo " IPAM Enterprise - Ubuntu Installation"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install_ubuntu.sh)"
  exit
fi

echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv sqlite3

echo "Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create Database and Migrate if db.sqlite3 does not exist
if [ ! -f "db.sqlite3" ]; then
    echo "Creating Database and Migrations..."
    python manage.py makemigrations
    python manage.py migrate
    
    echo "====================================================="
    echo " ATTENTION: No database found! Creating Admin user."
    echo " Please enter a username and password for the admin:"
    echo "====================================================="
    python manage.py createsuperuser
fi

# Collect static files
python manage.py collectstatic --noinput

echo "Creating Web Server Systemd Service..."
cat << EOF > /etc/systemd/system/ipam-web.service
[Unit]
Description=IPAM Enterprise Web Server (CherryPy)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PWD
ExecStart=$PWD/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Creating Background Scanner Systemd Service..."
cat << EOF > /etc/systemd/system/ipam-scanner.service
[Unit]
Description=IPAM Enterprise Background Scanner
After=network.target ipam-web.service

[Service]
Type=simple
User=root
WorkingDirectory=$PWD
ExecStart=$PWD/venv/bin/python manage.py auto_scan
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and Starting Services..."
systemctl daemon-reload
systemctl enable ipam-web.service
systemctl enable ipam-scanner.service
systemctl restart ipam-web.service
systemctl restart ipam-scanner.service

echo "=========================================="
echo " Installation Complete!"
echo " Web Server is running on port 80."
echo " Check status with: systemctl status ipam-web"
echo "=========================================="
