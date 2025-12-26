# 🔐 Railway Session File Setup Guide

## Problem
Railway cannot prompt for phone number interactively. You need to upload your Telegram session file.

## ✅ Solution: Upload Session File to Railway

### Step 1: Create Session File Locally (If You Don't Have One)

1. **Run the bot locally**:
   ```bash
   python telegram_monitor_new.py
   ```

2. **Enter your phone number** when prompted:
   ```
   Please enter your phone (or bot token): +1234567890
   ```

3. **Enter the authentication code** sent to your Telegram:
   ```
   Please enter the code you received: 12345
   ```

4. **Session file created**: `blackhat_empire_session.session`

### Step 2: Upload Session File to Railway

#### Option A: Via Railway Dashboard (Easiest)

1. Go to Railway dashboard: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. Click on your service
3. Go to **Files** tab
4. Click **Upload** or drag and drop
5. Upload: `blackhat_empire_session.session`
6. Also upload: `bot_session.session` (if it exists)

#### Option B: Via Railway CLI

```bash
# Navigate to your project directory
cd C:\Users\Admin\Desktop\amaverse

# Upload session file
railway run --service <your-service-name> --file blackhat_empire_session.session
```

#### Option C: Commit to Git (Not Recommended - Security Risk)

⚠️ **WARNING:** Session files contain authentication keys. Only do this if:
- Your repository is private
- You understand the security implications

```bash
# Add to git (only if repo is private!)
git add blackhat_empire_session.session
git commit -m "Add session file for Railway"
git push
```

### Step 3: Verify Session File is on Railway

1. Go to Railway dashboard → Your service → Files tab
2. You should see: `blackhat_empire_session.session`
3. Check file size matches your local file

### Step 4: Redeploy

Railway will automatically redeploy, or manually trigger:
- Go to Railway dashboard → Your service → Deployments
- Click **Redeploy**

## 🔍 Troubleshooting

### Error: "Session file not found"
- ✅ Upload the session file to Railway Files tab
- ✅ Make sure filename matches: `blackhat_empire_session.session`

### Error: "AuthKeyDuplicatedError"
- ✅ Stop bot locally (if running)
- ✅ Delete session file on Railway
- ✅ Upload fresh session file
- ✅ Only run bot in ONE place at a time

### Error: "EOFError: EOF when reading a line"
- ✅ This means Railway is trying to prompt for phone number
- ✅ Upload session file instead (Railway can't prompt interactively)

## 📝 Session File Location

**Local:**
- `blackhat_empire_session.session` (in your project directory)
- `bot_session.session` (for bot client)

**Railway:**
- Upload to: `/app/blackhat_empire_session.session`
- Upload to: `/app/bot_session.session` (if exists)

## 🔒 Security Notes

- **Never commit session files to public repositories**
- Session files contain authentication keys
- If session file is compromised, delete it and create a new one
- Use Railway's secure file storage (Files tab)

## ✅ Verification

After uploading and redeploying, check Railway logs:
```
✅ Connection successful!
Connected as: Your Name (@username)
```

If you see this, the session file is working correctly!

---

**Last Updated:** December 26, 2025

