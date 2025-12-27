# CasettaFit
Home Gym Weight Lifting Tracker

## Overview

CasettaFit is a comprehensive workout tracking application designed for home gym enthusiasts. Track your exercises, monitor progress, and manage your fitness journey with a powerful yet intuitive interface.

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

The application uses NGINX as a reverse proxy to the Gunicorn application server with HTTPS enabled.

### Configuration

- **Config File**: `/etc/nginx/sites-available/casettafit.conf`
- **Server Name**: Accepts any hostname or IP address
- **Ports**: 
  - 443 (HTTPS) - Primary access
  - 80 (HTTP) - Redirects to HTTPS
- **SSL Certificate**: Self-signed certificate at `/etc/nginx/ssl/casettafit.crt`
- **Static Files**: Served directly by NGINX for better performance
- **Max Upload Size**: 10MB

### Accessing the Application

- **By IP**: `https://your-server-ip/` (recommended)
- **By hostname**: `https://casettafit.local/`
- **HTTP**: Automatically redirects to HTTPS

**Note**: Since this uses a self-signed certificate, browsers will show a security warning. Click "Advanced" and "Proceed" to continue.

### NGINX Commands

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart NGINX
sudo systemctl restart nginx

# View NGINX logs
tail -f /var/log/nginx/casettafit_access.log
tail -f /var/log/nginx/casettafit_error.log
```

### SSL Certificate Management

The current self-signed certificate is valid for 1 year. To regenerate:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/casettafit.key \
  -out /etc/nginx/ssl/casettafit.crt \
  -subj "/C=US/ST=State/L=City/O=CasettaFit/CN=your-domain.com"

sudo chmod 600 /etc/nginx/ssl/casettafit.key
sudo chmod 644 /etc/nginx/ssl/casettafit.crt
sudo systemctl reload nginx
```

For production, consider using Let's Encrypt for a trusted SSL certificate.

### Updating Server Name

If you want to restrict to a specific domain, edit `/etc/nginx/sites-available/casettafit.conf` and change:
```nginx
server_name _;  # Currently accepts any hostname or IP
```

To:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

Then reload NGINX:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Troubleshooting

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
