# 🚀 COSMIC Data Fusion - Deployment Guide

## Table of Contents
1. [Quick Start Options](#quick-start-options)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Methods](#deployment-methods)
4. [Production Configuration](#production-configuration)
5. [Post-Deployment Steps](#post-deployment-steps)

---

## Quick Start Options

### ⚡ Fastest: Railway.app (2 minutes)
**Best for:** Hackathons, quick demos, MVPs  
**Cost:** $5-20/month, includes PostgreSQL

1. **Sign up:** [railway.app](https://railway.app)
2. **New Project** → Deploy from GitHub
3. **Add PostgreSQL** → Enable PostGIS extension
4. **Set environment variables** (see below)
5. **Deploy** → Railway handles everything automatically

### 🐳 Most Flexible: Docker Compose (Self-Hosted)
**Best for:** Full control, cost optimization  
**Cost:** VPS from $5/month (DigitalOcean, Hetzner)

### ☁️ Enterprise: AWS/GCP/Azure
**Best for:** Scalability, compliance requirements  
**Cost:** Variable, $50-500+/month

---

## Pre-Deployment Checklist

### ✅ 1. Build Frontend for Production

```bash
cd frontend
npm install
npm run build
```

This creates a `frontend/dist` folder with optimized static files.

### ✅ 2. Update Dockerfile to Serve Frontend

Add to your Dockerfile:

```dockerfile
# Copy frontend build
COPY frontend/dist ./frontend/dist
```

Or serve frontend separately on Netlify/Vercel (free).

### ✅ 3. Environment Variables

Create `.env.production`:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/cosmic_data
POSTGRES_PASSWORD=<strong_password>

# Application
APP_ENV=production
DEBUG=False
COSMIC_API_PORT=8000

# Security (generate new secrets!)
SECRET_KEY=<generate_with: openssl rand -hex 32>
JWT_SECRET_KEY=<generate_with: openssl rand -hex 32>

# CORS (update with your frontend domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional
MAX_UPLOAD_SIZE_MB=500
MAX_INGEST_RECORDS=50000
```

### ✅ 4. Security Hardening

Update `app/main.py` CORS settings:

```python
# Replace * with your actual domain
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### ✅ 5. Database Preparation

- Enable PostGIS extension
- Run migrations: `alembic upgrade head`
- Consider backup strategy

---

## Deployment Methods

## 1️⃣ Railway.app Deployment (Recommended for Speed)

### Step-by-Step:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   ```
   Dashboard → New Project → Deploy from GitHub Repo
   ```

3. **Add PostgreSQL Database**
   ```
   + New → Database → PostgreSQL
   ```
   
4. **Enable PostGIS**
   ```
   Database → Connect → Run:
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS postgis_topology;
   ```

5. **Configure Backend Service**
   - Railway auto-detects your Dockerfile
   - Add environment variables:
     - `DATABASE_URL` → Copy from PostgreSQL service
     - `APP_ENV` → `production`
     - `SECRET_KEY` → Generate new
     - `JWT_SECRET_KEY` → Generate new

6. **Run Migrations**
   ```
   Service → Settings → One-off Command:
   alembic upgrade head
   ```

7. **Generate Domain**
   ```
   Settings → Generate Domain
   ```

### Estimated Time: 5 minutes  
### Cost: $5-20/month

---

## 2️⃣ Docker Compose on VPS (Best for Control)

### Recommended VPS Providers:
- **DigitalOcean**: $6/month Droplet
- **Hetzner**: €4.15/month
- **Linode**: $5/month
- **Vultr**: $6/month

### Step-by-Step:

1. **Provision VPS**
   - Ubuntu 22.04 LTS
   - Minimum: 2GB RAM, 1 vCPU, 50GB storage
   - Recommended: 4GB RAM, 2 vCPU

2. **Install Docker**
   ```bash
   # Connect via SSH
   ssh root@your-server-ip
   
   # Install Docker & Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/cosmic-data-fusion.git
   cd cosmic-data-fusion
   ```

4. **Configure Environment**
   ```bash
   # Create .env file
   nano .env
   
   # Add production variables
   POSTGRES_PASSWORD=your_secure_password
   APP_ENV=production
   DEBUG=False
   ```

5. **Build Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

6. **Update docker-compose.yml for Production**
   ```yaml
   services:
     app:
       command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
       environment:
         DEBUG: False
       restart: always
   ```

7. **Deploy**
   ```bash
   docker-compose up -d
   ```

8. **Run Migrations**
   ```bash
   docker exec cosmic-data-fusion-app alembic upgrade head
   ```

9. **Setup Nginx Reverse Proxy (Optional but Recommended)**
   ```bash
   sudo apt install nginx
   sudo nano /etc/nginx/sites-available/cosmic
   ```
   
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/cosmic /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

10. **Setup SSL with Certbot**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomain.com
    ```

### Estimated Time: 30 minutes  
### Cost: $5-12/month

---

## 3️⃣ Render.com Deployment

### Step-by-Step:

1. **Sign Up**: [render.com](https://render.com)

2. **Create PostgreSQL Database**
   ```
   New → PostgreSQL → Name: cosmic-db
   ```
   
   After creation, connect and enable PostGIS:
   ```sql
   CREATE EXTENSION postgis;
   CREATE EXTENSION postgis_topology;
   ```

3. **Create Web Service**
   ```
   New → Web Service → Connect GitHub Repo
   ```
   
   Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

4. **Add Environment Variables**
   - `DATABASE_URL` → Copy from PostgreSQL database
   - `APP_ENV` → `production`
   - `SECRET_KEY` → Generate new
   - `PORT` → Auto-set by Render

5. **Run Migrations** (via Shell)
   ```bash
   alembic upgrade head
   ```

### Estimated Time: 10 minutes  
### Cost: Free tier available, then $7/month+

---

## 4️⃣ Fly.io Deployment

### Step-by-Step:

1. **Install Flyctl**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Create Postgres Database**
   ```bash
   fly postgres create --name cosmic-db --region ord
   ```

4. **Initialize App**
   ```bash
   fly launch
   # Follow prompts, select region
   ```

5. **Attach Database**
   ```bash
   fly postgres attach cosmic-db
   ```

6. **Enable PostGIS**
   ```bash
   fly postgres connect -a cosmic-db
   # In psql:
   CREATE EXTENSION postgis;
   CREATE EXTENSION postgis_topology;
   ```

7. **Set Environment Variables**
   ```bash
   fly secrets set APP_ENV=production
   fly secrets set SECRET_KEY=$(openssl rand -hex 32)
   ```

8. **Deploy**
   ```bash
   fly deploy
   ```

9. **Run Migrations**
   ```bash
   fly ssh console
   alembic upgrade head
   ```

### Estimated Time: 15 minutes  
### Cost: $3-15/month (excellent free tier)

---

## 5️⃣ AWS Deployment (Enterprise)

### Architecture:
- **ECS Fargate**: Docker container hosting
- **RDS PostgreSQL**: Managed database with PostGIS
- **S3 + CloudFront**: Frontend static files
- **Application Load Balancer**: Traffic distribution
- **Route 53**: DNS management

### High-Level Steps:

1. **RDS PostgreSQL**
   - Create PostgreSQL 15 instance
   - Enable PostGIS in parameter group
   - Configure security groups

2. **ECS Fargate**
   - Create ECR repository
   - Push Docker image
   - Create Task Definition
   - Create Service with ALB

3. **Frontend on S3**
   ```bash
   cd frontend
   npm run build
   aws s3 sync dist/ s3://your-bucket-name
   ```

4. **CloudFront Distribution**
   - Point to S3 bucket
   - Configure caching
   - Add SSL certificate

5. **Environment Variables**
   - Use AWS Systems Manager Parameter Store
   - Reference in Task Definition

### Estimated Time: 2-4 hours  
### Cost: $50-200/month (depends on traffic)

---

## Production Configuration

### Update `app/main.py` for Production:

```python
import os

# CORS - restrict origins
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

# Only allow * in development
if os.getenv("APP_ENV") != "production":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Update Dockerfile for Production:

```dockerfile
# Add frontend build
FROM python:3.13-slim

# ... existing setup ...

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y nodejs npm

# Build frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Copy frontend dist to serve
COPY --from=0 /app/frontend/dist ./frontend/dist

# Serve static files from FastAPI
```

Or deploy frontend separately on:
- **Vercel**: `npx vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **Cloudflare Pages**: `npx wrangler pages deploy frontend/dist`

---

## Post-Deployment Steps

### ✅ 1. Test API Health
```bash
curl https://your-api-domain.com/health
```

### ✅ 2. Run Database Migrations
```bash
# Railway/Render: Use web console
alembic upgrade head

# Docker:
docker exec cosmic-data-fusion-app alembic upgrade head

# Fly.io:
fly ssh console -a your-app
alembic upgrade head
```

### ✅ 3. Load Initial Data (Optional)
```bash
# If you have seed data
python scripts/fetch_real_data.py
```

### ✅ 4. Setup Monitoring

**Backend Monitoring:**
- **Sentry**: Error tracking
- **DataDog**: APM and logs
- **Uptime Robot**: Uptime monitoring (free)

**Database Monitoring:**
- **PgHero**: PostgreSQL insights
- Enable slow query logs

### ✅ 5. Configure Backups

**Railway/Render:** Automatic daily backups

**Self-Hosted:**
```bash
# Daily backup cron job
0 2 * * * docker exec cosmic-postgis pg_dump -U cosmic_user cosmic_data > /backups/backup_$(date +\%F).sql
```

### ✅ 6. Setup Domain & SSL

**Custom Domain:**
- Update DNS records to point to your deployment
- Enable SSL (auto-handled by most platforms)

### ✅ 7. Performance Optimization

```python
# In app/main.py
@app.on_event("startup")
async def startup():
    # Warm up database connections
    # Initialize caching
    pass
```

---

## Environment Variables Reference

### Required:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
APP_ENV=production
```

### Optional:
```bash
DEBUG=False
COSMIC_API_PORT=8000
COSMIC_API_HOST=0.0.0.0
MAX_UPLOAD_SIZE_MB=500
MAX_INGEST_RECORDS=50000
ALLOWED_ORIGINS=https://yourdomain.com
```

### Generate Secrets:
```bash
# On Linux/Mac/WSL
openssl rand -hex 32

# On Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Check PostGIS
psql $DATABASE_URL -c "SELECT PostGIS_version();"
```

### Migration Errors
```bash
# Check current version
alembic current

# Reset to specific version
alembic downgrade <revision>
alembic upgrade head
```

### CORS Errors
- Update `allow_origins` in `app/main.py`
- Ensure frontend URL matches exactly (no trailing slash mismatch)

### Memory Issues
- Increase container memory (Railway: Settings → Resources)
- Reduce `MAX_INGEST_RECORDS` in config

---

## Recommended: Railway Deployment (Quick Start)

For fastest deployment:

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL
railway add --plugin postgresql

# 5. Deploy
railway up

# 6. Run migrations
railway run alembic upgrade head

# 7. Open deployed app
railway open
```

**Time to deploy: ~3 minutes**

---

## Cost Comparison

| Platform | Database | Backend | Frontend | Total/Month |
|----------|----------|---------|----------|-------------|
| Railway | Included | $5+ | $0 | $5-20 |
| Render | $7 | $7 | $0 | $14 |
| Fly.io | $3+ | $3+ | $0 | $6-15 |
| DigitalOcean VPS | Self-hosted | Self-hosted | Self-hosted | $6-12 |
| AWS | $15+ | $30+ | $1+ | $50-200 |
| Vercel/Netlify (Frontend only) | - | - | Free-$20 | - |

---

## Next Steps

1. ✅ Choose deployment platform
2. ✅ Build frontend: `cd frontend && npm run build`
3. ✅ Set environment variables
4. ✅ Deploy backend
5. ✅ Run migrations
6. ✅ Deploy frontend (or serve from backend)
7. ✅ Test API: `curl https://your-api/health`
8. ✅ Setup monitoring
9. ✅ Configure custom domain
10. ✅ Celebrate! 🎉

---

## Support

- **Documentation**: Check API docs at `/docs` endpoint
- **Issues**: Open GitHub issue
- **Community**: Join Discord/Slack

---

**Happy Deploying! 🚀**
