# GhostDav Desktop Client

End-to-end encrypted P2P messaging desktop application built with React and Electron.

## Setup

1. Install dependencies:
```bash
cd frontend/desktop
npm install
```

2. Start the backend server:
```bash
# In another terminal
cd /path/to/GhostDav
python3 -m backend.main
```

3. Start the dev client:
```bash
npm run dev
```

Or run both together:
```bash
npm start
```

## Features

- **Encrypted Messaging**: All messages are end-to-end encrypted using XChaCha20-Poly1305
- **P2P Communication**: Direct peer-to-peer messaging with server routing
- **User Identification**: Connect with a username
- **Peer Targeting**: Send messages to specific peer IDs
- **Modern UI**: Dark theme with cyberpunk aesthetic

## Building

```bash
npm run build
```

This creates a distributable Electron app in the `dist` folder.

## Architecture

- **Frontend**: React 18 with Vite
- **Desktop Framework**: Electron 28
- **Encryption**: Socket-based communication with server-side encryption handling
- **Backend**: Python backend at `localhost:8888`

## Environment

Default connection:
- Backend URL: `http://localhost:8888`
- Encryption Key: Demo password with fixed salt

For production, update these in `src/ChatApp.jsx`.
