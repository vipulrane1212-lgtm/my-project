# 🚀 Quick Start - SolBoy Alerts API

## ⚡ 3-Step Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements_api.txt
```

### Step 2: Start API Server
**Windows:**
```bash
start_api.bat
```

**Mac/Linux:**
```bash
chmod +x start_api.sh
./start_api.sh
```

**Or manually:**
```bash
python api_server.py
```

### Step 3: Verify It's Running
Visit: http://localhost:5000/api/health

You should see:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "files": {...}
}
```

---

## 📡 API Endpoints for Lovable AI

### Base URL
```
http://localhost:5000
```

### Main Endpoints

1. **Statistics** (for dashboard)
   - URL: `http://localhost:5000/api/stats`
   - Method: `GET`
   - Returns: Total subscribers, alerts, tier breakdown, win rate

2. **Recent Alerts** (for alerts page)
   - URL: `http://localhost:5000/api/alerts/recent`
   - Method: `GET`
   - Params: `?limit=20&tier=1` (optional)
   - Returns: List of recent alerts

3. **Daily Stats** (for charts)
   - URL: `http://localhost:5000/api/alerts/stats/daily?days=7`
   - Method: `GET`
   - Returns: Daily statistics for charts

---

## 🔗 Next.js Integration

### Update `src/app/api/stats/route.ts`:
```typescript
export async function GET() {
  try {
    const res = await fetch('http://localhost:5000/api/stats', {
      cache: 'no-store',
    })
    const data = await res.json()
    return Response.json(data)
  } catch (error) {
    // Fallback mock data
    return Response.json({
      totalSubscribers: 1250,
      totalAlerts: 3420,
      tier1Alerts: 890,
      tier2Alerts: 1520,
      tier3Alerts: 1010,
      winRate: 68.5,
    })
  }
}
```

### Update `src/app/api/alerts/recent/route.ts`:
```typescript
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') || '20'
    const tier = searchParams.get('tier')
    
    const url = new URL('http://localhost:5000/api/alerts/recent')
    url.searchParams.set('limit', limit)
    if (tier) url.searchParams.set('tier', tier)
    
    const res = await fetch(url.toString(), { cache: 'no-store' })
    const data = await res.json()
    return Response.json(data)
  } catch (error) {
    return Response.json({ alerts: [], count: 0 })
  }
}
```

---

## ✅ What You Have Now

- ✅ `api_server.py` - Complete API server
- ✅ `requirements_api.txt` - Dependencies
- ✅ `LOVABLE_API_INFO.md` - Full documentation for Lovable AI
- ✅ `API_DOCUMENTATION.md` - Complete API reference
- ✅ `start_api.bat` / `start_api.sh` - Easy startup scripts

---

## 📋 Share with Lovable AI

**Copy this to Lovable AI:**

```
API Base URL: http://localhost:5000

Main Endpoints:
1. GET /api/stats - Dashboard statistics
2. GET /api/alerts/recent?limit=20&tier=1 - Recent alerts
3. GET /api/alerts/stats/daily?days=7 - Daily chart data

See LOVABLE_API_INFO.md for complete integration guide.
```

---

## 🎯 Ready to Use!

The API is:
- ✅ Safe (read-only, won't harm your monitoring system)
- ✅ Ready (just run `python api_server.py`)
- ✅ Documented (see API_DOCUMENTATION.md)
- ✅ Integrated (Next.js examples included)

**Start the API and your website will show real data!** 🚀



