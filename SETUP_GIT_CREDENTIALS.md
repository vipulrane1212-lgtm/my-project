# Setup Git Credentials for Railway

## 🎯 Goal
Configure Git credentials so Railway can automatically push alerts to GitHub after each alert.

## 📋 Step 1: Create GitHub Personal Access Token (PAT)

1. Go to GitHub: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name it: `Railway Auto-Sync`
4. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - ✅ **workflow** (if using GitHub Actions)
5. Click **"Generate token"**
6. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)
   - Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## 📋 Step 2: Add Token to Railway

### Option A: Via Railway Dashboard (Recommended)

1. Go to Railway dashboard: https://railway.app
2. Navigate to your project → Your service
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Add:
   - **Variable Name:** `GITHUB_TOKEN`
   - **Value:** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (your token)
6. Click **Add**

### Option B: Via Railway CLI

```bash
railway variables --set "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 📋 Step 3: Verify Setup

After Railway redeploys, check the logs for:

```
✅ Synced XXX alerts to Git and pushed to remote
```

If you see:
```
❌ CRITICAL: Git push failed
```

Then check:
1. Token is set correctly in Railway Variables
2. Token has `repo` scope
3. Token hasn't expired

## 🔒 Security Notes

- ✅ Token is stored securely in Railway (encrypted)
- ✅ Token only has `repo` scope (minimal permissions)
- ✅ Token can be revoked anytime from GitHub settings
- ⚠️ Never commit token to Git or share it publicly

## 🧪 Test Locally (Optional)

To test Git sync locally:

```bash
# Set token as environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Or on Windows PowerShell:
$env:GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Run the bot and check if Git sync works
python telegram_monitor_new.py
```

Look for in logs:
```
✅ Synced XXX alerts to Git and pushed to remote
```

## 🔄 Alternative: Use SSH Keys (Advanced)

If you prefer SSH keys instead of PAT:

1. Generate SSH key on Railway
2. Add public key to GitHub: https://github.com/settings/keys
3. Update Git remote to use SSH:
   ```bash
   git remote set-url origin git@github.com:vipulrane1212-lgtm/my-project.git
   ```

## ✅ Verification Checklist

- [ ] GitHub PAT created with `repo` scope
- [ ] Token added to Railway as `GITHUB_TOKEN` variable
- [ ] Railway service redeployed
- [ ] Check Railway logs for "Synced to Git" messages
- [ ] Verify alerts are in GitHub: `git log kpi_logs.json`

---

**Once set up, Railway will automatically push alerts to GitHub after each alert, ensuring zero data loss on redeployments!**

