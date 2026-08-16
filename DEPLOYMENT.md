# Production Deployment Guide

## Free Deployment Options

### 1. **Render.com** (Recommended - Free Tier)
- **Best for**: Production-ready Python apps
- **Free Tier**: 512MB RAM, 0.1 CPU
- **Database**: Free PostgreSQL (1GB)
- **SSL**: Automatic HTTPS
- **Pros**: Easy setup, automatic SSL, good for Flask
- **Cons**: 512MB RAM limit

**How to Deploy on Render:**
1. Create a Render account at [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT`
6. Add Environment Variables:
   - `SECRET_KEY`: Generate a strong random key
   - `UPI_ID`: Your UPI ID
   - `PAYEE_NAME`: Your business name
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: Provided by Render PostgreSQL
7. Deploy!

### 2. **PythonAnywhere** (Free Tier)
- **Best for**: Python-specific hosting
- **Free Tier**: Limited but functional
- **Database**: SQLite (free) or upgrade for PostgreSQL
- **SSL**: Available on paid tier
- **Pros**: Built for Python, easy setup
- **Cons**: Limited free tier, no SSL on free

**How to Deploy on PythonAnywhere:**
1. Create account at [pythonanywhere.com](https://pythonanywhere.com)
2. Create a new Web App
3. Upload your files via Git or web interface
4. Configure WSGI file
5. Add environment variables
6. Install requirements: `pip install -r requirements.txt`
7. Set up worker: `gunicorn app:app`

### 3. **Railway.app** (Free Tier)
- **Best for**: Modern deployment with databases
- **Free Tier**: $5 credit/month
- **Database**: Free PostgreSQL
- **SSL**: Automatic HTTPS
- **Pros**: Great UI, includes database
- **Cons**: Free tier has limits

**How to Deploy on Railway:**
1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Railway will detect Flask automatically
4. Add environment variables
5. Deploy!

### 4. **Vercel** (Free Tier)
- **Best for**: Frontend-focused, but supports Python
- **Free Tier**: Generous limits
- **Database**: Can add external databases
- **SSL**: Automatic HTTPS
- **Pros**: Fast deployment, great CDN
- **Cons**: Python support is newer

**How to Deploy on Vercel:**
1. Create account at [vercel.com](https://vercel.com)
2. Install Vercel CLI: `npm install -g vercel`
3. Run: `vercel` in your project directory
4. Configure as Python app
5. Add environment variables

## Pre-Deployment Checklist

### 1. Environment Variables
```bash
SECRET_KEY=your-strong-random-secret-key-here
UPI_ID=yourupi@upi
PAYEE_NAME=Your Business Name
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 2. Security
- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS (automatic on most platforms)
- [ ] Set up proper database permissions
- [ ] Remove test files

### 3. Database
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Set up database backups
- [ ] Configure proper connection pooling

### 4. Performance
- [ ] Use production WSGI server (Gunicorn)
- [ ] Configure appropriate number of workers
- [ ] Enable static file caching
- [ ] Consider CDN for static assets

## Quick Start with Render (Recommended)

1. **Prepare your code:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repo
   - Use these settings:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT`

3. **Add Environment Variables:**
   - `SECRET_KEY`: Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `UPI_ID`: Your UPI ID
   - `PAYEE_NAME`: Your business name
   - `FLASK_ENV`: `production`

4. **Add PostgreSQL Database:**
   - In Render, create a new PostgreSQL database
   - Copy the DATABASE_URL to your web service environment variables

5. **Deploy!**
   - Render will automatically build and deploy
   - Your app will be available at `https://your-app.onrender.com`

## Post-Deployment Steps

1. **Access Admin Panel:**
   - Visit `https://your-app.onrender.com/admin/login`
   - Login with default credentials
   - **IMPORTANT**: Change admin password immediately

2. **Configure Products:**
   - Add your actual products
   - Set correct prices
   - Update descriptions

3. **Test Payment Flow:**
   - Place a test order
   - Verify UPI QR code generation
   - Test payment confirmation

4. **Set Up Monitoring:**
   - Monitor app logs in Render dashboard
   - Set up error tracking (optional)
   - Check database usage

## Troubleshooting

### Common Issues:

**App won't start:**
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure DATABASE_URL is correct

**Database connection errors:**
- Verify DATABASE_URL format
- Check database is running
- Ensure proper permissions

**Static files not loading:**
- Clear browser cache
- Check file permissions
- Verify static file configuration

**Login issues:**
- Clear browser cookies
- Verify SECRET_KEY is set
- Check database tables are created

## Cost Comparison

| Platform | Free Tier | RAM | CPU | Database | SSL |
|----------|-----------|-----|-----|----------|-----|
| Render | Yes | 512MB | 0.1 | Free PostgreSQL | Yes |
| PythonAnywhere | Yes | Limited | Limited | SQLite | Paid |
| Railway | $5/mo credit | 512MB | 0.5 | Free PostgreSQL | Yes |
| Vercel | Yes | 1024MB | 0.6 | External | Yes |

## Recommendation

**For production use, I recommend Render.com** because:
- ✅ Truly free tier with generous limits
- ✅ Automatic SSL/HTTPS
- ✅ Free PostgreSQL database
- ✅ Easy Flask deployment
- ✅ Good performance for small apps
- ✅ Simple dashboard and monitoring

Your order payment app should work well on Render's free tier for moderate traffic.