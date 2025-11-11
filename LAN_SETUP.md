# LAN Development Setup

## Quick Start:

### 1. Start Backend on LAN:
```bash
cd backend/backend
python run_lan.py
```

This will show your computer's IP address like:
```
📱 Frontend should use: http://192.168.1.100:8000/api
```

### 2. Update Frontend Config:
Edit `spotifyClone/config/api.ts` and update the IP:
```typescript
const COMPUTER_IP = "192.168.1.100"; // Your actual IP from step 1
```

### 3. Start Frontend:
```bash
cd spotifyClone
npm start
```

## Benefits of LAN Setup:
- ✅ Keep Ollama running locally (llama3:8b works)
- ✅ Use local SQLite database
- ✅ No need for PostgreSQL setup
- ✅ Frontend can connect from phone/emulator
- ✅ All AI features work perfectly

## Troubleshooting:

### Can't connect from phone?
- Make sure both devices are on same WiFi
- Check firewall settings
- Try different IP (run `ipconfig` or `ifconfig`)

### Still getting network errors?
- Restart both backend and frontend
- Check the IP in frontend config matches backend output
- Try using `http://10.0.2.2:8000/api` for Android emulator

## Network Requirements:
- Both computer and phone on same WiFi network
- No VPN blocking local connections
- Firewall allows port 8000