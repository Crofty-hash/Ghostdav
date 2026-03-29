# GhostDav Deployment Guide

Complete guide to deploying GhostDav P2P encrypted messaging platform across all platforms.

## 📋 Deployment Overview

GhostDav consists of:
1. **Backend Server** - Python 3.12, runs on any machine (port 8888)
2. **Desktop Client** - HTML (zero deps) or Electron/React
3. **Mobile Client** - Flutter (iOS & Android)

## 🚀 Server Deployment

### Local Development

**1. Install Python 3.12+**
```bash
# Ubuntu/Debian
sudo apt-get install python3.12 python3.12-venv

# macOS
brew install python@3.12

# Windows
# Download from https://www.python.org/downloads/
```

**2. Create Virtual Environment**
```bash
cd GhostDav
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Start Server**
```bash
python3 -m backend.main
# Output:
# INFO:__main__:External address discovered: 192.168.1.X:PORT
# INFO:__main__:Server listening on 0.0.0.0:8888
```

### Docker Deployment

**Build Docker Image**
```bash
docker build -t ghostdav-server .
docker run -p 8888:8888 ghostdav-server
```

### Systemd Service (Linux)

**Create service file**
```bash
sudo nano /etc/systemd/system/ghostdav.service
```

**Service configuration**
```ini
[Unit]
Description=GhostDav P2P Server
After=network.target

[Service]
Type=simple
User=ghostdav
WorkingDirectory=/opt/ghostdav
ExecStart=/opt/ghostdav/venv/bin/python3 -m backend.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ghostdav
sudo systemctl start ghostdav
sudo systemctl status ghostdav
```

## 💻 Desktop Client Deployment

### Option 1: HTML Client (Instant - No Setup)

**Zero dependencies - just open in browser**
```bash
# Linux
xdg-open frontend/desktop/index.html

# macOS
open frontend/desktop/index.html

# Windows
start frontend/desktop/index.html

# Or from any web server
python3 -m http.server --directory frontend/desktop 8000
# Then open http://localhost:8000
```

### Option 2: Electron Client

**Prerequisites**
- Node.js 18+
- npm or yarn

**Build**
```bash
cd frontend/desktop
npm install
npm start
```

**Build for Release**
```bash
npm run build
# Creates executables in out/GhostDav-win32-x64/ (Windows)
# Creates executables in out/GhostDav-darwin-arm64/ (macOS)
# Creates executables in out/GhostDav-linux-x64/ (Linux)
```

**Package Installer**
```bash
npm run dist
# Creates .exe (Windows), .dmg (macOS), .AppImage (Linux)
```

## 📱 Mobile Client Deployment

### Prerequisites
```bash
# Install Flutter SDK
# https://flutter.dev/docs/get-started/install

# Verify installation
flutter doctor
# Should show: ✓ Flutter, ✓ Dart, ✓ Android/iOS Setup
```

### Android Deployment

**Development**
```bash
cd frontend/mobile
flutter pub get
flutter run
# Select Android emulator or connected device
```

**Build APK**
```bash
flutter build apk --release
# Output: build/app/outputs/apk/release/app-release.apk
```

**Install on Device**
```bash
adb install build/app/outputs/apk/release/app-release.apk
```

**Build for Google Play**
```bash
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab
# Upload to Google Play Console
```

### iOS Deployment

**Development**
```bash
cd frontend/mobile
flutter pub get
flutter run
# Select iOS simulator or connected device
```

**Build IPA**
```bash
flutter build ios --release
# Output: build/ios/iphoneos/Runner.app
```

**Generate IPA for Distribution**
```bash
flutter build ios --release --no-codesign
# Use Xcode to code sign and create .ipa
```

**Deploy via TestFlight**
1. Open `ios/Runner.xcworkspace` in Xcode
2. Select Product → Archive
3. Upload to App Store Connect
4. Submit to TestFlight for testing

**Deploy to App Store**
1. Complete TestFlight testing
2. Submit for App Store review
3. Monitor review status in App Store Connect

## 🔧 Configuration

### Backend Configuration

**Environment Variables**
```bash
# Server settings
export GHOSTDAV_HOST="0.0.0.0"
export GHOSTDAV_PORT="8888"

# Cryptography
export GHOSTDAV_CRYPTO_ITERATIONS="100000"
export GHOSTDAV_NONCE_SIZE="24"

# Routing
export GHOSTDAV_ALIAS_ROTATION_INTERVAL="300"
export GHOSTDAV_SESSION_TIMEOUT="3600"

# STUN/TURN
export GHOSTDAV_STUN_SERVERS="stun.l.google.com:19302,stun1.l.google.com:19302"
export GHOSTDAV_TURN_SERVER="turn.example.com"
export GHOSTDAV_TURN_USER="username"
export GHOSTDAV_TURN_PASSWORD="password"

# Logging
export GHOSTDAV_DEBUG="false"
export GHOSTDAV_LOG_LEVEL="INFO"
```

### Client Configuration

**Desktop HTML Client**
Edit `frontend/desktop/index.html`:
```javascript
const BACKEND_URL = 'http://localhost:8888';
// Change to your server IP/domain for remote deployment
const BACKEND_URL = 'http://192.168.1.100:8888';  // LAN
const BACKEND_URL = 'https://ghostdav.example.com';  // Production
```

**Flutter Mobile Client**
Edit `frontend/mobile/lib/main.dart`:
```dart
static const String BACKEND_URL = 'http://localhost:8888';
// Change to:
static const String BACKEND_URL = 'http://192.168.1.100:8888';  // LAN
```

## 🌐 Production Deployment

### Network Setup

**Port Forwarding**
```
WAN → Internet → Router → Port 8888 → Server (LAN)
```

**Firewall Rules**
```bash
# Linux iptables
sudo iptables -A INPUT -p tcp --dport 8888 -j ACCEPT

# Ubuntu ufw
sudo ufw allow 8888/tcp
```

**DNS Configuration**
```bash
# Point domain to your server
example.com A 203.0.113.456

# Update client configs to use domain
const BACKEND_URL = 'http://ghostdav.example.com:8888';
```

### Security Hardening

**TLS/HTTPS**
1. Install Let's Encrypt certificate
2. Configure reverse proxy (Nginx, Caddy, etc.)
3. Update clients to use `https://`

**Rate Limiting**
```bash
# Use reverse proxy to limit connections
# Example: Nginx
limit_req_zone $binary_remote_addr zone=ghostdav:10m rate=100r/s;
limit_req zone=ghostdav burst=200;
```

**Monitoring**
```bash
# Monitor server logs
tail -f server.log | grep -E "ERROR|WARNING"

# Monitor connections
netstat -an | grep 8888
ss -tan | grep 8888
```

### Reverse Proxy (Nginx)

```nginx
upstream ghostdav {
    server 127.0.0.1:8888;
}

server {
    listen 80;
    server_name ghostdav.example.com;
    
    location / {
        proxy_pass http://ghostdav;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring & Maintenance

### Health Check
```bash
# Check if server is running
curl http://localhost:8888

# Check for listener
lsof -i :8888

# Get server info
ps aux | grep backend.main
```

### Log Monitoring
```bash
# Real-time logs
tail -f backend.log

# Error logs
grep ERROR backend.log

# Last 100 connections
grep "client connected" backend.log | tail -100
```

### Performance Monitoring
```bash
# CPU & Memory
top -p $(pgrep -f backend.main)

# Network connections
netstat -an | grep 8888 | wc -l

# Message throughput
grep "Routed message" backend.log | wc -l
```

## 🛠 Troubleshooting

### Server won't start
```bash
# Check if port 8888 is in use
lsof -i :8888
# Kill existing process
pkill -f "backend.main"
# Try again
python3 -m backend.main
```

### Clients can't connect
```bash
# Check firewall
sudo ufw status
sudo iptables -L -n | grep 8888

# Check server binding
netstat -tan | grep 8888

# Test local connection
curl http://127.0.0.1:8888
```

### Mobile app can't reach server
- Ensure backend is on same network or accessible via IP
- Update BACKEND_URL to server's actual IP address
- Check that firewall allows port 8888 from client device
- For emulators, use `10.0.2.2` instead of `localhost`

### Flutter build issues
```bash
flutter clean
flutter pub get
flutter pub upgrade
flutter doctor -v
```

## 📚 Deployment Checklist

- [ ] Backend server running and accessible
- [ ] STUN/TURN configured for NAT traversal
- [ ] Desktop HTML client opening in browser
- [ ] Desktop Electron client built (optional)
- [ ] Mobile client built for Android
- [ ] Mobile client built for iOS
- [ ] All clients connecting to backend
- [ ] Encryption roundtrip tested
- [ ] Multi-peer messaging verified
- [ ] Firewall rules configured
- [ ] TLS/HTTPS setup (production)
- [ ] Monitoring & logging enabled
- [ ] Backup strategy in place

## 📞 Support

For deployment issues:
1. Check server logs: `grep ERROR backend.log`
2. Test connectivity: `curl -v http://SERVER:8888`
3. Run diagnostic: `flutter doctor -v`
4. Review network: `netstat -an | grep 8888`

---

**Last Updated**: 2026-03-21  
**Version**: 1.0.0  
**Status**: Production Ready
