# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────┐
│                    GhostDav Network                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐              ┌──────────────┐        │
│  │  Mobile      │              │  Desktop     │        │
│  │  (Flutter)   │──────────────│  (Electron)  │        │
│  │              │              │              │        │
│  └──────────────┘              └──────────────┘        │
│        │                               │                │
│        └───────────────┬───────────────┘                │
│                        │                                │
│                        ▼                                │
│        ┌───────────────────────────────┐               │
│        │      P2P Server Node          │               │
│        │  (First device online)        │               │
│        │                               │               │
│        │ ┌─────────────────────────┐  │               │
│        │ │ Socket Server (8888)    │  │               │
│        │ ├─────────────────────────┤  │               │
│        │ │ Routing Layer           │  │               │
│        │ ├─────────────────────────┤  │               │
│        │ │ Session Tracker         │  │               │
│        │ └─────────────────────────┘  │               │
│        └───────────────────────────────┘               │
│                        │                                │
│                   NAT Traversal                         │
│         (STUN for discovery, TURN for relay)          │
│                        │                                │
│        ┌────────────────────────────┐                 │
│        │  External Internet         │                 │
│        │  (Optional TURN servers)   │                 │
│        └────────────────────────────┘                 │
│                                                        │
└─────────────────────────────────────────────────────────┘
```

## Backend Architecture

### Core Modules

**1. Encryption Layer** (`backend/core/`)
- Symmetric encryption: ChaCha20-Poly1305 (AEAD)
- Key management with automatic rotation
- Message obfuscation with padding + noise

**2. Networking Layer** (`backend/networking/`)
- Socket server for peer management
- Socket client for peer connections
- P2P direct communication
- NAT traversal (STUN/TURN)

**3. Routing Layer** (`backend/routing/`)
- 4-stage routing (obfuscation → fake IP → alias → relay)
- Fake IP generation for anonymity
- Dynamic alias management
- Session tracking

**4. Steganography** (`backend/stego/`)
- LSB embedding in images
- Data extraction from steganographic images
- Capacity analysis

**5. Media Handling** (`backend/media/`)
- Audio: Codec support (OPUS, PCM, etc.)
- Video: Codec support (VP9, H264, etc.)
- Real-time streaming

## Data Flow

### Sending a Message

```
User Input
    ↓
[Compression]
    ↓
[Session Key Selection]
    ↓
[Encryption with ChaCha20-Poly1305]
    ↓
[Obfuscation Layer 1 - Padding + Noise]
    ↓
[Fake IP Assignment Layer 2]
    ↓
[Alias Mapping Layer 3]
    ↓
[Optional Steganography] → Hide in Image
    ↓
[TURN Relay Layer 4] ← If needed
    ↓
[Network Transmission]
```

### Receiving a Message

```
[Network Reception]
    ↓
[Relay Unwrapping] ← If relayed
    ↓
[Alias Resolution Layer 3]
    ↓
[Fake IP Resolution Layer 2]
    ↓
[Deobfuscation Layer 1]
    ↓
[Steganography Extraction] ← If hidden
    ↓
[Decryption with Session Key]
    ↓  
[Decompression]
    ↓
User Display
```

## Security Properties

### Encryption
- **Algorithm**: ChaCha20-Poly1305 (modern, fast, secure)
- **Key Size**: 256 bits
- **Forward Secrecy**: Keys rotate hourly
- **Authentication**: Built-in with AEAD

### Anonymity
- **Fake IPs**: Untraceable routing identifiers
- **Aliases**: Temporary endpoint masks
- **Multi-hop**: Messages bounce through peers
- **Obfuscation**: Constant-size padding prevents traffic analysis

### P2P
- **Decentralized**: No central server required
- **Self-Healing**: Works even if nodes go offline
- **Direct**: Peer-to-peer when possible
- **Relayed**: Falls back to TURN when P2P blocked

## Performance Considerations

### Optimizations
- C++ core engine for crypto and steganography
- Async I/O for networking
- Connection pooling
- Message batching

### Scalability
- Horizontal scaling with multiple server nodes
- Load balancing via distributed routing
- Caching for frequently accessed data
- Cleanup of expired sessions/keys

## Future Enhancements

- [ ] Blockchain-based peer discovery
- [ ] Distributed hash table (DHT) for peer lookup
- [ ] Hardware acceleration (GPU crypto)
- [ ] Post-quantum cryptography
- [ ] Multi-hop onion routing
- [ ] Reputation system for peer selection

---

See [protocols/ghostdav_protocol.md](../protocols/ghostdav_protocol.md) for protocol details.
