# CasettaFit SSL/HTTPS Setup

This guide covers setting up HTTPS for your CasettaFit installation using different certificate options.

## Prerequisites

- CasettaFit installed and running
- Root/sudo access to the server
- For Let's Encrypt: Valid domain name with DNS configured

## Option 1: Let's Encrypt (Recommended)

**Automated Setup for fit.casettacloud.com:**

1. Ensure DNS is configured to point to your server:
   ```bash
   # Check your server's IP
   hostname -I
   
   # Verify DNS points to your server
   host fit.casettacloud.com
   ```

2. Update DNS if needed:
   - Create an A record: `fit.casettacloud.com` → `YOUR_SERVER_IP`
   - Wait for DNS propagation (can take a few minutes)

3. Run the automated setup:
   ```bash
   sudo /opt/CasettaFit/app/setup_ssl_auto.sh
   ```

**Manual Let's Encrypt Setup for Any Domain:**

```bash
sudo /opt/CasettaFit/app/setup_ssl.sh
# Select option 1 (Let's Encrypt)
# Enter your domain name
# Optionally provide email for notifications
```

### Let's Encrypt Features:
- ✓ Free SSL certificate
- ✓ Trusted by all browsers
- ✓ Auto-renewal every 90 days
- ✓ Automatic HTTP to HTTPS redirect

### Checking Certificate Status:
```bash
sudo certbot certificates
```

### Testing Auto-Renewal:
```bash
sudo certbot renew --dry-run
```

## Option 2: Self-Signed Certificate

Use for development, testing, or internal networks. Browsers will show security warnings.

```bash
sudo /opt/CasettaFit/app/setup_ssl.sh
# Select option 2 (Self-Signed)
# Enter your domain/hostname
```

The script will:
- Generate a self-signed certificate valid for 365 days
- Store in `/etc/nginx/ssl/`
- Configure NGINX with HTTPS

**Note:** You'll need to accept the security warning in your browser.

## Option 3: Custom Certificate Upload

Use if you already have certificates from another provider.

```bash
sudo /opt/CasettaFit/app/setup_ssl.sh
# Select option 3 (Upload Custom)
# Enter your domain name
# Provide paths to:
#   - Certificate file (.crt or .pem)
#   - Private key file (.key)
#   - CA bundle/chain file (optional)
```

### Certificate Requirements:
- Valid SSL certificate for your domain
- Matching private key
- Optional: CA bundle/intermediate certificates

## Current Server Configuration

**Server IP:** 143.244.184.105  
**Domain:** fit.casettacloud.com  
**DNS Status:** Currently points to 143.244.210.65 (needs update)

### To Set Up SSL for This Server:

1. Update DNS A record to: `143.244.184.105`
2. Wait for DNS propagation (5-15 minutes)
3. Run: `sudo /opt/CasettaFit/app/setup_ssl_auto.sh`

## Troubleshooting

### Let's Encrypt fails with "DNS problem"
- Verify DNS is correctly configured
- Wait for DNS propagation (can take up to 48 hours, usually 5-15 minutes)
- Ensure no firewall blocks ports 80/443

### Certificate renewal fails
```bash
# Check certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Manually renew
sudo certbot renew --force-renewal
```

### NGINX fails to start
```bash
# Test configuration
sudo nginx -t

# Check for port conflicts
sudo netstat -tlnp | grep -E ':(80|443)'
```

## Post-Setup

After successful SSL setup:

1. Access your site: `https://fit.casettacloud.com`
2. Verify HTTPS is working (green padlock in browser)
3. Test HTTP redirect: `http://fit.casettacloud.com` should redirect to HTTPS

## Security Best Practices

- ✓ HTTPS redirect enabled automatically
- ✓ HSTS header set (Strict-Transport-Security)
- ✓ Modern TLS protocols only (TLSv1.2, TLSv1.3)
- ✓ Strong cipher suites configured
- ✓ Security headers enabled

## Certificate Management

### Let's Encrypt Auto-Renewal
Certificates renew automatically via systemd timer:
```bash
# Check renewal timer status
sudo systemctl status certbot.timer

# View scheduled renewals
sudo certbot certificates
```

### Manual Certificate Renewal
```bash
# Dry run (test without actually renewing)
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

## Scripts Available

1. **setup_ssl.sh** - Interactive SSL setup with all options
2. **setup_ssl_auto.sh** - Automated Let's Encrypt for fit.casettacloud.com

Both scripts are located in `/opt/CasettaFit/app/`
