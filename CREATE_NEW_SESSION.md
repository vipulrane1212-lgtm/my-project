# 🔐 Create New Session for Railway

## Step-by-Step Guide

### Step 1: Create Session File Locally

1. **Make sure you're in the project directory**:
   ```bash
   cd C:\Users\Admin\Desktop\amaverse
   ```

2. **Run the bot locally**:
   ```bash
   python telegram_monitor_new.py
   ```

3. **When prompted, enter your phone number**:
   ```
   Please enter your phone (or bot token): +1234567890
   ```
   - Include country code (e.g., +1 for US, +91 for India)
   - Use the same format as your Telegram account

4. **Enter the authentication code** sent to your Telegram:
   ```
   Please enter the code you received: 12345
   ```
   - Check your Telegram app for the code
   - Enter it within the time limit

5. **If 2FA is enabled, enter your password**:
   ```
   Please enter your password: your_2fa_password
   ```

6. **Session file created**: 
   - `blackhat_empire_session.session` (or whatever your SESSION_NAME is)
   - The bot will connect and you'll see: `✅ Connection successful!`

7. **Stop the bot** (press `Ctrl+C`)

### Step 2: Verify Session File Exists

Check that the session file was created:
```bash
dir *.session
```

You should see:
- `blackhat_empire_session.session`
- `bot_session.session` (if bot token is set)

### Step 3: Upload to Railway

#### Option A: Via Railway Dashboard (Recommended)

1. Go to Railway dashboard: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. Click on your service
3. Go to **Files** tab
4. Click **Upload** or drag and drop
5. Upload: `blackhat_empire_session.session`
6. Wait for upload to complete

#### Option B: Via Railway CLI

```bash
# Make sure you're logged in
railway login

# Link to your project (if not already linked)
railway link -p 3b315a2d-7565-4bec-96d6-6b21f35ca241

# Upload session file
railway run --file blackhat_empire_session.session
```

### Step 4: Verify on Railway

1. Go to Railway dashboard → Your service → Files tab
2. You should see: `blackhat_empire_session.session`
3. Check the file size matches your local file

### Step 5: Redeploy

Railway will automatically redeploy, or manually trigger:
- Go to Railway dashboard → Your service → Deployments
- Click **Redeploy** or wait for auto-deploy

### Step 6: Check Logs

After redeploy, check Railway logs:
```
✅ Connection successful!
Connected as: Your Name (@username)
```

If you see this, the session file is working! 🎉

## Troubleshooting

### "Session file not found" on Railway
- ✅ Make sure you uploaded the file to the correct service
- ✅ Check the file name matches `SESSION_NAME` environment variable
- ✅ Verify the file uploaded successfully (check file size)

### "AuthKeyDuplicatedError"
- ✅ Stop the bot locally (if running)
- ✅ Delete old session file on Railway
- ✅ Upload the new session file
- ✅ Only run bot in ONE place at a time

### "EOFError: EOF when reading a line"
- ✅ This means Railway tried to prompt for phone number
- ✅ Session file must be uploaded (Railway can't prompt interactively)
- ✅ Follow Step 1 to create session locally first

## Security Notes

- ⚠️ **Never commit session files to public repositories**
- ⚠️ Session files contain authentication keys
- ⚠️ If session file is compromised, delete it and create a new one
- ✅ Use Railway's secure file storage (Files tab)

---

**Last Updated:** December 26, 2025

