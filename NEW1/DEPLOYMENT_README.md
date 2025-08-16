# 🚀 Jadeed Gadgets - Free Deployment Guide

Your Django e-commerce application is now ready for deployment! Here are three free options to deploy your project.

## 📋 Pre-deployment Checklist

✅ **Files Created for Deployment:**
- `requirements.txt` - Python dependencies
- `build.sh` - Build script for deployment
- `render.yaml` - Render.com configuration
- `Procfile` - Process file for web servers  
- `runtime.txt` - Python version specification
- `.env` - Environment variables (for development)
- `.gitignore` - Files to ignore in git
- Updated `settings.py` - Production-ready settings

## 🌟 Option 1: Render.com (Recommended)

### Step 1: Prepare Your Code
1. Create a GitHub repository:
   - Go to [GitHub.com](https://github.com) and create a new repository
   - Name it `jadeed-gadgets` or similar
   - Don't initialize with README (we already have files)

2. Push your code to GitHub:
   ```bash
   cd NEW1
   git init
   git add .
   git commit -m "Initial commit - Jadeed Gadgets Django App"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/jadeed-gadgets.git
   git push -u origin main
   ```

### Step 2: Deploy to Render
1. Go to [Render.com](https://render.com) and sign up with GitHub
2. Click "New +" → "Web Service"
3. Connect your `jadeed-gadgets` repository
4. Configure the service:
   - **Name**: `jadeed-gadgets`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn jadeedgadgets.wsgi:application`
   - **Instance Type**: `Free`

5. Add Environment Variables:
   - `SECRET_KEY`: Generate a new one at [Django Secret Key Generator](https://djecrety.ir/)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*` (or your render domain)

6. Create a PostgreSQL database:
   - Go to Dashboard → "New +" → "PostgreSQL"
   - Name: `jadeed-gadgets-db`
   - Copy the `DATABASE_URL` and add it as an environment variable

7. Click "Create Web Service"

### Step 3: Post-deployment
1. Your app will build and deploy automatically
2. Run migrations: In the Render dashboard, go to your service and run:
   ```
   python manage.py migrate
   python manage.py createsuperuser
   ```

## 🚂 Option 2: Railway.app

### Step 1: Prepare Code (same as above)
Push your code to GitHub as described in Option 1.

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app) and sign up with GitHub
2. Click "Deploy from GitHub repo"
3. Select your `jadeed-gadgets` repository
4. Railway will automatically detect it's a Django app

### Step 3: Configure
1. Add environment variables in the Variables tab:
   - `SECRET_KEY`: Generate new key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*.up.railway.app`

2. Add PostgreSQL:
   - Go to your project → "New" → "Database" → "Add PostgreSQL"
   - Railway automatically sets `DATABASE_URL`

3. Your app will deploy automatically!

## 🐍 Option 3: PythonAnywhere

### Step 1: Upload Code
1. Create account at [PythonAnywhere.com](https://pythonanywhere.com)
2. Go to "Files" → Upload your project files
3. Open a Bash console

### Step 2: Setup Virtual Environment
```bash
mkvirtualenv jadeed-gadgets --python=python3.10
pip install -r requirements.txt
```

### Step 3: Configure Web App
1. Go to "Web" tab → "Add a new web app"
2. Choose "Manual configuration" → Python 3.10
3. Set source code: `/home/yourusername/NEW1`
4. Set WSGI file: `/home/yourusername/NEW1/jadeedgadgets/wsgi.py`

### Step 4: Configure Static Files
- URL: `/static/`
- Directory: `/home/yourusername/NEW1/staticfiles/`

## 🔧 Environment Variables

For any platform, you'll need these environment variables:

```env
SECRET_KEY=your-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.herokuapp.com,*.render.com
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## 🎯 Testing Your Deployment

After deployment, test these URLs:
- `/` - Home page
- `/admin/` - Django admin (create superuser first)
- Your product pages and recommendation features

## 📞 Support

If you encounter issues:
1. Check the deployment logs in your chosen platform
2. Verify all environment variables are set
3. Ensure your database migrations ran successfully

## 🎉 Success!

Your Jadeed Gadgets e-commerce site should now be live and accessible to the world!

**Popular choice**: I recommend **Render.com** for its simplicity and generous free tier.

---
*Generated for Jadeed Gadgets Django Application*
