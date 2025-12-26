# 🔄 Update Lovable AI to Use Railway API

## ✅ Your Railway API is Working!

Your Railway API is live and accessible at:
**https://my-project-production-3d70.up.railway.app/**

The API is responding correctly (as confirmed by the root endpoint).

---

## 🔧 Update Lovable AI Configuration

### Step 1: Update the API Secret in Lovable AI

1. Go to your **Lovable AI project**
2. Navigate to **Settings** → **Secrets** (or **Environment Variables**)
3. Find the secret named: `SOLBOY_API_URL`
4. **Update it** to:
   ```
   https://my-project-production-3d70.up.railway.app
   ```
5. **Save** the changes

### Step 2: Verify the Update

After updating, your Lovable AI frontend should now connect to:
- ✅ `https://my-project-production-3d70.up.railway.app/api/stats`
- ✅ `https://my-project-production-3d70.up.railway.app/api/alerts/recent`
- ✅ `https://my-project-production-3d70.up.railway.app/api/health`

---

## 📋 Complete API Endpoints (Railway)

### Base URL:
```
https://my-project-production-3d70.up.railway.app
```

### Available Endpoints:

1. **Health Check:**
   ```
   https://my-project-production-3d70.up.railway.app/api/health
   ```

2. **Statistics:**
   ```
   https://my-project-production-3d70.up.railway.app/api/stats
   ```

3. **Recent Alerts:**
   ```
   https://my-project-production-3d70.up.railway.app/api/alerts/recent
   ```
   With filters:
   - `?limit=20` - Number of alerts
   - `?tier=1` - Filter by tier (1, 2, or 3)
   - `?limit=50&tier=1` - Combined filters

4. **Subscribers:**
   ```
   https://my-project-production-3d70.up.railway.app/api/subscribers
   ```

5. **Tier Breakdown:**
   ```
   https://my-project-production-3d70.up.railway.app/api/alerts/tiers
   ```

6. **Daily Stats:**
   ```
   https://my-project-production-3d70.up.railway.app/api/alerts/stats/daily?days=7
   ```

7. **API Documentation:**
   ```
   https://my-project-production-3d70.up.railway.app/docs
   ```

---

## 🔍 Test Your API

### Quick Test in Browser:

1. **Health Check:**
   ```
   https://my-project-production-3d70.up.railway.app/api/health
   ```
   Should return: `{"status": "healthy", "service": "SolBoy Alerts API"}`

2. **Statistics:**
   ```
   https://my-project-production-3d70.up.railway.app/api/stats
   ```
   Should return subscriber and alert statistics

3. **Recent Alerts:**
   ```
   https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=5
   ```
   Should return recent alerts

---

## 📝 For Lovable AI Code

If you have hardcoded API URLs in your Lovable AI code, update them:

### Before (Old - ngrok/localhost):
```typescript
const apiUrl = 'https://mildred-unstatuesque-seedily.ngrok-free.dev'
// or
const apiUrl = 'http://localhost:5000'
```

### After (New - Railway):
```typescript
const apiUrl = 'https://my-project-production-3d70.up.railway.app'
```

### Using Environment Variable (Recommended):
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://my-project-production-3d70.up.railway.app'
```

Then set in Lovable AI secrets:
- **Secret Name:** `NEXT_PUBLIC_API_URL`
- **Secret Value:** `https://my-project-production-3d70.up.railway.app`

---

## ✅ Checklist

- [ ] Updated `SOLBOY_API_URL` secret in Lovable AI
- [ ] Tested health endpoint: `https://my-project-production-3d70.up.railway.app/api/health`
- [ ] Tested stats endpoint: `https://my-project-production-3d70.up.railway.app/api/stats`
- [ ] Updated any hardcoded API URLs in Lovable AI code
- [ ] Redeployed Lovable AI app (if needed)
- [ ] Verified frontend is now connecting to Railway API

---

## 🐛 Troubleshooting

### Lovable AI still not connecting?

1. **Check the secret name** - Make sure it's exactly `SOLBOY_API_URL` (case-sensitive)
2. **Check the URL** - Must include `https://` (not `http://`)
3. **No trailing slash** - Use `https://my-project-production-3d70.up.railway.app` (not `...app/`)
4. **Redeploy** - After updating secrets, you may need to redeploy your Lovable AI app
5. **Check browser console** - Look for CORS errors or connection errors

### CORS Issues?

The Railway API has CORS enabled for all origins (`allow_origins=["*"]`), so this shouldn't be an issue. If you see CORS errors, check:
- The API URL is correct
- You're using HTTPS (not HTTP)
- The endpoint path is correct (e.g., `/api/stats` not `/stats`)

---

## 🎯 Summary

**Old API URL (ngrok/localhost):** ❌ No longer working
```
https://mildred-unstatuesque-seedily.ngrok-free.dev
or
http://localhost:5000
```

**New API URL (Railway):** ✅ Working now
```
https://my-project-production-3d70.up.railway.app
```

**Action Required:** Update `SOLBOY_API_URL` secret in Lovable AI to the new Railway URL.

