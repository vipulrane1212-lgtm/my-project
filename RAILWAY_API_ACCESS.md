# How to Access Your API Server on Railway

## ❌ Why `http://0.0.0.0:8080/` Doesn't Work

`0.0.0.0:8080` is a **bind address** (tells the server to listen on all network interfaces), not a public URL you can access from your browser.

On Railway, you need to use **Railway's public domain** to access your API.

---

## ✅ Step-by-Step: Access Your API

### Step 1: Generate Public Domain in Railway

1. Go to your Railway project: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. Click on your **service** (the one running your bot)
3. Go to the **Settings** tab
4. Scroll down to **"Networking"** section
5. Click **"Generate Domain"** or **"Public Domain"**
6. Railway will create a URL like: `https://your-service-name.up.railway.app`

### Step 2: Access Your API

Once you have the domain, use these URLs:

#### Health Check:
```
https://your-service-name.up.railway.app/api/health
```

#### API Documentation (Swagger UI):
```
https://your-service-name.up.railway.app/docs
```

#### Recent Alerts:
```
https://your-service-name.up.railway.app/api/alerts/recent
```

---

## 🔍 Verify API is Running

### Method 1: Check Railway Logs

1. Go to Railway dashboard → Your service → **Logs** tab
2. Look for:
   ```
   🚀 Starting SolBoy Alerts API Server...
   📡 API will be available at: http://0.0.0.0:8080
   ✅ API server started successfully on port 8080
   ```
   - ✅ **If you see these** → API is running
   - ❌ **If you don't** → Check if API server is enabled in code

### Method 2: Test the Health Endpoint

Open in your browser:
```
https://your-service-name.up.railway.app/api/health
```

Expected response:
```json
{"status": "healthy", "service": "SolBoy Alerts API"}
```

---

## ⚠️ Important Notes

1. **Port 8080**: Railway assigned port 8080 (from `PORT` env var). Your API server is using this port.

2. **Public Domain Required**: You **must** generate a public domain in Railway Settings to access the API from outside Railway.

3. **HTTPS Only**: Railway domains use HTTPS, not HTTP. Always use `https://` not `http://`.

4. **Wait for Deployment**: After generating the domain, wait 1-2 minutes for Railway to configure it.

---

## 🐛 Troubleshooting

### "This site can't be reached"
- ✅ Generate a public domain in Railway Settings
- ✅ Use HTTPS, not HTTP
- ✅ Wait 1-2 minutes after generating domain

### "502 Bad Gateway" or "Connection refused"
- Check Railway logs for errors
- Verify API server is enabled in code
- Check if service is running (should show "Active" in dashboard)

### "404 Not Found"
- API server is running but endpoint is wrong
- Try `/api/health` first to verify API is accessible
- Check Railway logs for the exact port being used

---

## 📝 Quick Checklist

- [ ] Generated public domain in Railway Settings
- [ ] Using HTTPS (not HTTP)
- [ ] Using Railway domain (not `0.0.0.0:8080`)
- [ ] API server enabled in code (check logs)
- [ ] Service shows as "Active" in Railway dashboard

---

**TL;DR:** Generate a public domain in Railway Settings, then access `https://your-domain.up.railway.app/api/health`

