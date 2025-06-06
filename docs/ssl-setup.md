# SSL Certificate Setup Guide

## Custom Domain Setup

1. Configure DNS Records:
   - Add a CNAME record pointing to `minimalwave-blog.azurewebsites.net`
   - Add a TXT record for domain verification

2. Add Custom Domain to Azure App Service:
   ```bash
   az webapp config hostname add --webapp-name minimalwave-blog \
       --resource-group minimalwave-blog-rg \
       --hostname YOUR_DOMAIN_NAME
   ```

## SSL Certificate Options

### Option 1: Free App Service Managed Certificate
```bash
# Once custom domain is configured, create managed certificate
az webapp config ssl create --resource-group minimalwave-blog-rg \
    --name minimalwave-blog \
    --hostname YOUR_DOMAIN_NAME
```

### Option 2: Import Custom SSL Certificate
```bash
# Import existing PFX certificate
az webapp config ssl upload --resource-group minimalwave-blog-rg \
    --name minimalwave-blog \
    --certificate-file YOUR_CERT.pfx \
    --certificate-password YOUR_PASSWORD
```

### Option 3: Let's Encrypt Setup
1. Install certbot on your local machine
2. Generate certificate:
   ```bash
   certbot certonly --manual \
       --preferred-challenges=dns \
       --email admin@yourdomain.com \
       --agree-tos \
       --manual-public-ip-logging-ok \
       -d yourdomain.com
   ```
3. Convert to PFX format:
   ```bash
   openssl pkcs12 -export \
       -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
       -inkey /etc/letsencrypt/live/yourdomain.com/privkey.pem \
       -out certificate.pfx
   ```
4. Upload using Option 2 method

## Bind Certificate to Custom Domain
```bash
# Get certificate thumbprint
az webapp config ssl list --resource-group minimalwave-blog-rg

# Bind SSL certificate
az webapp config ssl bind --resource-group minimalwave-blog-rg \
    --name minimalwave-blog \
    --certificate-thumbprint YOUR_THUMBPRINT \
    --ssl-type SNI
```

## Verify SSL Configuration
1. Check SSL binding:
   ```bash
   az webapp config ssl show --resource-group minimalwave-blog-rg \
       --name minimalwave-blog
   ```

2. Verify HTTPS is enforced in settings:
   - This is already configured in our production.py settings:
   ```python
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   ```

## Renewal Process

### For Managed Certificates
- Azure automatically handles renewal

### For Let's Encrypt
1. Set up renewal automation:
   ```bash
   # Create renewal script
   certbot renew
   # Convert new certificate to PFX
   # Upload new certificate to Azure
   # Update binding
   ```
2. Add to crontab to run monthly:
   ```bash
   0 0 1 * * /path/to/renewal/script
   ```

## Monitoring
SSL certificate expiration is monitored through the Azure Monitor alerts we previously set up.
