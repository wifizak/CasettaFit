#!/bin/bash

# CasettaFit Installation and Setup Script
# Run this script to set up the application on a fresh Ubuntu server

set -e

echo "=== CasettaFit Setup Script ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx

echo "Creating Python virtual environment..."
cd /opt/CasettaFit/app
python3 -m venv venv

# Create necessary directories
mkdir -p logs
mkdir -p uploads

source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Initializing database..."
export PYTHONPATH=/opt/CasettaFit
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "Seeding admin user..."
python3 -c "
import sys
sys.path.insert(0, '/opt/CasettaFit')
from app import create_app, db
from app.models import User, UserProfile

app = create_app('production')

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.flush()
        
        profile = UserProfile(user_id=admin.id)
        db.session.add(profile)
        
        db.session.commit()
        print('Admin user created successfully!')
    else:
        print('Admin user already exists.')
"

echo "Setting permissions..."
chown -R www-data:www-data /opt/CasettaFit/app
chmod -R 755 /opt/CasettaFit/app
# Ensure www-data can write to logs and database
chmod 775 /opt/CasettaFit/app/logs
chmod 664 /opt/CasettaFit/app/casettafit.db* 2>/dev/null || true

echo "Configuring Gunicorn service..."
cp /opt/CasettaFit/app/casettafit.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable casettafit
systemctl start casettafit

echo "Configuring NGINX..."
cp /opt/CasettaFit/app/nginx.conf /etc/nginx/sites-available/casettafit
ln -sf /etc/nginx/sites-available/casettafit /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "CasettaFit is now running!"
echo "Access it at: http://your-server-ip"
echo ""
echo "Default admin credentials:"
echo "Username: admin"
echo "Password: adminpass"
echo ""
echo "IMPORTANT: Change the admin password after first login!"
echo ""
echo "Service commands:"
echo "  - View logs: journalctl -u casettafit -f"
echo "  - Restart app: systemctl restart casettafit"
echo "  - Check status: systemctl status casettafit"
echo ""
