# 🔧 Manual ngrok Setup Instructions

Since ngrok needs to run interactively, here's the easiest way:

## ✅ Quick Steps:

### 1. Open a NEW Terminal/Command Prompt
Keep your API server running in one terminal, open a NEW one.

### 2. Run ngrok
In the new terminal, type:
```bash
ngrok http 5000
```

### 3. Copy the URL
You'll see output like:
```
Forwarding   https://abc123-def456.ngrok-free.app -> http://localhost:5000
```

**Copy the `https://` URL** (the one ending in `.ngrok-free.app`)

### 4. Test It
Open in browser:
```
https://[your-url].ngrok-free.app/api/health
```

You should see:
```json
{"status": "healthy", ...}
```

### 5. Add to Lovable AI
- **Secret Name:** `SOLBOY_API_URL`
- **Secret Value:** `https://[your-url].ngrok-free.app`

---

## 🌐 Alternative: Use ngrok Web Interface

After running `ngrok http 5000`, visit:
```
http://localhost:4040
```

This shows a web interface with your public URL.

---

## ⚠️ Important Notes:

1. **Keep both running:**
   - Terminal 1: Your API server (`python api_server.py`)
   - Terminal 2: ngrok (`ngrok http 5000`)

2. **URL changes:** Free ngrok URLs change each time you restart. For production, use a paid plan or deploy your API.

3. **Authentication:** If ngrok asks you to sign up, create a free account at ngrok.com

---

## 🚀 Once You Have the URL:

1. Test it works: `https://[your-url]/api/health`
2. Add to Lovable AI as `SOLBOY_API_URL`
3. Your website will now fetch real data!

---

**That's it!** Just run `ngrok http 5000` in a new terminal and copy the URL. 🎉



