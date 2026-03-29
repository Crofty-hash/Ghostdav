# Deployment Guide

## Development Environment Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Flutter SDK
- CMake 3.15+
- C++ compiler (g++/clang)
- Git

### Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd ghostdav

# 2. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Activate Python environment
source venv/bin/activate

# 4. Install additional tools
pip install -r requirements.txt

# 5. Run tests
./scripts/run_tests.sh

# 6. Start server
./scripts/run_server.sh
```

## Backend Deployment

### Local Development
```bash
# Terminal 1: Start backend server
python backend/main.py

# Terminal 2: Run tests (optional)
pytest tests/ -v

# Terminal 3: Monitor logs
tail -f logs/ghostdav.log
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
CMD ["python", "backend/main.py"]
```

### Production Deployment
```bash
# Use systemd service
sudo systemctl start ghostdav
sudo systemctl status ghostdav

# Use Docker Compose
docker-compose up -d
```

## Frontend Deployment

### Mobile (Flutter)
```bash
cd frontend/mobile

# iOS
flutter build ios --release

# Android
flutter build apk --release
flutter build appbundle --release

# Deploy to app stores
# Use TestFlight for iOS
# Use Google Play Console for Android
```

### Desktop (Electron)
```bash
cd frontend/desktop

# Development
npm install
npm start

# Production build
npm run build

# Package for distribution
npm run dist
```

## C++ Core Engine Build

```bash
cd core_engine
mkdir build
cd build
cmake ..
make
sudo make install

# Python bindings
# (Would require PyO3/Rust or SWIG)
```

## Monitoring & Logging

### Log Files
- `logs/ghostdav.log` - Main server log
- `logs/connections.log` - Connection events
- `logs/errors.log` - Error log

### Metrics
```bash
# Check server status
curl http://localhost:8888/status

# Monitor connections
watch -n 1 'lsof -i :8888'

# Check performance
top -p $(pgrep -f "python backend/main.py")
```

## Security Hardening

### Encryption
- [ ] Enable TLS for socket connections
- [ ] Use strong key derivation (PBKDF2)
- [ ] Rotate session keys regularly

### Network
- [ ] Run behind firewall
- [ ] Rate limiting on socket server
- [ ] IP whitelisting for admin ports
- [ ] DDoS protection

### Code
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Static analysis (SonarQube)
- [ ] Penetration testing

## Backup & Recovery

### Data Backup
```bash
# Backup configuration
tar -czf ghostdav_backup_$(date +%s).tar.gz logs/

# Restore
tar -xzf ghostdav_backup_*.tar.gz
```

### Database Backup (if applicable)
```bash
# SQLite
cp ghostdav.db ghostdav.db.backup

# PostgreSQL
pg_dump ghostdav > ghostdav_backup.sql
```

## Troubleshooting

### Server Won't Start
```bash
# Check port is not in use
lsof -i :8888

# Check Python version
python --version

# Check dependencies
pip list | grep cryptography
```

### Connection Issues
```bash
# Test STUN server
python -c "from backend.networking import STUNClient; STUNClient().get_external_address()"

# Check firewall
sudo ufw status
```

### Memory Leaks
```bash
# Monitor memory usage
watch -n 1 'ps aux | grep main.py'

# Use memory profiler
pip install memory-profiler
python -m memory_profiler backend/main.py
```

---

For more details, see [README.md](../README.md) and [docs/architecture.md](../docs/architecture.md)
