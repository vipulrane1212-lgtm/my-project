# How to Check if API Server is Running on Railway

## 🔍 Quick Check Methods

### 1. **Check Railway Logs** (Easiest)
1. Go to your Railway project: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. Click on your service
3. Go to **Logs** tab
4. Look for these messages:
   ```
   🚀 Starting SolBoy Alerts API Server...
   📡 API will be available at: http://0.0.0.0:5000
   📖 API docs at: http://0.0.0.0:5000/docs
   ```
   - ✅ **If you see these** → API server is running
   - ❌ **If you don't see these** → API server is disabled

### 2. **Check Railway Service URL**
1. Go to Railway dashboard → Your service
2. Go to **Settings** tab
3. Look for **"Public Domain"** or **"Generate Domain"**
4. Railway will give you a URL like: `https://your-service-name.up.railway.app`
5. Try accessing:
   - `https://your-service-name.up.railway.app/api/health`
   - `https://your-service-name.up.railway.app/api/alerts/recent`
   - `https://your-service-name.up.railway.app/docs` (API documentation)

### 3. **Test API Endpoints Directly**

#### Health Check:
```bash
curl https://your-service-name.up.railway.app/api/health
```
Expected response:
```json
{"status": "healthy", "service": "SolBoy Alerts API"}
```

#### Recent Alerts:
```bash
curl https://your-service-name.up.railway.app/api/alerts/recent
```
Expected response:
```json
{
  "alerts": [...],
  "count": 10,
  "timestamp": "2025-12-22T..."
}
```

#### API Documentation:
Open in browser:
```
https://your-service-name.up.railway.app/docs
```

### 4. **Check Railway Metrics**
1. Go to Railway dashboard → Your service
2. Go to **Metrics** tab
3. Look for network traffic on port 5000
4. If you see traffic, the API is likely running

---

## ⚠️ Current Status

**The API server is currently DISABLED** in the code.

To check if it's enabled:
1. Open `telegram_monitor_new.py`
2. Look for line ~1828-1832
3. If you see:
   ```python
   await asyncio.gather(
       run_api_server(),  # ← This line means API is enabled
       monitor.start(),
   )
   ```
   → API is **enabled**

4. If you see:
   ```python
   await monitor.start()  # ← Only this means API is disabled
   ```
   → API is **disabled** (current state)

---

## 🔧 How to Re-Enable API Server

If you want to enable the API server again:

1. Edit `telegram_monitor_new.py`
2. Find the `main()` function (around line 1820)
3. Change this:
   ```python
   # Start monitor only (API server disabled)
   await monitor.start()
   ```
   
   To this:
   ```python
   # Start API server and monitor concurrently
   await asyncio.gather(
       run_api_server(),
       monitor.start(),
       return_exceptions=True
   )
   ```

4. Commit and push:
   ```bash
   git add telegram_monitor_new.py
   git commit -m "Re-enable API server"
   git push
   ```

5. Railway will auto-deploy and start the API server

---

## 📊 Railway Port Configuration

**Important:** Railway automatically assigns a port via the `PORT` environment variable.

If your API server needs to use Railway's assigned port instead of hardcoded 5000:

1. Check Railway's `PORT` environment variable
2. Update `api_server.py` to use: `os.getenv("PORT", "5000")`

Current code uses port 5000, which should work, but Railway might assign a different port.

---

## 🐛 Troubleshooting

### API Not Responding?

1. **Check if API server code is enabled** (see above)
2. **Check Railway logs** for errors
3. **Verify port configuration** - Railway uses `PORT` env var
4. **Check service is running** - Look for "Monitoring started" in logs
5. **Check Railway domain** - Make sure public domain is generated

### Common Errors:

- **"Connection refused"** → API server not running or wrong port
- **"404 Not Found"** → API server running but endpoint wrong
- **"502 Bad Gateway"** → Service crashed, check logs
- **No response** → Service might be starting up (wait 1-2 minutes)

---

## ✅ Quick Verification Checklist

- [ ] API server code is enabled in `telegram_monitor_new.py`
- [ ] Railway logs show "Starting SolBoy Alerts API Server"
- [ ] `/api/health` endpoint returns `{"status": "healthy"}`
- [ ] `/docs` endpoint shows Swagger UI
- [ ] Railway service shows as "Active" in dashboard

---

**TL;DR:** Check Railway logs for "Starting SolBoy Alerts API Server" message, or test `https://your-railway-url.up.railway.app/api/health`

