# Railway Workflow Guide

## 🚀 How Railway Auto-Deployment Works

### Automatic Deployment (Recommended)

When you connect a GitHub repository to Railway, it automatically:

1. **Watches your repository** for changes
2. **Detects pushes** to the connected branch (usually `main`)
3. **Automatically redeploys** when you push new commits
4. **Runs the build** using your `Procfile` or detected settings

### Workflow: Making Changes

```
1. Make changes locally
   ↓
2. Commit changes: git commit -m "Your message"
   ↓
3. Push to GitHub: git push
   ↓
4. Railway automatically detects the push
   ↓
5. Railway redeploys your service (usually takes 1-3 minutes)
   ↓
6. Your bot restarts with new changes
```

## 📋 Step-by-Step: After Making Changes

### 1. Make Your Changes Locally
Edit files, add features, fix bugs, etc.

### 2. Commit Changes
```bash
git add .
git commit -m "Description of your changes"
```

### 3. Push to GitHub
```bash
git push
```

### 4. Railway Auto-Deploys
- Railway detects the push within seconds
- Starts a new deployment automatically
- You'll see it in Railway dashboard under "Deployments"
- Usually completes in 1-3 minutes

### 5. Verify Deployment
- Check Railway dashboard → **Deployments** tab
- Look for the latest deployment (should show "Building" then "Active")
- Check **Logs** tab to see if it started successfully

## 🔧 Manual Deployment (If Auto-Deploy is Off)

If auto-deploy is disabled, you can manually trigger:

### Via Railway Dashboard:
1. Go to your service
2. Click **Deployments** tab
3. Click **Redeploy** button

### Via Railway CLI:
```bash
railway up
```

## ✅ Check Auto-Deploy Status

1. Go to Railway dashboard
2. Click your service
3. Go to **Settings** tab
4. Look for **"Auto Deploy"** or **"GitHub"** section
5. Should show: "Connected to GitHub" and "Auto-deploy: Enabled"

## 🔍 Monitor Deployments

### View Deployment Status:
- **Dashboard** → Your service → **Deployments** tab
- Shows all deployments with status (Building, Active, Failed)

### View Logs:
- **Dashboard** → Your service → **Logs** tab
- Real-time logs from your running service
- Check for errors or startup messages

## ⚠️ Important Notes

### Environment Variables
- If you add new environment variables, set them in Railway dashboard
- Go to: Service → **Variables** tab → **+ New Variable**
- Changes take effect on next deployment

### Session Files
- If you update `blackhat_empire_session.session`, you may need to:
  - Upload via Railway **Files** tab, OR
  - Let it recreate on first run (will need phone auth)

### Dependencies
- If you update `requirements.txt`, Railway will auto-install on next deploy
- No manual action needed

## 🎯 Quick Commands

```bash
# Make changes, then:
git add .
git commit -m "Your changes"
git push                    # Railway auto-deploys!

# Check deployment status:
railway status

# View logs:
railway logs

# Manual redeploy (if needed):
railway up
```

## 📊 Deployment Checklist

After pushing changes:
- [ ] Check Railway dashboard for new deployment
- [ ] Wait for deployment to complete (1-3 min)
- [ ] Check logs for any errors
- [ ] Verify bot is running (check logs for "Monitoring started")
- [ ] Test bot commands if needed

## 🐛 Troubleshooting

### Deployment Fails:
1. Check **Logs** tab for error messages
2. Verify all environment variables are set
3. Check `requirements.txt` is correct
4. Ensure `Procfile` exists and is correct

### Bot Not Starting:
1. Check logs for connection errors
2. Verify `BOT_TOKEN` is correct
3. Check session file exists or needs authentication
4. Verify API_ID and API_HASH are correct

### Changes Not Appearing:
1. Wait a few minutes (deployment takes time)
2. Check if deployment actually completed
3. View logs to see if new code is running
4. Try manual redeploy if needed

---

**TL;DR:** Just `git push` and Railway automatically redeploys! 🚀

