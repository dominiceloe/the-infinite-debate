# Production Deployment Guide

**Project:** The Infinite Debate
**Last Updated:** October 20, 2025
**Target Environment:** AWS Lightsail (or similar VPS)

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Server Provisioning](#server-provisioning)
3. [Initial Server Setup](#initial-server-setup)
4. [Application Deployment](#application-deployment)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Database Configuration](#database-configuration)
7. [Environment Variables](#environment-variables)
8. [First Deployment](#first-deployment)
9. [Post-Deployment Verification](#post-deployment-verification)
10. [Monitoring Setup](#monitoring-setup)
11. [Backup Configuration](#backup-configuration)
12. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
13. [DNS Configuration](#dns-configuration)
14. [Rollback Procedures](#rollback-procedures)
15. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Required Accounts & Services

- [ ] **Domain Name:** Register domain (e.g., theinfinitedebate.com via ICDSoft)
- [ ] **Server:** AWS Lightsail account or similar VPS provider
- [ ] **Vercel:** Account for frontend hosting
- [ ] **Stripe:** Live API keys (not test keys)
- [ ] **Anthropic:** API key with sufficient credits
- [ ] **Sentry:** Account for error tracking (optional but recommended)
- [ ] **GitHub:** Repository with latest code

### Local Preparation

```bash
# 1. Ensure all tests pass
cd backend
docker compose exec web pytest --cov
cd ../frontend
npm test -- --run

# 2. Run production validation (will fail on some checks, that's OK locally)
cd backend
bash scripts/validate-production.sh

# 3. Commit all changes
git add .
git commit -m "chore: prepare for production deployment"
git push origin main

# 4. Create production branch (optional but recommended)
git checkout -b production
git push origin production
```

---

## Server Provisioning

### AWS Lightsail Setup

**Recommended Instance:**
- **Size:** 2 vCPUs, 4 GB RAM, 80 GB SSD ($20/month)
- **OS:** Ubuntu 22.04 LTS
- **Region:** Choose closest to target audience (e.g., us-east-1)
- **Firewall:** Open ports 22, 80, 443

**Steps:**

1. **Create Instance:**
   ```
   AWS Console → Lightsail → Create Instance
   - Platform: Linux/Unix
   - Blueprint: OS Only → Ubuntu 22.04 LTS
   - Instance Plan: $20/month (2GB RAM minimum)
   - Instance Name: debates-production
   ```

2. **Assign Static IP:**
   ```
   Networking Tab → Create Static IP
   - Name: debates-static-ip
   - Attach to: debates-production
   - Note the IP address (e.g., 54.123.45.67)
   ```

3. **Configure Firewall:**
   ```
   Networking Tab → IPv4 Firewall
   - SSH (22) - Your IP only
   - HTTP (80) - All IPs
   - HTTPS (443) - All IPs
   - Custom (8001) - Remove (backend should not be public)
   ```

4. **Download SSH Key:**
   ```
   Account → SSH Keys → Download
   - Save as: ~/.ssh/debates-lightsail.pem
   - chmod 400 ~/.ssh/debates-lightsail.pem
   ```

---

## Initial Server Setup

### SSH Into Server

```bash
# Add to ~/.ssh/config for easy access
cat >> ~/.ssh/config <<EOF
Host debates-prod
    HostName 54.123.45.67
    User ubuntu
    IdentityFile ~/.ssh/debates-lightsail.pem
EOF

# Connect
ssh debates-prod
```

### System Updates

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release
```

### Install Docker

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Verify installation
docker --version
docker compose version

# Log out and back in for group changes to take effect
exit
ssh debates-prod
```

### Configure Firewall (UFW)

```bash
# Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Verify
sudo ufw status
```

### Create Application Directory

```bash
# Create app directory
sudo mkdir -p /opt/the-infinite-debate
sudo chown ubuntu:ubuntu /opt/the-infinite-debate
cd /opt/the-infinite-debate
```

---

## Application Deployment

### Clone Repository

```bash
cd /opt/the-infinite-debate

# Clone from GitHub (use SSH key or HTTPS)
git clone https://github.com/yourusername/philosophical-debates.git .

# Or if using production branch
git clone -b production https://github.com/yourusername/philosophical-debates.git .

# Verify
ls -la
```

### Create Production Environment File

```bash
cd /opt/the-infinite-debate/backend

# Create .env file
cat > .env <<EOF
# Django Settings
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=api.theinfinitedebate.com,theinfinitedebate.com

# Database
DB_NAME=philosophical_debates
DB_USER=debatesuser
DB_PASSWORD=$(openssl rand -base64 32)
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Anthropic API
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Stripe (LIVE KEYS!)
STRIPE_SECRET_KEY=sk_live_your-live-key-here
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret-here
STRIPE_STUDENT_PRICE_ID=price_your-student-price-id
STRIPE_SCHOLAR_PRICE_ID=price_your-scholar-price-id

# CORS (Frontend URL)
CORS_ALLOWED_ORIGINS=https://theinfinitedebate.com

# Sentry (Optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENABLED=True

# Email (Optional - for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Flower (Celery monitoring)
FLOWER_USER=admin
FLOWER_PASSWORD=$(openssl rand -base64 16)

# Security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
EOF

# Secure the file
chmod 600 .env

# IMPORTANT: Edit the file and replace placeholder values
nano .env
```

**⚠️ CRITICAL:** Replace these placeholder values:
- `ANTHROPIC_API_KEY` - Your real Anthropic API key
- `STRIPE_SECRET_KEY` - Stripe LIVE key (starts with `sk_live_`)
- `STRIPE_WEBHOOK_SECRET` - From Stripe dashboard webhooks
- `STRIPE_STUDENT_PRICE_ID` - Starter tier price ID
- `STRIPE_SCHOLAR_PRICE_ID` - Pro tier price ID
- `SENTRY_DSN` - If using Sentry for error tracking
- Email settings - If using email notifications

---

## SSL Certificate Setup

### Using Let's Encrypt with Certbot

```bash
cd /opt/the-infinite-debate/backend

# Create certbot directories
mkdir -p certbot_conf certbot_www

# Start nginx temporarily (without SSL) to get certificate
docker compose -f docker-compose.yml up -d nginx

# Wait for nginx to start
sleep 10

# Get SSL certificate
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d theinfinitedebate.com \
    -d www.theinfinitedebate.com \
    -d api.theinfinitedebate.com

# Stop temporary nginx
docker compose down

# Verify certificates
ls -la certbot_conf/live/theinfinitedebate.com/
```

**Expected Files:**
- `cert.pem` - SSL certificate
- `chain.pem` - Certificate chain
- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key

### Update Nginx Configuration for SSL

```bash
# Edit nginx.conf to enable SSL (if not already configured)
nano nginx.conf
```

Ensure nginx.conf includes:
```nginx
server {
    listen 443 ssl;
    server_name api.theinfinitedebate.com;

    ssl_certificate /etc/letsencrypt/live/theinfinitedebate.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/theinfinitedebate.com/privkey.pem;

    # ... rest of SSL config
}
```

---

## Database Configuration

### Initialize Database

```bash
cd /opt/the-infinite-debate/backend

# Start database only
docker compose -f docker-compose.yml up -d db redis

# Wait for database to be ready
sleep 10

# Verify database is healthy
docker compose exec db pg_isready -U debatesuser
```

### Run Migrations

```bash
# Build and start web container
docker compose -f docker-compose.yml -f docker-compose.prod.yml build web

docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py migrate

# Verify migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py showmigrations
```

### Load Fixtures

```bash
# Load personas (CRITICAL - database starts empty!)
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py load_personas

# Verify personas loaded
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py shell -c "
from personas.models import Persona
print(f'Loaded {Persona.objects.count()} personas')
"

# Load primary texts (if you have fixtures)
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py load_texts
```

### Create Superuser

```bash
# Create admin account
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py createsuperuser

# Follow prompts:
# Email: admin@theinfinitedebate.com
# Password: [secure password]
```

---

## Environment Variables

### Verification

```bash
cd /opt/the-infinite-debate/backend

# Run validation script
bash scripts/validate-production.sh
```

**Fix any errors before proceeding!**

Common issues:
- `DEBUG=True` - Must be `False`
- Test Stripe keys - Must use live keys (`sk_live_`)
- Missing API keys
- Incorrect ALLOWED_HOSTS

---

## First Deployment

### Build and Start All Services

```bash
cd /opt/the-infinite-debate/backend

# Build all images (this takes 5-10 minutes)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify all services are running
docker compose ps
```

**Expected Output:**
```
NAME                 STATUS    PORTS
debates_postgres     Up        5432/tcp
debates_redis        Up        6379/tcp
debates_web          Up        8000/tcp
debates_celery       Up        -
debates_celery_beat  Up        -
debates_flower       Up        -
debates_nginx        Up        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
debates_certbot      Up        -
```

### Collect Static Files

```bash
# Django collectstatic (should happen automatically, but verify)
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Post-Deployment Verification

### Health Checks

```bash
# Backend health check (from server)
curl http://localhost/health/

# Expected: {"status": "healthy", "database": "ok", "redis": "ok"}

# External health check (from your local machine)
curl https://api.theinfinitedebate.com/health/

# Django admin access
curl -I https://api.theinfinitedebate.com/admin/
# Expected: HTTP/2 200 or 302 (redirect to login)
```

### Test API Endpoints

```bash
# List personas
curl https://api.theinfinitedebate.com/api/personas/ | jq '.results | length'
# Expected: 196

# Get specific persona
curl https://api.theinfinitedebate.com/api/personas/socrates/ | jq '.name'
# Expected: "Socrates"

# Register test user
curl -X POST https://api.theinfinitedebate.com/api/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }'

# Expected: User created with trial subscription
```

### Check Logs

```bash
# View all logs
docker compose logs

# Web logs only
docker compose logs web

# Celery logs
docker compose logs celery

# Follow logs in real-time
docker compose logs -f web celery
```

### Monitor Resource Usage

```bash
# Server resources
htop

# Docker stats
docker stats

# Disk usage
df -h

# Database size
docker compose exec db psql -U debatesuser -d philosophical_debates -c "
    SELECT pg_size_pretty(pg_database_size('philosophical_debates'));
"
```

---

## Monitoring Setup

### Sentry Error Tracking

1. **Create Sentry Project:**
   - Go to https://sentry.io
   - Create new project (Django)
   - Copy DSN

2. **Add to .env:**
   ```bash
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   SENTRY_ENABLED=True
   ```

3. **Restart services:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml restart web celery
   ```

4. **Test Sentry:**
   ```bash
   # Trigger test error
   docker compose exec web python manage.py shell -c "
   from django.core.exceptions import ValidationError
   raise ValidationError('Sentry test error')
   "
   ```

   Check Sentry dashboard for error.

### Flower (Celery Monitoring)

Flower is running but not publicly exposed (security).

**Access via SSH tunnel:**
```bash
# From local machine
ssh -L 5555:localhost:5555 debates-prod

# Open browser: http://localhost:5555
# Login: admin / [password from .env]
```

### Log Monitoring

**Set up log rotation:**
```bash
# View Docker logs size
docker compose logs --tail=0 | wc -l

# Docker handles log rotation automatically, but verify settings:
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Backup Configuration

### Set Up Automated Backups

```bash
cd /opt/the-infinite-debate/backend

# Test backup script
bash scripts/backup-database.sh

# Verify backup created
ls -lh backups/

# Set up cron job for daily backups
crontab -e
```

Add to crontab:
```cron
# Daily database backup at 2 AM
0 2 * * * cd /opt/the-infinite-debate/backend && bash scripts/backup-database.sh --quiet

# Monthly archive on 1st of month at 3 AM
0 3 1 * * cd /opt/the-infinite-debate/backend && bash scripts/backup-database.sh --monthly --quiet

# Weekly cleanup of old backups (keep 30 days)
0 4 * * 0 find /opt/the-infinite-debate/backend/backups -name "debates_*.sql.gz" -mtime +30 -delete
```

### Test Backup/Restore

```bash
# Create test backup
bash scripts/backup-database.sh --verify

# Test restore (with confirmation prompt)
bash scripts/restore-database.sh backups/debates_YYYYMMDD_HHMMSS.sql.gz

# Type 'yes' when prompted
```

### Optional: S3 Backup Upload

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region

# Test S3 upload
bash scripts/backup-database.sh --s3-bucket your-backup-bucket

# Add to cron for automated S3 backups
0 2 * * * cd /opt/the-infinite-debate/backend && bash scripts/backup-database.sh --s3-bucket your-backup-bucket --quiet
```

---

## Frontend Deployment (Vercel)

### Prepare Frontend Environment

**Create `frontend/.env.production`:**
```bash
NEXT_PUBLIC_API_URL=https://api.theinfinitedebate.com/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your-live-publishable-key
```

### Deploy to Vercel

**Option 1: Vercel CLI**
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy production
cd /path/to/frontend
vercel --prod
```

**Option 2: GitHub Integration (Recommended)**

1. **Connect GitHub:**
   - Go to https://vercel.com/new
   - Import Git Repository
   - Select your repository
   - Framework: Next.js (auto-detected)
   - Root Directory: `frontend`

2. **Configure Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL = https://api.theinfinitedebate.com/api
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY = pk_live_your_key
   ```

3. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Vercel provides preview URL

4. **Add Custom Domain:**
   - Project Settings → Domains
   - Add `theinfinitedebate.com` and `www.theinfinitedebate.com`
   - Follow DNS instructions

### Verify Frontend Deployment

```bash
# Test frontend (from local machine)
curl https://theinfinitedebate.com

# Test API connection from frontend
# Open browser: https://theinfinitedebate.com
# Register account
# Create debate
# Verify it works end-to-end
```

---

## DNS Configuration

### Update DNS Records

**At your DNS provider (ICDSoft):**

| Type  | Name | Value                | TTL  |
|-------|------|----------------------|------|
| A     | @    | 54.123.45.67 (backend IP) | 3600 |
| A     | api  | 54.123.45.67         | 3600 |
| CNAME | www  | theinfinitedebate.com    | 3600 |

**For Vercel frontend:**
| Type  | Name | Value                | TTL  |
|-------|------|----------------------|------|
| CNAME | @    | cname.vercel-dns.com | 3600 |
| CNAME | www  | cname.vercel-dns.com | 3600 |

**Note:** If using Vercel for frontend, follow their exact DNS instructions (they'll provide specific CNAME values).

### Verify DNS Propagation

```bash
# Check DNS (may take 5-60 minutes)
nslookup theinfinitedebate.com
nslookup api.theinfinitedebate.com

# Or use online tool: https://www.whatsmydns.net
```

---

## Rollback Procedures

### Rollback Docker Deployment

```bash
cd /opt/the-infinite-debate/backend

# List all images
docker images

# Stop current containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Restore from previous image
docker tag philosophical-debates_web:previous philosophical-debates_web:latest

# Restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Rollback Database

```bash
# List backups
ls -lh backups/

# Restore from specific backup
bash scripts/restore-database.sh backups/debates_20251020_020000.sql.gz

# Verify restoration
docker compose exec web python manage.py shell -c "
from debates.models import Debate
print(f'Debates: {Debate.objects.count()}')
"
```

### Rollback Code

```bash
cd /opt/the-infinite-debate

# View recent commits
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>

# Rebuild and deploy
cd backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Common Issues

**1. 502 Bad Gateway**
```bash
# Check if web container is running
docker compose ps web

# Check web container logs
docker compose logs web

# Restart web container
docker compose restart web
```

**2. Database Connection Errors**
```bash
# Check database is running
docker compose ps db

# Test connection
docker compose exec db pg_isready -U debatesuser

# Check credentials in .env
cat .env | grep DB_
```

**3. Celery Tasks Not Processing**
```bash
# Check Celery worker status
docker compose ps celery

# View Celery logs
docker compose logs celery

# Restart Celery
docker compose restart celery

# Check Redis connection
docker compose exec redis redis-cli ping
```

**4. SSL Certificate Issues**
```bash
# Verify certificate files exist
ls -la certbot_conf/live/theinfinitedebate.com/

# Renew certificate manually
docker compose run --rm certbot renew

# Check nginx SSL config
docker compose exec nginx nginx -t

# Restart nginx
docker compose restart nginx
```

**5. Out of Memory**
```bash
# Check memory usage
free -h

# Check Docker stats
docker stats

# Reduce Gunicorn workers (edit docker-compose.prod.yml)
# Change --workers 4 to --workers 2

# Restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**6. Disk Space Full**
```bash
# Check disk usage
df -h

# Clean old Docker images
docker system prune -a

# Clean old backups (keep last 30 days)
find backups/ -name "debates_*.sql.gz" -mtime +30 -delete

# Clean old logs
docker compose logs --tail=0 > /dev/null
```

### Debug Mode (Emergency Only)

**⚠️ NEVER leave debug mode enabled in production!**

```bash
# Temporarily enable debug (for emergency troubleshooting)
nano .env
# Change DEBUG=False to DEBUG=True

# Restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart web

# View detailed error pages
curl https://api.theinfinitedebate.com/api/personas/

# IMMEDIATELY disable debug after troubleshooting
nano .env
# Change DEBUG=True back to DEBUG=False

# Restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart web
```

### Getting Help

**Check logs first:**
```bash
# All logs
docker compose logs --tail=100

# Specific service
docker compose logs web --tail=50

# Follow logs in real-time
docker compose logs -f web celery
```

**Health checks:**
```bash
# Run validation
bash scripts/validate-production.sh

# Check health endpoint
curl http://localhost/health/

# Database migrations status
docker compose exec web python manage.py showmigrations
```

---

## Maintenance Tasks

### Regular Maintenance Schedule

**Daily (Automated via Cron):**
- [ ] Database backup (2 AM)
- [ ] Log rotation (automatic)

**Weekly:**
- [ ] Check disk space: `df -h`
- [ ] Review error logs: `docker compose logs --tail=100 | grep ERROR`
- [ ] Check backup integrity: `ls -lh backups/`

**Monthly:**
- [ ] Review Sentry errors
- [ ] Update dependencies (security patches)
- [ ] Review Stripe billing/usage
- [ ] Test backup restore procedure
- [ ] SSL certificate renewal (automatic, but verify)
- [ ] Database vacuum: `docker compose exec db vacuumdb -U debatesuser -d philosophical_debates -v`

**Quarterly:**
- [ ] Full disaster recovery test
- [ ] Security audit
- [ ] Performance optimization review
- [ ] User feedback review and improvements

### Update Deployment

```bash
cd /opt/the-infinite-debate

# Pull latest code
git pull origin production

# Rebuild containers
cd backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Run new migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm web python manage.py migrate

# Restart services (zero-downtime)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost/health/
```

---

## Success Criteria

### Deployment Complete Checklist

- [ ] Server provisioned and secured
- [ ] SSL certificates obtained and configured
- [ ] Database initialized with migrations
- [ ] Personas loaded (196 personas)
- [ ] Admin user created
- [ ] All services running (`docker compose ps` shows all Up)
- [ ] Health check returns OK: `curl https://api.theinfinitedebate.com/health/`
- [ ] Frontend deployed to Vercel
- [ ] DNS configured and propagated
- [ ] Can register user account via frontend
- [ ] Can create and view debate via frontend
- [ ] Stripe webhooks configured and tested
- [ ] Automated backups configured
- [ ] Monitoring (Sentry) configured
- [ ] SSL grade A+ (test at https://www.ssllabs.com/ssltest/)

### Final Verification

**Full end-to-end test:**
1. Visit https://theinfinitedebate.com
2. Register new account (should get trial subscription)
3. Browse personas
4. Create debate (2-3 participants, simple topic)
5. Watch debate generate in theater mode
6. Verify citations appear
7. Export debate as PDF
8. Upgrade to paid tier (Stripe test)
9. Create another debate (verify credits deducted)
10. Logout and login again (verify auth works)

**If all steps work:** 🎉 **Deployment successful!**

---

## Support & Documentation

- **Architecture:** See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Development:** See [QUICKSTART.md](./QUICKSTART.md)
- **Implementation Plan:** See [NEXT_STEPS.md](./NEXT_STEPS.md)
- **Status:** See [STATUS.md](./STATUS.md)

**Emergency Contacts:**
- Server issues: Check server provider support
- Payment issues: Stripe dashboard → Support
- SSL issues: Let's Encrypt community forum
- Application issues: Check Sentry errors first

---

**Last Updated:** October 20, 2025
**Next Review:** After first deployment completion
