# 🚀 Quick Deployment Guide - TL;DR

## Fastest Path to Production (5 minutes)

### Option 1: Railway.app (Recommended)

```bash
# 1. Build frontend
cd frontend && npm install && npm run build && cd ..

# 2. Push to GitHub
git add . && git commit -m "Ready for deployment" && git push

# 3. Go to railway.app → New Project → Deploy from GitHub

# 4. Add PostgreSQL → Enable PostGIS:
CREATE EXTENSION IF NOT EXISTS postgis;

# 5. Set environment variables in Railway dashboard:
APP_ENV=production
SECRET_KEY=<generate: openssl rand -hex 32>
JWT_SECRET_KEY=<generate: openssl rand -hex 32>

# 6. Run migration (Railway Shell):
alembic upgrade head

# Done! 🎉
```

**Cost:** $5-20/month | **Time:** 5 minutes

---

### Option 2: Docker on VPS (Self-hosted)

```bash
# On your VPS (DigitalOcean, Hetzner, etc.)

# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Clone your repo
git clone <your-repo-url>
cd cosmic-data-fusion

# 3. Setup environment
cp .env.example .env
nano .env  # Edit with your values

# 4. Build frontend
cd frontend && npm install && npm run build && cd ..

# 5. Deploy
chmod +x deploy.sh
./deploy.sh production

# Done! 🎉
```

**Cost:** $5-12/month | **Time:** 30 minutes

---

## What You Get

✅ **Backend API** - FastAPI with full documentation  
✅ **Database** - PostgreSQL with PostGIS  
✅ **Frontend** - React/Vite dashboard  
✅ **HTTPS** - Automatic SSL certificates  
✅ **Backups** - Automatic database backups  
✅ **Monitoring** - Health checks and logs  

---

## Essential Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/cosmic_data
SECRET_KEY=<random-32-char-string>
JWT_SECRET_KEY=<random-32-char-string>
APP_ENV=production

# Optional but recommended
ALLOWED_ORIGINS=https://yourdomain.com
DEBUG=False
LOG_LEVEL=INFO
```

**Generate secrets:**
```bash
# Linux/Mac/WSL
openssl rand -hex 32

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## After Deployment

1. **Test API:** `curl https://your-domain.com/health`
2. **Check docs:** Visit `https://your-domain.com/docs`
3. **Run migrations:** `alembic upgrade head`
4. **Setup monitoring:** [uptimerobot.com](https://uptimerobot.com) (free)

---

## Help

- **Full Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Checklist:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Troubleshooting:** See deployment guide Section 5

---

**Ready? Start with Railway for fastest results!** 🚀
