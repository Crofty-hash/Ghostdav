"""
Socket Client - Client connection to P2P network
"""

import socket
import json
import threading
import time
from typing import Dict, Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocketClient:
    """Client for connecting to GhostDav network"""
    
    def __init__(self, client_id: str, server_host: str = 'localhost', server_port: int = 8888):
        """
        Initialize client
        
        Args:
            client_id: Unique client identifier
            server_host: Server hostname/IP
            server_port: Server port
        """
        self.client_id = client_id
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self._receive_thread = None
        self._lock = threading.RLock()
    
    def connect(self) -> bool:
        """
        Connect to server
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.is_connected = True
            
            logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
            
            # Send client identification
            self.send_message({'type': 'connect', 'client_id': self.client_id})
            
            # Start receive thread
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            return True
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from server"""
        self.is_connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        logger.info("Disconnected from server")
    
    def send_message(self, message: Dict) -> bool:
        """
        Send a message to the server
        
        Args:
            message: Message dictionary
        
        Returns:
            True if sent, False otherwise
        """
        if not self.is_connected or not self.socket:
            logger.warning("Not connected to server")
            return False
        
        try:
            message_json = json.dumps(message)
            self.socket.sendall(message_json.encode('utf-8'))
            return True
        
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.is_connected = False
            return False
    
    def send_message_to_peer(self, peer_id: str, data: Dict) -> bool:
        """
        Send a message to another peer through the server
        
        Args:
            peer_id: Target peer identifier
            data: Message data
        
        Returns:
            True if sent, False otherwise
        """
        message = {
            'type': 'peer_message',
            'target': peer_id,
            'sender': self.client_id,
            'data': data,
            'timestamp': time.time()
        }
        
        return self.send_message(message)
    
    def _receive_loop(self) -> None:
        """Receive messages from server"""
        buffer = b''
        
        while self.is_connected:
            try:
                data = self.socket.recv(4096)
                
                if not data:
                    self.is_connected = False
                    break
                
                buffer += data
                
                # Try to parse JSON messages
                while buffer:
                    try:
                        message_str, remaining = self._parse_message(buffer)
                        if message_str is None:
                            break
                        
                        buffer = remaining
                        message = json.loads(message_str)
                        self._handle_message(message)
                    
                    except json.JSONDecodeError:
                        break
            
            except Exception as e:
                logger.error(f"Receive error: {e}")
                self.is_connected = False
                break
    
    def _parse_message(self, buffer: bytes) -> tuple:
        """
        Parse a message from buffer (simple newline-delimited)
        
        Returns:
            Tuple of (message_str, remaining_buffer) or (None, buffer)
        """
        try:
            message_str = buffer.decode('utf-8')
            lines = message_str.split('\n', 1)
            if len(lines) == 2:
                return lines[0], lines[1].encode('utf-8')
            return None, buffer
        except:
            return None, buffer
    
    def _handle_message(self, message: Dict) -> None:
        """Handle received message"""
        msg_type = message.get('type')
        
        # Call registered handler if exists
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
        
        logger.debug(f"Received message: {msg_type}")
    
    def register_message_handler(self, msg_type: str, handler: Callable) -> None:
        """Register handler for message type"""
        with self._lock:
            self.message_handlers[msg_type] = handler
