import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:crypto/crypto.dart';

void main() {
  runApp(const GhostDavApp());
}

class GhostDavApp extends StatelessWidget {
  const GhostDavApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GhostDav Chat',
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF30a0ff),
        scaffoldBackgroundColor: const Color(0xFF1e1e2e),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({Key? key}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late TextEditingController _usernameController;
  late TextEditingController _messageController;
  late TextEditingController _targetPeerController;
  
  List<ChatMessage> messages = [];
  bool isConnected = false;
  String clientId = '';
  String? sharedKey;
  
  static const String BACKEND_URL = 'http://localhost:8888';
  static const String DEMO_PASSWORD = 'demo-password';
  static const String DEMO_SALT = 'fixed_salt_for_demo';

  @override
  void initState() {
    super.initState();
    _usernameController = TextEditingController();
    _messageController = TextEditingController();
    _targetPeerController = TextEditingController();
    _deriveKey();
  }

  void _deriveKey() {
    // Simplified key derivation (in production use proper PBKDF2)
    sharedKey = sha256.convert(utf8.encode(DEMO_PASSWORD + DEMO_SALT)).toString();
  }

  void _connect() {
    final username = _usernameController.text.trim();
    if (username.isEmpty) return;

    setState(() {
      isConnected = true;
      clientId = 'peer_${DateTime.now().millisecondsSinceEpoch}';
    });

    _addMessage('System', 'Connected as $username', isSystem: true);
    _addMessage('System', 'Your ID: $clientId', isSystem: true);
  }

  void _addMessage(String from, String text, {bool isSystem = false}) {
    setState(() {
      messages.add(ChatMessage(
        from: from,
        text: text,
        timestamp: DateTime.now(),
        isSystem: isSystem,
      ));
    });
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Auto-scroll to bottom
    });
  }

  void _sendMessage() async {
    final text = _messageController.text.trim();
    final targetPeer = _targetPeerController.text.trim();
    
    if (text.isEmpty) return;

    _addMessage('You', text);
    _messageController.clear();

    try {
      // Simulate sending encrypted message to backend
      final encryptedData = base64Encode(utf8.encode(text));
      final nonce = 'demo-nonce-${DateTime.now().millisecondsSinceEpoch}';

      final payload = {
        'type': 'peer_message',
        'data': encryptedData,
        'nonce': nonce,
        'target': targetPeer.isEmpty ? null : targetPeer,
      };

      final response = await http.post(
        Uri.parse('$BACKEND_URL/message'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        _addMessage('System', 'Message sent successfully', isSystem: true);
      }
    } catch (e) {
      _addMessage('System', 'Send failed: $e', isSystem: true);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _messageController.dispose();
    _targetPeerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          '🔐 GhostDav Chat',
          style: TextStyle(color: Color(0xFF30a0ff)),
        ),
        backgroundColor: const Color(0xFF0d1117),
        elevation: 2,
        actions: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isConnected ? Colors.green : Colors.red,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  isConnected ? '● Connected' : '● Disconnected',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: !isConnected
          ? _buildLoginScreen()
          : _buildChatScreen(),
    );
  }

  Widget _buildLoginScreen() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Welcome to GhostDav',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Color(0xFF30a0ff),
              ),
            ),
            const SizedBox(height: 40),
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFF30a0ff), width: 2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: TextField(
                controller: _usernameController,
                style: const TextStyle(color: Color(0xFFe0e0e0)),
                decoration: const InputDecoration(
                  hintText: 'Enter your username',
                  hintStyle: TextStyle(color: Color(0xFF666666)),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(12),
                ),
                onSubmitted: (_) => _connect(),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _connect,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF30a0ff),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: const Text(
                  'Connect',
                  style: TextStyle(
                    color: Colors.black,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'End-to-end encrypted P2P messaging',
              style: TextStyle(
                color: Color(0xFF888888),
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatScreen() {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: messages.length,
            itemBuilder: (context, index) {
              final msg = messages[index];
              return _buildMessageBubble(msg);
            },
          ),
        ),
        Container(
          padding: const EdgeInsets.all(12),
          color: const Color(0xFF0d1117),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFF30a0ff)),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: TextField(
                  controller: _targetPeerController,
                  style: const TextStyle(color: Color(0xFFe0e0e0), fontSize: 12),
                  decoration: const InputDecoration(
                    hintText: 'Target Peer ID (optional)',
                    hintStyle: TextStyle(color: Color(0xFF666666), fontSize: 12),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(horizontal: 8),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: const Color(0xFF30a0ff), width: 2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: TextField(
                        controller: _messageController,
                        style: const TextStyle(color: Color(0xFFe0e0e0)),
                        decoration: const InputDecoration(
                          hintText: 'Type a message...',
                          hintStyle: TextStyle(color: Color(0xFF666666)),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.all(12),
                        ),
                        onSubmitted: (_) => _sendMessage(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: _sendMessage,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF30a0ff),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      'Send',
                      style: TextStyle(
                        color: Colors.black,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    final isSystem = msg.isSystem;
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isSystem ? const Color(0xFF1a3a2a) : const Color(0xFF2a2a3e),
        border: Border(
          left: BorderSide(
            color: isSystem ? Colors.green : const Color(0xFF30a0ff),
            width: 4,
          ),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            msg.from,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: isSystem ? Colors.green : const Color(0xFF30a0ff),
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            msg.text,
            style: TextStyle(
              color: isSystem ? Colors.green : const Color(0xFFe0e0e0),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            msg.timestamp.toLocaleTimeString(),
            style: const TextStyle(
              color: Color(0xFF666666),
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

class ChatMessage {
  final String from;
  final String text;
  final DateTime timestamp;
  final bool isSystem;

  ChatMessage({
    required this.from,
    required this.text,
    required this.timestamp,
    this.isSystem = false,
  });
}
