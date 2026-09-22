# Railway-Brand-Extractor
SM brand extractor for demos. Built using Railway

Deploy Brand Extractor to Railway
Railway is perfect for this because it supports Chrome/Selenium natively.

Step 1: Prepare Your GitHub Repo
Update your GitHub repo with these files:

Replace:

brand_extractor.py → Use brand_extractor_selenium.py (rename it to brand_extractor.py)
requirements.txt → Use the Railway version (with Selenium)
Add:

Procfile (included)
Update:

streamlit_app.py (already updated to import brand_extractor_selenium)
Then commit and push:

git add -A
git commit -m "Switch to Railway with Selenium support"
git push origin main
Step 2: Deploy to Railway
Go to railway.app
Sign up with GitHub (or sign in)
Click "Create New Project"
Select "Deploy from GitHub repo"
Select your brand-extractor repository
Railway auto-detects it's a Python app
It reads your Procfile and requirements.txt automatically
Click "Deploy" and wait 2-3 minutes
Step 3: Get Your URL
Once deployed:

Go to your Railway project
Click your app
Go to "Deployments"
You'll see a public URL like: https://brand-extractor-prod-xyz.railway.app
Share this URL with your team!
What's Different on Railway
✅ Selenium works - Chrome is installed and available
✅ Accurate colors - Extracts computed CSS styles properly
✅ Better logo detection - Uses browser rendering
✅ No random image grabs - Real DOM inspection
✅ 24/7 uptime - No sleep/restart issues
✅ Only $5-10/month - Auto-scaling pricing

Troubleshooting
Build fails:

Check Railway build logs
Ensure all 3 files are in repo: streamlit_app.py, brand_extractor_selenium.py, Procfile
App crashes:

Railway logs will show the error
Usually missing dependencies - check requirements.txt
Slow performance:

Selenium can be slow on large sites
This is normal - typical extraction takes 10-15 seconds
Files You Need
streamlit_app.py - Web interface (update import line)
brand_extractor_selenium.py - Core extractor with Selenium
requirements.txt - Dependencies (Railway version)
Procfile - Tells Railway how to run the app
Done! Your team can now paste URLs and get accurate results! 🚀
