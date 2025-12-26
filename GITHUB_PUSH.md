# Push to GitHub - Quick Guide

## Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `solboy-telegram-bot` (or any name you want)
3. **Don't** initialize with README, .gitignore, or license
4. Click **Create repository**

## Step 2: Push Your Code

After creating the repo, GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/solboy-telegram-bot.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your GitHub username!**

## Step 3: Connect to Railway

1. Go to Railway: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. Click **+ New** → **GitHub Repo**
3. Select your repository
4. Railway will auto-deploy!

## What Was Changed

✅ **MCAP Filtering**: Alerts with current MCAP > $500k are now skipped
✅ **Duplicate Prevention**: Already implemented - prevents same token+tier alerts within 5 minutes
✅ **API Server Integration**: API server now runs alongside the main monitor (no need to run separately)
✅ **Environment Variables**: All config now uses environment variables for Railway deployment
✅ **Fixed Indentation**: All syntax errors fixed

## Environment Variables Needed in Railway

- `API_ID=25177061`
- `API_HASH=c11ea2f1db2aa742144dfa2a30448408`
- `BOT_TOKEN=8231103146:AAElHbn-WfOfafitmPGnDZ2WeA61HaAlXUA`
- `SESSION_NAME=blackhat_empire_session`

