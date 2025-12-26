# SolBoy Alerts API Documentation

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements_api.txt
```

### Run the API
```bash
python api_server.py
```

The API will start on: **http://localhost:5000**

---

## 📡 API Endpoints

### Base URL
- **Local**: `http://localhost:5000`
- **Production**: `https://your-api-domain.com` (when deployed)

---

## 🔗 Available Endpoints

### 1. Health Check
**GET** `/api/health`

Check if API is running and files are accessible.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-23T15:30:00.000000+00:00",
  "files": {
    "subscriptions": true,
    "kpi_logs": true,
    "alert_groups": true,
    "user_preferences": true
  }
}
```

---

### 2. Real-Time Statistics
**GET** `/api/stats`

Get comprehensive statistics for the website dashboard.

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

**Use in Next.js:**
```typescript
// src/app/api/stats/route.ts
export async function GET() {
  const res = await fetch('http://localhost:5000/api/stats')
  const data = await res.json()
  return Response.json(data)
}
```

---

### 3. Recent Alerts
**GET** `/api/alerts/recent`

Get recent alerts with optional filtering.

**Query Parameters:**
- `limit` (optional): Number of alerts to return (default: 20)
- `tier` (optional): Filter by tier (1, 2, or 3)

**Examples:**
- `GET /api/alerts/recent` - Get last 20 alerts
- `GET /api/alerts/recent?limit=50` - Get last 50 alerts
- `GET /api/alerts/recent?tier=1` - Get only TIER 1 alerts
- `GET /api/alerts/recent?limit=10&tier=2` - Get last 10 TIER 2 alerts

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
      "tags": ["tiny_buy"],
      "hotlist": "No",
      "description": "Hybrid heat: SUNABOZU's trending + mixed confirms—heat from all angles, no cold spots. Early signals set the stage. Cohort stole the show. Hot List? Standing ovation. Applaud with apes.",
      "currentMcap": 143500
    }
  ],
  "count": 20,
  "timestamp": "2025-12-23T15:30:00.000000+00:00"
}
```

**Response Fields:**
- `id`: Unique alert identifier
- `token`: Token symbol
- `tier`: Alert tier (1, 2, or 3)
- `level`: Alert level (HIGH, MEDIUM)
- `timestamp`: Alert timestamp (ISO format)
- `contract`: Solana contract address
- `score`: Alert score
- `liquidity`: Liquidity in USD
- `callers`: Number of callers
- `subs`: Number of subscribers
- `matchedSignals`: Array of matched signal sources
- `tags`: Array of alert tags
- `hotlist`: Hot List status ("Yes" or "No") ✅ **NEW**
- `description`: Spicy intro paragraph (same as Telegram post) ✅ **NEW**
- `currentMcap`: Market cap shown in the post (entry MC at alert time) ✅ **NEW**

**Use in Next.js:**
```typescript
// src/app/api/alerts/recent/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const limit = searchParams.get('limit') || '20'
  const tier = searchParams.get('tier')
  
  const url = new URL('http://localhost:5000/api/alerts/recent')
  url.searchParams.set('limit', limit)
  if (tier) url.searchParams.set('tier', tier)
  
  const res = await fetch(url.toString())
  const data = await res.json()
  return Response.json(data)
}
```

---

### 4. Subscribers
**GET** `/api/subscribers`

Get subscriber count information.

**Response:**
```json
{
  "totalSubscribers": 1250,
  "userSubscribers": 850,
  "groupSubscribers": 400,
  "usersWithPreferences": 320,
  "lastUpdated": "2025-12-23T15:30:00.000000+00:00"
}
```

---

### 5. Tier Breakdown
**GET** `/api/alerts/tiers`

Get alert breakdown by tier with recent examples.

**Response:**
```json
{
  "tier1": {
    "count": 890,
    "alerts": [
      {
        "token": "SUNABOZU",
        "timestamp": "2025-12-22T14:25:09.827175+00:00",
        "contract": "6EPGCRNQ2FZSC4QP4SFZV4TVWGELJ11A27SCNJHSPUMP"
      }
    ]
  },
  "tier2": {
    "count": 1520,
    "alerts": []
  },
  "tier3": {
    "count": 1010,
    "alerts": []
  },
  "total": 3420
}
```

---

### 6. Daily Statistics
**GET** `/api/alerts/stats/daily`

Get daily statistics for charts (last N days).

**Query Parameters:**
- `days` (optional): Number of days to include (default: 7)

**Example:**
- `GET /api/alerts/stats/daily?days=30` - Get last 30 days

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
    },
    {
      "date": "2025-12-18",
      "total": 52,
      "tier1": 15,
      "tier2": 22,
      "tier3": 15
    }
  ]
}
```

---

## 🔧 Configuration for Lovable AI

### API Base URL
```
http://localhost:5000
```

### For Production
When deploying, update the base URL to your production API:
```
https://your-api-domain.com
```

### CORS
The API is configured to allow all origins. For production, update in `api_server.py`:
```python
allow_origins=["https://your-website-domain.com"]
```

---

## 📝 Next.js Integration Examples

### 1. Stats Component
```typescript
// src/app/api/stats/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const res = await fetch('http://localhost:5000/api/stats', {
      cache: 'no-store', // Always get fresh data
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    // Fallback to mock data if API is down
    return NextResponse.json({
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

### 2. Recent Alerts Component
```typescript
// src/app/api/alerts/recent/route.ts
import { NextResponse } from 'next/server'

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
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ alerts: [], count: 0 })
  }
}
```

---

## 🚀 Deployment Options

### Option 1: Run Locally
```bash
python api_server.py
```

### Option 2: Run as Background Service
```bash
# Windows
pythonw api_server.py

# Linux/Mac
nohup python api_server.py &
```

### Option 3: Deploy to Cloud
- **Railway**: Easy deployment, free tier available
- **Render**: Simple deployment
- **Heroku**: Classic option
- **DigitalOcean**: More control

---

## 🔒 Security Notes

1. **CORS**: Update `allow_origins` in production
2. **Rate Limiting**: Consider adding rate limiting for production
3. **Authentication**: Add API keys if needed for production
4. **HTTPS**: Always use HTTPS in production

---

## 📊 Data Sources

The API reads from these JSON files (created by your monitoring system):
- `subscriptions.json` - User subscriptions
- `kpi_logs.json` - Alert logs and KPIs
- `alert_groups.json` - Telegram groups/channels
- `user_preferences.json` - User tier preferences

---

## ❓ Troubleshooting

### API not starting?
- Check if port 5000 is available
- Install dependencies: `pip install -r requirements_api.txt`

### No data returned?
- Check if JSON files exist
- Verify monitoring system is writing to files
- Check API logs for errors

### CORS errors?
- Update `allow_origins` in `api_server.py`
- Make sure your website domain is included

---

## 📞 Support

For issues or questions, check:
- API docs: `http://localhost:5000/docs` (when running)
- Health check: `http://localhost:5000/api/health`



