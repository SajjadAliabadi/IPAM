#!/bin/bash
echo "=========================================="
echo " IPAM Enterprise - Update Script"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./update_ubuntu.sh)"
  exit
fi

echo "[1/4] Pulling latest changes from Git..."
git fetch origin main
git reset --hard origin/main

echo "[2/4] Activating Virtual Environment and updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "[3/4] Collecting Static Files & Migrating Database..."
python manage.py collectstatic --noinput
python manage.py migrate
echo "      Setting up default permission groups..."
python manage.py setup_default_groups

echo "[4/4] Restarting IPAM Services..."
systemctl restart ipam-web.service
systemctl restart ipam-scanner.service

echo "=========================================="
echo " Update Complete!"
echo " Check status with: systemctl status ipam-web"
echo "=========================================="
