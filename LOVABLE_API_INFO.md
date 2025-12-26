# 📡 API Information for Lovable AI

## API Base URL
```
http://localhost:5000
```

**Note**: This is for local development. When deployed, update to your production API URL.

---

## 🔑 API Endpoints to Use

### 1. Statistics Endpoint
**URL**: `http://localhost:5000/api/stats`  
**Method**: `GET`  
**Description**: Get real-time statistics for dashboard

**Response Format:**
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

**Use in Next.js API Route:**
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
    // Fallback to mock data
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
**URL**: `http://localhost:5000/api/alerts/recent`  
**Method**: `GET`  
**Query Parameters**:
- `limit` (optional): Number of alerts (default: 20)
- `tier` (optional): Filter by tier (1, 2, or 3)

**Examples:**
- `http://localhost:5000/api/alerts/recent`
- `http://localhost:5000/api/alerts/recent?limit=50`
- `http://localhost:5000/api/alerts/recent?tier=1`
- `http://localhost:5000/api/alerts/recent?limit=10&tier=2`

**Response Format:**
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

**New Fields Added:**
- `hotlist`: Hot List status ("Yes" or "No") - Whether token was in Hot List
- `description`: Spicy intro paragraph - Same description shown in Telegram post
- `currentMcap`: Market cap at alert time - The MC shown in the Telegram post (e.g., 143500 for $143.5K)

**Use in Next.js API Route:**
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

### 3. Daily Statistics Endpoint (for Charts)
**URL**: `http://localhost:5000/api/alerts/stats/daily`  
**Method**: `GET`  
**Query Parameters**:
- `days` (optional): Number of days (default: 7)

**Example**: `http://localhost:5000/api/alerts/stats/daily?days=30`

**Response Format:**
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

## 🚀 How to Start the API

1. **Install dependencies:**
```bash
pip install -r requirements_api.txt
```

2. **Run the API:**
```bash
python api_server.py
```

3. **Verify it's working:**
- Visit: `http://localhost:5000/api/health`
- Or: `http://localhost:5000/docs` (Interactive API docs)

---

## 📋 Complete Next.js Integration

### Update your Next.js API routes to use the Python API:

**File: `src/app/api/stats/route.ts`**
```typescript
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const res = await fetch('http://localhost:5000/api/stats', {
      cache: 'no-store',
    })
    if (!res.ok) throw new Error('API error')
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    // Fallback mock data
    return NextResponse.json({
      totalSubscribers: 1250,
      totalAlerts: 3420,
      tier1Alerts: 890,
      tier2Alerts: 1520,
      tier3Alerts: 1010,
      winRate: 68.5,
      recentAlerts24h: 45,
      recentAlerts7d: 320,
    })
  }
}
```

**File: `src/app/api/alerts/recent/route.ts`**
```typescript
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
    if (!res.ok) throw new Error('API error')
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ alerts: [], count: 0 })
  }
}
```

---

## 🔧 Environment Variables (Optional)

Create `.env.local` in your Next.js project:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

Then use in code:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
const res = await fetch(`${apiUrl}/api/stats`)
```

---

## ✅ Checklist for Lovable AI

- [x] API server created (`api_server.py`)
- [x] Dependencies listed (`requirements_api.txt`)
- [x] API endpoints documented
- [x] Next.js integration examples provided
- [x] Fallback mock data included
- [x] Error handling implemented

---

## 📝 Notes for Development

1. **Run API first**: Start the Python API before testing the website
2. **Fallback data**: Website has mock data fallback if API is down
3. **CORS enabled**: API allows all origins (update for production)
4. **Read-only**: API only reads files, never writes (safe to run alongside monitoring)

---

## 🎯 Quick Reference

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `/api/stats` | Dashboard statistics | Stats page, hero section |
| `/api/alerts/recent` | Recent alerts list | Alerts page, recent alerts component |
| `/api/alerts/stats/daily` | Daily chart data | Charts, analytics |
| `/api/health` | Health check | Monitoring, debugging |

---

**Ready to use!** 🚀

The API is safe to run alongside your monitoring system - it only reads files, never writes.



