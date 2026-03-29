"""
GhostDav Backend Main Entry Point
P2P Communication Server
"""

import asyncio
import logging
import signal
import sys
from .networking import SocketServer, STUNClient, TURNClient
from .routing import SessionTracker, StageRouter, FakeIPGenerator, AliasManager
from .core import EncryptionManager, KeyManager, Obfuscator, Logger
from .config import config
import base64
import json

# Setup logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GhostDavServer:
    """Main GhostDav P2P Server"""
    
    def __init__(self):
        """Initialize server components"""
        # Core encryption
        self.encryption_manager = EncryptionManager()
        self.key_manager = KeyManager()
        self.obfuscator = Obfuscator()
        
        # Networking
        self.socket_server = SocketServer(
            host=config.server.HOST,
            port=config.server.PORT,
            max_clients=config.server.MAX_CLIENTS
        )
        
        # NAT traversal
        self.stun_client = STUNClient()
        self.turn_client = TURNClient()
        
        # Routing
        self.fake_ip_gen = FakeIPGenerator()
        self.alias_mgr = AliasManager()
        self.session_tracker = SessionTracker(session_timeout=config.routing.SESSION_TIMEOUT)
        self.stage_router = StageRouter(
            obfuscator=self.obfuscator,
            fake_ip_gen=self.fake_ip_gen,
            alias_mgr=self.alias_mgr,
            turn_client=self.turn_client
        )
        
        self.is_running = False
    
    def start(self) -> None:
        """Start the server"""
        logger.info(f"Starting {config.APP_NAME} v{config.VERSION}")
        
        # Discover external address
        logger.info("Discovering external address via STUN...")
        ip, port = self.stun_client.get_external_address()
        if ip:
            logger.info(f"External address: {ip}:{port}")
        else:
            logger.warning("Could not discover external address, using local address")
        
        # Start socket server
        self.socket_server.start()
        self.is_running = True
        
        # Register message handlers
        self._register_handlers()
        
        logger.info(f"Server is ready! Listening on {config.server.HOST}:{config.server.PORT}")
    
    def stop(self) -> None:
        """Stop the server"""
        logger.info("Shutting down server...")
        self.is_running = False
        
        self.socket_server.stop()
        self.session_tracker.cleanup_expired_sessions()
        
        logger.info("Server stopped")
    
    def _register_handlers(self) -> None:
        """Register message handlers"""
        self.socket_server.register_message_handler('connect', self._handle_connect)
        self.socket_server.register_message_handler('disconnect', self._handle_disconnect)
        self.socket_server.register_message_handler('peer_message', self._handle_peer_message)
        self.socket_server.register_message_handler('heartbeat', self._handle_heartbeat)
    
    def _handle_connect(self, sender, message) -> None:
        """Handle client connection"""
        logger.info(f"Client connected: {sender.client_id}")
        sender.is_authenticated = True
    
    def _handle_disconnect(self, sender, message) -> None:
        """Handle client disconnection"""
        logger.info(f"Client disconnecting: {sender.client_id}")
    
    def _handle_peer_message(self, sender, message) -> None:
        """Handle peer-to-peer message relay"""
        target = message.get('target')
        data_b64 = message.get('data')
        nonce_b64 = message.get('nonce')
        
        if not data_b64 or not nonce_b64:
            logger.warning("Missing data or nonce in peer message")
            return
        
        try:
            # Decode base64
            ciphertext = base64.b64decode(data_b64)
            nonce = base64.b64decode(nonce_b64)
            
            # Derive server key (same as demo)
            key, _ = self.encryption_manager.derive_key("demo-password", b'fixed_salt_for_demo')
            
            # Decrypt message
            plaintext = self.encryption_manager.decrypt_message(ciphertext, nonce, key)
            logger.info(f"Decrypted message from {sender.client_id}: {plaintext}")
            
            if target:
                # Route to target
                if target in self.socket_server.clients:
                    # Re-encrypt for target (demo: same key)
                    new_ciphertext, new_nonce = self.encryption_manager.encrypt_message(plaintext, key)
                    response = {
                        'type': 'peer_message',
                        'data': base64.b64encode(new_ciphertext).decode('utf-8'),
                        'nonce': base64.b64encode(new_nonce).decode('utf-8'),
                        'from': sender.client_id
                    }
                    try:
                        self.socket_server.clients[target].socket.sendall(json.dumps(response).encode('utf-8'))
                        logger.info(f"Routed message from {sender.client_id} to {target}")
                    except Exception as e:
                        logger.error(f"Failed to route to {target}: {e}")
                else:
                    logger.warning(f"Target {target} not connected")
            else:
                # Echo back: re-encrypt and send
                print("sender.client_id:", sender.client_id)
                new_ciphertext, new_nonce = self.encryption_manager.encrypt_message(plaintext, key)
                response = {
                    'type': 'peer_message',
                    'data': base64.b64encode(new_ciphertext).decode('utf-8'),
                    'nonce': base64.b64encode(new_nonce).decode('utf-8'),
                    'status': 'echo',
                    'client_id': sender.client_id
                }
                sender.socket.sendall(json.dumps(response).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error handling peer message: {e}", exc_info=True)
    
    def _handle_heartbeat(self, sender, message) -> None:
        """Handle heartbeat from client"""
        import time
        sender.last_heartbeat = time.time()
    
    def run(self) -> None:
        """Run the server (blocking)"""
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.start()
        
        # Keep server running
        try:
            while self.is_running:
                import time
                time.sleep(1)
                
                # Periodic cleanup
                self.session_tracker.cleanup_expired_sessions()
                self.alias_mgr.cleanup_expired_aliases()
                self.stage_router.cleanup_expired_paths()
        
        except KeyboardInterrupt:
            self.stop()


def main():
    """Main entry point"""
    server = GhostDavServer()
    server.run()


if __name__ == '__main__':
    main()
