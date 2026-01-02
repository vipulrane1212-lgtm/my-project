# Railway Git Setup - Quick Instructions

## 🚀 Quick Setup (5 minutes)

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. **Token name:** `Railway Auto-Sync`
3. **Expiration:** Choose (90 days recommended)
4. **Select scopes:**
   - ✅ **repo** (Full control of private repositories)
5. Click **"Generate token"**
6. **COPY THE TOKEN** (starts with `ghp_`)

### Step 2: Add to Railway

1. Go to Railway: https://railway.app
2. Your project → Your service
3. **Variables** tab
4. Click **+ New Variable**
5. **Name:** `GITHUB_TOKEN`
6. **Value:** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (paste your token)
7. Click **Add**

### Step 3: Redeploy

Railway will automatically redeploy. After redeploy, check logs for:

```
✅ Synced XXX alerts to Git and pushed to remote
```

## ✅ Verification

After Railway redeploys, verify it's working:

1. **Check Railway Logs:**
   - Look for: `✅ Synced XXX alerts to Git and pushed to remote`
   - Should appear after each alert

2. **Check GitHub:**
   - Go to: https://github.com/vipulrane1212-lgtm/my-project
   - Check `kpi_logs.json` - should update after each alert

3. **Test Alert:**
   - Wait for next alert
   - Check if it appears in GitHub within seconds

## 🐛 Troubleshooting

### If you see "Git push failed":

1. **Check Token:**
   - Verify `GITHUB_TOKEN` is set in Railway Variables
   - Token should start with `ghp_`

2. **Check Token Permissions:**
   - Go to: https://github.com/settings/tokens
   - Verify token has `repo` scope

3. **Check Token Expiration:**
   - Tokens can expire
   - Create new token if expired

4. **Check Railway Logs:**
   - Look for specific error message
   - Common: "Authentication failed" = wrong token

## 🔒 Security

- ✅ Token is encrypted in Railway
- ✅ Token only has `repo` scope (minimal permissions)
- ✅ Can revoke anytime from GitHub
- ⚠️ Never commit token to code

## 📝 Notes

- Token is used automatically by the bot
- No manual Git commands needed
- Works on every Railway redeploy
- Alerts are pushed to GitHub after each alert

---

**That's it! Once set up, Railway will automatically push alerts to GitHub after each alert, ensuring zero data loss on redeployments.**

