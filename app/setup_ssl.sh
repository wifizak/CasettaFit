#!/bin/bash

# CasettaFit SSL/HTTPS Setup Script
# Supports: Self-Signed, Let's Encrypt, or Custom Certificate Upload

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== CasettaFit SSL/HTTPS Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Get domain/hostname
echo -e "${YELLOW}Enter your domain or hostname:${NC}"
read -p "Domain: " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Domain cannot be empty${NC}"
    exit 1
fi

# Choose certificate type
echo ""
echo "Choose certificate type:"
echo "1) Let's Encrypt (free, auto-renewing, requires valid domain)"
echo "2) Self-Signed Certificate (for testing/internal use)"
echo "3) Upload Custom Certificate"
echo ""
read -p "Selection (1-3): " CERT_TYPE

case $CERT_TYPE in
    1)
        echo ""
        echo -e "${YELLOW}Setting up Let's Encrypt...${NC}"
        
        # Check if certbot is installed
        if ! command -v certbot &> /dev/null; then
            echo "Installing certbot..."
            apt-get update
            apt-get install -y certbot python3-certbot-nginx
        fi
        
        # Update NGINX config with domain
        sed -i "s/server_name .*/server_name $DOMAIN;/" /etc/nginx/sites-available/casettafit
        nginx -t && systemctl reload nginx
        
        # Get email for Let's Encrypt notifications
        echo ""
        read -p "Email for certificate notifications (or press Enter to skip): " EMAIL
        
        if [ -z "$EMAIL" ]; then
            certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect
        else
            certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect
        fi
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Let's Encrypt certificate installed successfully!${NC}"
            echo -e "${GREEN}✓ Auto-renewal is configured${NC}"
        else
            echo ""
            echo -e "${RED}Failed to obtain Let's Encrypt certificate.${NC}"
            echo "Make sure:"
            echo "  1. DNS is properly configured for $DOMAIN"
            echo "  2. Port 80 and 443 are open"
            echo "  3. Domain points to this server"
            exit 1
        fi
        ;;
        
    2)
        echo ""
        echo -e "${YELLOW}Creating self-signed certificate...${NC}"
        
        # Create directory for certificates
        mkdir -p /etc/nginx/ssl
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/casettafit.key \
            -out /etc/nginx/ssl/casettafit.crt \
            -subj "/CN=$DOMAIN"
        
        chmod 600 /etc/nginx/ssl/casettafit.key
        chmod 644 /etc/nginx/ssl/casettafit.crt
        
        # Update NGINX config
        cat > /etc/nginx/sites-available/casettafit << 'NGINXEOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    ssl_certificate /etc/nginx/ssl/casettafit.crt;
    ssl_certificate_key /etc/nginx/ssl/casettafit.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
NGINXEOF
        
        sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/casettafit
        
        nginx -t && systemctl reload nginx
        
        echo ""
        echo -e "${GREEN}✓ Self-signed certificate created successfully!${NC}"
        echo -e "${YELLOW}⚠ Browsers will show a security warning for self-signed certificates${NC}"
        ;;
        
    3)
        echo ""
        echo -e "${YELLOW}Custom certificate upload...${NC}"
        
        # Create directory for certificates
        mkdir -p /etc/nginx/ssl
        
        echo ""
        echo "Please provide the paths to your certificate files:"
        read -p "Certificate file (.crt or .pem): " CERT_FILE
        read -p "Private key file (.key): " KEY_FILE
        read -p "CA bundle/chain file (optional, press Enter to skip): " CHAIN_FILE
        
        if [ ! -f "$CERT_FILE" ]; then
            echo -e "${RED}Certificate file not found: $CERT_FILE${NC}"
            exit 1
        fi
        
        if [ ! -f "$KEY_FILE" ]; then
            echo -e "${RED}Private key file not found: $KEY_FILE${NC}"
            exit 1
        fi
        
        # Copy certificates
        cp "$CERT_FILE" /etc/nginx/ssl/casettafit.crt
        cp "$KEY_FILE" /etc/nginx/ssl/casettafit.key
        
        if [ -n "$CHAIN_FILE" ] && [ -f "$CHAIN_FILE" ]; then
            cat "$CERT_FILE" "$CHAIN_FILE" > /etc/nginx/ssl/casettafit-fullchain.crt
            CERT_PATH="/etc/nginx/ssl/casettafit-fullchain.crt"
        else
            CERT_PATH="/etc/nginx/ssl/casettafit.crt"
        fi
        
        chmod 600 /etc/nginx/ssl/casettafit.key
        chmod 644 /etc/nginx/ssl/casettafit*.crt
        
        # Update NGINX config
        cat > /etc/nginx/sites-available/casettafit << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $CERT_PATH;
    ssl_certificate_key /etc/nginx/ssl/casettafit.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
NGINXEOF
        
        nginx -t && systemctl reload nginx
        
        echo ""
        echo -e "${GREEN}✓ Custom certificate installed successfully!${NC}"
        ;;
        
    *)
        echo -e "${RED}Invalid selection${NC}"
        exit 1
        ;;
esac

echo ""
echo "=== SSL Setup Complete! ==="
echo ""
echo -e "${GREEN}Your site is now accessible at: https://$DOMAIN${NC}"
echo ""
echo "Certificate details:"
case $CERT_TYPE in
    1)
        echo "  Type: Let's Encrypt"
        echo "  Auto-renewal: Enabled (via certbot timer)"
        echo "  Check renewal: sudo certbot renew --dry-run"
        ;;
    2)
        echo "  Type: Self-Signed"
        echo "  Location: /etc/nginx/ssl/"
        echo "  Valid for: 365 days"
        echo "  ⚠ Browsers will show security warnings"
        ;;
    3)
        echo "  Type: Custom Certificate"
        echo "  Location: /etc/nginx/ssl/"
        ;;
esac
echo ""
