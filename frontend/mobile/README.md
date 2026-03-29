# GhostDav Flutter App

The mobile client for the GhostDav P2P encrypted messaging platform.

## Features

- 🔐 End-to-end encryption using ChaCha20-Poly1305
- 💬 Real-time peer-to-peer messaging
- 📱 Native iOS and Android support
- 🎨 Cyberpunk-themed dark UI
- 🚀 Ultra-fast startup and message delivery

## Prerequisites

- Flutter SDK (3.0+)
- Dart SDK (included with Flutter)
- Android Studio or Xcode (for device emulation/build)
- GhostDav backend running on `localhost:8888`

## Setup

### 1. Install Flutter

```bash
# Download from https://flutter.dev
# Or on macOS:
brew install flutter

# Verify installation
flutter doctor
```

### 2. Clone and Navigate

```bash
cd frontend/mobile
```

### 3. Install Dependencies

```bash
flutter pub get
```

## Build & Run

### Android

```bash
# Get emulator list
flutter emulators

# Launch emulator
flutter emulators --launch Pixel_4_API_30

# Run on emulator
flutter run
```

### iOS

```bash
# Run on iOS simulator
flutter run

# Or on physical device (requires provisioning)
flutter run -d <device_id>
```

### Web (Testing)

```bash
flutter run -d chrome
```

## Architecture

### Main Components

**`lib/main.dart`** - Main chat application
- GhostDavApp: Root widget with Material theme
- ChatScreen: Stateful chat interface
- ChatMessage: Data model for messages

### Key Features

#### Login Screen
- Username input field
- Client ID generation
- System notifications

#### Chat Interface
- Message history with timestamp
- Send button and input field
- Target peer ID field (for directed messages)
- Connection status indicator
- System message display (green)

#### Encryption Integration
- PBKDF2 key derivation (demo simplified)
- ChaCha20 encryption/decryption
- Base64 encoding for transmission
- Nonce-based authentication

### State Management

Uses Flutter's built-in `StatefulWidget` for simplicity. For production, consider:
- Provider
- Riverpod
- GetX
- Bloc

## Configuration

Backend URL configured in `_ChatScreenState`:
```dart
static const String BACKEND_URL = 'http://localhost:8888';
```

To change, update the constant and rebuild.

## Development

### Hot Reload

```bash
flutter run
# Then press 'r' in terminal to hot reload
# Press 'R' to hot restart
```

### Debugging

```bash
# Enable verbose logging
flutter run -v

# Attach debugger to running app
flutter attach
```

### Widget Inspector

```bash
flutter run
# Press 'w' in terminal to open Widget Inspector
```

## Cryptography

### Key Derivation
- Algorithm: PBKDF2-HMAC-SHA256
- Iterations: 100,000 (in backend)
- Salt: `fixed_salt_for_demo` (demo mode)
- Output: 32-byte key

### Encryption
- **Cipher**: ChaCha20-Poly1305 with fallback support
- **Nonce**: 24-byte (XChaCha20) or 12-byte (ChaCha20)
- **Authentication**: Built-in Poly1305 MAC
- **Encoding**: Base64 for JSON transmission

## Building Release APK

```bash
# Build release APK
flutter build apk --release

# Build split APKs for smaller size
flutter build apk --split-per-abi

# Output: build/app/outputs/apk/release/
```

## Building Release IPA

```bash
# Build for iOS
flutter build ios --release

# Deploy via TestFlight or App Store
```

## Troubleshooting

### "Flutter command not found"
```bash
export PATH=$PATH:~/flutter/bin
```

### "ANDROID_SDK_ROOT not set"
```bash
export ANDROID_SDK_ROOT=~/Android/Sdk
```

### "Gradle build failure"
```bash
cd android
./gradlew clean
cd ..
flutter clean && flutter pub get && flutter run
```

### "ios pod install failures"
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
flutter run
```

### "HTTP requests not working on device"
Ensure backend is accessible from device IP (not localhost):
```bash
# Update BACKEND_URL to your machine's IP
static const String BACKEND_URL = 'http://192.168.1.100:8888';
```

## Performance Tips

1. **Use release builds** for testing performance
2. **Profile with DevTools**: `flutter pub global run devtools`
3. **Enable code obfuscation** for production builds
4. **Test on real devices** before release

## License

GhostDav - All Rights Reserved

## Contact

For issues or questions, refer to the main GhostDav repository.
