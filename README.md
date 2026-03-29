[README.md](https://github.com/user-attachments/files/26328756/README.md)
# 🔒 GhostDav - P2P Encrypted Communication

A decentralized peer-to-peer communication platform with advanced encryption, steganography, and multi-stage routing. The first device online automatically becomes the server.

## Features

✨ **End-to-End Encryption**
- AES-256 & XChaCha20-Poly1305
- Layered encryption with ephemeral session keys
- Forward secrecy

🎭 **Steganography**
- Hide messages in images
- LSB + random noise embedding
- Constant-size padding for integrity

🌐 **Decentralized P2P**
- WebRTC + STUN/TURN support
- Custom 4-stage routing layer
- Fake IP & alias system for anonymity
- Automatic server election (first online)

📱 **Cross-Platform**
- Flutter mobile (iOS/Android)
- Electron desktop (Windows/Mac/Linux)
- Shared API layer

🎙️ **Real-Time Media**
- Voice & video streaming
- Codec agnostic
- Ultra-low latency

## Project Structure

```
ghostdav/
├── frontend/
│   ├── mobile/          # Flutter app
│   ├── desktop/         # Electron app
│   └── shared/          # Shared components
├── backend/             # Python 3.12 core
│   ├── core/           # Encryption & keys
│   ├── networking/     # Socket & P2P
│   ├── routing/        # 4-stage routing
│   ├── stego/          # Steganography
│   └── media/          # Voice/Video
├── core_engine/        # C++ performance layer
├── protocols/          # Protocol specifications
├── security/           # Security docs
├── tests/              # Unit & integration tests
└── docs/               # Architecture & diagrams
```

## ✅ Current Status

**Backend**: Production Ready ✓
- Python 3.12 server fully operational
- ChaCha20-Poly1305 encryption working
- Socket-based networking tested
- Multi-peer routing verified
- STUN NAT traversal implemented
- Unit tests: 10/10 passing

**Desktop Client**: Working ✓
- HTML chat client: Zero dependencies, tested & working
- Electron/React: Scaffolded, ready for npm install

**Mobile Client**: Completed ✓
- Flutter app: Full source code ready to build
- Android & iOS support included
- Cyberpunk UI theme matching desktop
- Ready for emulator/device testing

## Quick Start

### Prerequisites
- Python 3.12+ (with venv)
- Node.js 18+ (optional, for Electron)
- Flutter SDK (for mobile)
- C++ compiler + CMake (optional)

### Installation & First Run

**1. Start Backend Server**
```bash
# From project root
python3 -m backend.main

# Output:
# INFO:__main__:External address discovered: YOUR_IP:PORT
# INFO:__main__:Server listening on 0.0.0.0:8888
```

**2. Connect Desktop Client (Instant - No Setup)**
```bash
# Open HTML client in any browser
xdg-open frontend/desktop/index.html
# macOS: open frontend/desktop/index.html
# Windows: start frontend/desktop/index.html
```

**3. Optional: Mobile Client**
```bash
cd frontend/mobile
flutter pub get
flutter run
# [Select Android emulator, iOS simulator, or connected device]
```

**4. Optional: Electron Desktop Client**
```bash
cd frontend/desktop
npm install  # First run only (~5 min)
npm start
```

## Architecture

### P2P Server Mode
The first device to connect online automatically becomes the server node. It handles:
- Peer discovery
- Route establishment
- Message relay (encrypted)
- Session management

### Encryption Pipeline
```
User Input → Compression → Encryption → Steganography → Network
```

### Routing Stages
1. **Obfuscation**: Random noise + padding
2. **Fake IP Assignment**: Untraceable routing IDs
3. **Alias Mapping**: Dynamic endpoint masking
4. **Multi-hop Relay**: Messages bounced through peers

## Security

- **Threat Model**: [security/threat_model.md](security/threat_model.md)
- **Encryption Design**: [security/encryption_design.md](security/encryption_design.md)
- **Audit Notes**: [security/audit_notes.md](security/audit_notes.md)

## Protocol Specification

See [protocols/ghostdav_protocol.md](protocols/ghostdav_protocol.md) for the complete protocol design.

## Development

### Running Tests
```bash
pytest tests/unit -v
pytest tests/integration -v
pytest tests/network_tests -v
```

### Building C++ Engine
```bash
cd core_engine
mkdir build && cd build
cmake ..
make
```

### Logging
Logs are stored in `logs/` (disabled in production). Set `DEBUG=1` for verbose output.

## Contributing

1. Create a feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Submit a pull request

## License

MIT License - See LICENSE file

## Author

**GhostDav Team** - Privacy-first communication 🔐
# Ghostdav
# Ghostdav
