# CasettaFit
Home Gym Weight Lifting Tracker

## Overview

CasettaFit is a comprehensive workout tracking application designed for home gym enthusiasts. Track your exercises, monitor progress, and manage your fitness journey with a powerful yet intuitive interface.

## Quick Start

### Installation

1. Clone the repository to `/opt/CasettaFit`
2. Run the installation script:
```bash
cd /opt/CasettaFit/app
sudo bash setup.sh
```

3. Configure SSL/HTTPS (recommended):
```bash
sudo bash setup_ssl.sh
```

### First Login

- **URL**: https://your-server-ip/ or https://your-domain.com/
- **Username**: admin
- **Password**: adminpass

⚠️ **Change the admin password immediately after first login!**

## SSL/HTTPS Setup

CasettaFit supports three SSL certificate options. See [SSL_SETUP.md](SSL_SETUP.md) for detailed instructions.

### Option 1: Let's Encrypt (Recommended for Production)

**Automated setup:**
```bash
cd /opt/CasettaFit/app
sudo bash setup_ssl_auto.sh
```

**Manual setup:**
```bash
sudo bash setup_ssl.sh
# Select option 1
# Enter your domain name
```

**Features:**
- Free trusted SSL certificate
- Auto-renewal every 90 days
- No browser warnings

### Option 2: Self-Signed Certificate (Development/Testing)

```bash
sudo bash setup_ssl.sh
# Select option 2
```

**Note:** Browsers will show security warnings. Click "Advanced" → "Proceed" to continue.

### Option 3: Custom Certificate Upload

If you have your own SSL certificate:
```bash
sudo bash setup_ssl.sh
# Select option 3
# Provide paths to your certificate files
```

For detailed SSL setup instructions, troubleshooting, and certificate management, see **[SSL_SETUP.md](SSL_SETUP.md)**.

## System Service Management

The application runs as a systemd service using Gunicorn as the production WSGI server.

### Quick Commands

```bash
# Check service status
sudo systemctl status casettafit.service

# Start/Stop/Restart service
sudo systemctl start casettafit.service
sudo systemctl stop casettafit.service
sudo systemctl restart casettafit.service

# View real-time logs
sudo journalctl -u casettafit.service -f
```

### After Making Code Changes

```bash
sudo systemctl restart casettafit.service
```

### After Database Migrations

```bash
cd /opt/CasettaFit
source app/venv/bin/activate
flask db upgrade
sudo systemctl restart casettafit.service
```

### Application Logs

- **Access Log**: `/opt/CasettaFit/logs/access.log`
- **Error Log**: `/opt/CasettaFit/logs/error.log`

```bash
# View logs
tail -f /opt/CasettaFit/logs/access.log
tail -f /opt/CasettaFit/logs/error.log
```

## Service Configuration

- **Service File**: `/etc/systemd/system/casettafit.service`
- **Port**: 5000
- **Workers**: 4 Gunicorn workers
- **Auto-start**: Enabled on boot
- **User**: casettalocal

## NGINX Reverse Proxy

The application uses NGINX as a reverse proxy to the Gunicorn application server.

### Configuration

- **Config File**: `/etc/nginx/sites-available/casettafit`
- **Ports**: 
  - 80 (HTTP) - Redirects to HTTPS when SSL is configured
  - 443 (HTTPS) - Primary access when SSL is configured
- **Max Upload Size**: 10MB

### SSL Configuration

After running the initial setup, configure SSL using:
```bash
cd /opt/CasettaFit/app
sudo bash setup_ssl.sh
```

See [SSL_SETUP.md](SSL_SETUP.md) for detailed SSL setup instructions.

### Accessing the Application

- **With SSL**: `https://your-domain.com/`
- **Without SSL**: `http://your-server-ip/`

### NGINX Commands

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart NGINX
sudo systemctl restart nginx

# View NGINX logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Database Management

### Migrations

### Service Won't Start
```bash
# Check detailed status and logs
sudo systemctl status casettafit.service
sudo journalctl -u casettafit.service -n 100
tail -50 /opt/CasettaFit/logs/error.log
```

### Check Port Usage
```bash
sudo netstat -tulpn | grep :5000
```

### Reload Service Configuration
After editing `/etc/systemd/system/casettafit.service`:
```bash
sudo systemctl daemon-reload
sudo systemctl restart casettafit.service
```
