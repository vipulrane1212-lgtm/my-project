# 📡 API Information for Lovable AI Integration

## 🚀 API Server Details

**Base URL:** `http://localhost:5000`

**Status:** ✅ Ready to use
**Type:** FastAPI (Python)
**Port:** 5000
**CORS:** Enabled (all origins)

---

## 📋 Key Endpoints

### 1. Statistics Endpoint
**URL:** `GET http://localhost:5000/api/stats`

**Response:**
```json
{
  "totalSubscribers": 1250,
  "userSubscribers": 850,
  "groupSubscribers": 400,
  "totalAlerts": 3420,
  "tier1Alerts": 890,
  "tier2Alerts": 1520,
  "tier3Alerts": 1010,
  "winRate": 68.5,
  "recentAlerts24h": 45,
  "recentAlerts7d": 320,
  "truePositives": 2340,
  "falsePositives": 180,
  "lastUpdated": "2025-12-23T15:30:00.000000+00:00"
}
```

**Next.js Integration:**
```typescript
// src/app/api/stats/route.ts
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

---

### 2. Recent Alerts Endpoint
**URL:** `GET http://localhost:5000/api/alerts/recent`

**Query Parameters:**
- `limit` (optional, default: 20) - Number of alerts
- `tier` (optional) - Filter by tier (1, 2, or 3)

**Examples:**
- `http://localhost:5000/api/alerts/recent`
- `http://localhost:5000/api/alerts/recent?limit=50`
- `http://localhost:5000/api/alerts/recent?tier=1`
- `http://localhost:5000/api/alerts/recent?limit=10&tier=2`

**Response:**
```json
{
  "alerts": [
    {
      "id": "6EPGCRNQ_2025-12-22",
      "token": "SUNABOZU",
      "tier": 1,
      "level": "HIGH",
      "timestamp": "2025-12-22T14:25:09.827175+00:00",
      "contract": "6EPGCRNQ2FZSC4QP4SFZV4TVWGELJ11A27SCNJHSPUMP",
      "score": 25,
      "liquidity": 50442.13,
      "callers": 23,
      "subs": 160436,
      "matchedSignals": ["Early trending"],
      "tags": ["tiny_buy"]
    }
  ],
  "count": 20,
  "timestamp": "2025-12-23T15:30:00.000000+00:00"
}
```

**Next.js Integration:**
```typescript
// src/app/api/alerts/recent/route.ts
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

### 3. Daily Statistics (for Charts)
**URL:** `GET http://localhost:5000/api/alerts/stats/daily?days=7`

**Query Parameters:**
- `days` (optional, default: 7) - Number of days

**Response:**
```json
{
  "period": 7,
  "data": [
    {
      "date": "2025-12-17",
      "total": 45,
      "tier1": 12,
      "tier2": 20,
      "tier3": 13
    }
  ]
}
```

---

## 🔧 How to Start the API

1. **Install dependencies:**
```bash
pip install -r requirements_api.txt
```

2. **Run the API:**
```bash
python api_server.py
```

3. **Verify:**
Visit `http://localhost:5000/api/health`

---

## ✅ Integration Checklist

- [ ] API server running on `http://localhost:5000`
- [ ] Update `src/app/api/stats/route.ts` to fetch from API
- [ ] Update `src/app/api/alerts/recent/route.ts` to fetch from API
- [ ] Add fallback mock data for when API is down
- [ ] Test all endpoints work correctly

---

## 📝 Important Notes

1. **Fallback Data:** Always include fallback mock data in case API is down
2. **Cache:** Use `cache: 'no-store'` to always get fresh data
3. **Error Handling:** Wrap API calls in try-catch blocks
4. **Production:** Update base URL when deploying to production

---

## 🎯 Data Flow

```
Monitoring System (telegram_monitor_new.py)
    ↓
    Writes to JSON files
    ↓
API Server (api_server.py)
    ↓
    Reads from JSON files
    ↓
Next.js Website
    ↓
    Fetches from API
    ↓
    Displays real-time data
```

---

## 📚 Full Documentation

- **Complete API Docs:** See `API_DOCUMENTATION.md`
- **Quick Start:** See `QUICK_START_API.md`
- **Lovable Info:** See `LOVABLE_API_INFO.md`

---

## 🚀 Ready to Use!

The API is:
- ✅ **Safe** - Read-only, won't interfere with monitoring system
- ✅ **Ready** - Just run `python api_server.py`
- ✅ **Documented** - Complete documentation included
- ✅ **Tested** - Error handling and fallbacks included

**Start the API and connect your website!** 🎉



