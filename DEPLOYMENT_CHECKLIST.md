# 🚀 Deployment Checklist

## Pre-Deployment (5 minutes)

- [ ] **Build frontend**
  ```bash
  cd frontend
  npm install
  npm run build
  ```

- [ ] **Create .env file**
  ```bash
  cp .env.example .env
  # Edit .env with your values
  ```

- [ ] **Generate secrets**
  ```powershell
  # PowerShell
  [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
  ```

- [ ] **Test locally**
  ```bash
  docker-compose up
  # Visit: http://localhost:8000/docs
  ```

---

## Railway Deployment (Recommended - 5 minutes)

- [ ] Sign up at [railway.app](https://railway.app)
- [ ] New Project → Deploy from GitHub
- [ ] Add PostgreSQL database
- [ ] Enable PostGIS:
  ```sql
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS postgis_topology;
  ```
- [ ] Set environment variables:
  - `DATABASE_URL` (auto-set by PostgreSQL service)
  - `APP_ENV=production`
  - `DEBUG=False`
  - `SECRET_KEY=<generated>`
  - `JWT_SECRET_KEY=<generated>`
- [ ] Generate domain
- [ ] Run migration: Settings → One-off Command: `alembic upgrade head`
- [ ] Test: Visit your-app.railway.app/health

**Cost: $5-20/month** ✅

---

## Docker VPS Deployment (30 minutes)

- [ ] Provision VPS (DigitalOcean, Hetzner, Linode)
  - Minimum: 2GB RAM, 1 CPU, Ubuntu 22.04
- [ ] Install Docker:
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  ```
- [ ] Clone repository
- [ ] Build frontend (see above)
- [ ] Create .env file with production values
- [ ] Deploy:
  ```bash
  chmod +x deploy.sh
  ./deploy.sh production
  ```
- [ ] Setup Nginx + SSL (optional):
  ```bash
  sudo apt install nginx certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  ```

**Cost: $5-12/month** ✅

---

## Render.com Deployment (10 minutes)

- [ ] Sign up at [render.com](https://render.com)
- [ ] Create PostgreSQL database
- [ ] Enable PostGIS in database console
- [ ] Create Web Service from GitHub repo
- [ ] Settings:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables
- [ ] Run migration via Shell: `alembic upgrade head`

**Cost: Free tier → $7/month** ✅

---

## Post-Deployment Verification

- [ ] **API Health Check**
  ```bash
  curl https://your-domain.com/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **Test Database Connection**
  ```bash
  curl https://your-domain.com/analytics/summary
  # Should return data statistics
  ```

- [ ] **Test CORS** (from your frontend domain)
  ```javascript
  fetch('https://your-api.com/health')
  ```

- [ ] **Test File Upload** (via /docs Swagger UI)
  - Try uploading a small test file

- [ ] **Check Migrations**
  ```bash
  # Railway: Shell
  alembic current
  
  # Docker:
  docker exec cosmic-data-fusion-app alembic current
  ```

---

## Production Hardening

- [ ] **Update CORS origins** in `app/main.py`
  ```python
  origins = [
      "https://yourdomain.com",
      "https://www.yourdomain.com"
  ]
  ```

- [ ] **Enable HTTPS**
  - Railway/Render: Automatic
  - VPS: Use Certbot

- [ ] **Setup Backups**
  - Railway: Automatic daily backups
  - VPS: Setup cron job for pg_dump

- [ ] **Configure Monitoring**
  - [ ] Uptime monitoring (UptimeRobot - free)
  - [ ] Error tracking (Sentry)
  - [ ] Logging (Papertrail, Logtail)

- [ ] **Set Resource Limits**
  ```yaml
  # In docker-compose.prod.yml
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
  ```

---

## Optional Enhancements

- [ ] **Custom Domain**
  - Add DNS A/CNAME records
  - Configure SSL certificate

- [ ] **CDN for Frontend**
  - Cloudflare (free)
  - CloudFront (AWS)

- [ ] **Database Connection Pooling**
  - PgBouncer for high-traffic scenarios

- [ ] **Rate Limiting**
  - Already configured in nginx.conf
  - Or use Cloudflare free tier

- [ ] **Caching Layer**
  - Uncomment Redis in docker-compose.yml
  - Implement API response caching

---

## Troubleshooting

### Database Connection Failed
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/dbname

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

### Migration Errors
```bash
# Check migration status
alembic current

# Force reset (⚠️ destroys data)
alembic downgrade base
alembic upgrade head
```

### CORS Errors
- Verify `allow_origins` in `app/main.py` matches your frontend URL exactly
- Check for trailing slash differences

### 502 Bad Gateway
- Check app logs: `docker-compose logs app`
- Verify app is listening on correct port
- Check health endpoint internally: `docker exec cosmic-data-fusion-app curl http://localhost:8000/health`

---

## Deployment Status

| Task | Platform | Status | URL |
|------|----------|--------|-----|
| Backend API | _____ | ⬜ Not started | |
| Database | _____ | ⬜ Not started | |
| Frontend | _____ | ⬜ Not started | |
| Domain | _____ | ⬜ Not started | |
| SSL | _____ | ⬜ Not started | |
| Monitoring | _____ | ⬜ Not started | |

**Legend:** ⬜ Not started | 🟡 In progress | ✅ Complete

---

## Quick Commands Reference

```bash
# Local development
docker-compose up
docker-compose down
docker-compose logs -f app

# Production deployment
./deploy.sh production  # Linux/Mac
.\deploy.ps1 production # Windows

# Database migrations
alembic upgrade head
alembic current
alembic history

# Generate secrets
openssl rand -hex 32  # Linux/Mac
# PowerShell: See above

# Health check
curl http://localhost:8000/health
curl https://your-domain.com/health

# View logs
docker-compose logs -f
docker exec -it cosmic-data-fusion-app sh
```

---

## Need Help?

- 📖 **Detailed Guide**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🐛 **Issues**: Open GitHub issue
- 📧 **Support**: Check documentation in `/docs` endpoint

---

**Ready to launch? Start with Railway for the fastest deployment!** 🚀
