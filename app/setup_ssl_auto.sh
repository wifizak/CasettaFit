#!/bin/bash

# Automated SSL Setup for fit.casettacloud.com with Let's Encrypt
# This script assumes DNS is already configured

set -e

DOMAIN="fit.casettacloud.com"

echo "=== CasettaFit SSL Setup for $DOMAIN ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check DNS
echo "Checking DNS configuration..."
DNS_IP=$(host "$DOMAIN" | grep "has address" | awk '{print $4}' || echo "")

if [ -z "$DNS_IP" ]; then
    echo "⚠ DNS not configured for $DOMAIN"
    echo "Please configure DNS A record"
    exit 1
else
    echo "✓ DNS configured: $DOMAIN -> $DNS_IP"
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo ""
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Update NGINX config with domain
echo ""
echo "Updating NGINX configuration..."
sed -i "s/server_name .*/server_name $DOMAIN;/" /etc/nginx/sites-available/casettafit
nginx -t && systemctl reload nginx

# Get Let's Encrypt certificate
echo ""
echo "Obtaining Let's Encrypt certificate..."
echo "This may take a moment..."

certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect

if [ $? -eq 0 ]; then
    echo ""
    echo "=== SSL Setup Complete! ==="
    echo ""
    echo "✓ Let's Encrypt certificate installed"
    echo "✓ HTTPS enabled with auto-redirect from HTTP"
    echo "✓ Auto-renewal configured"
    echo ""
    echo "Access your site at: https://$DOMAIN"
    echo ""
    echo "Certificate info:"
    certbot certificates
else
    echo ""
    echo "Failed to obtain certificate. Please check:"
    echo "  1. DNS is propagated (may take a few minutes)"
    echo "  2. Ports 80 and 443 are open"
    echo "  3. No firewall blocking Let's Encrypt"
    exit 1
fi
