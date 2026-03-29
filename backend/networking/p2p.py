"""
P2P Module - Peer-to-peer communication handling
Direct peer connections for efficient data transfer
"""

import socket
import threading
from typing import Dict, Callable, Optional
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class P2PManager:
    """Manages direct peer-to-peer connections"""
    
    def __init__(self, local_port: int = 9999):
        """
        Initialize P2P manager
        
        Args:
            local_port: Port to listen for direct P2P connections
        """
        self.local_port = local_port
        self.peer_connections: Dict[str, socket.socket] = {}
        self.listener_socket = None
        self.is_listening = False
        self.message_handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def start_listener(self, host: str = '0.0.0.0') -> bool:
        """
        Start listening for incoming P2P connections
        
        Args:
            host: Bind address
        
        Returns:
            True if successful
        """
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind((host, self.local_port))
            self.listener_socket.listen(5)
            self.is_listening = True
            
            logger.info(f"P2P listener started on {host}:{self.local_port}")
            
            # Start listener thread
            threading.Thread(target=self._listen_loop, daemon=True).start()
            return True
        
        except Exception as e:
            logger.error(f"Failed to start listener: {e}")
            return False
    
    def connect_to_peer(self, peer_id: str, peer_host: str, peer_port: int) -> bool:
        """
        Connect to another peer
        
        Args:
            peer_id: Peer identifier
            peer_host: Peer address
            peer_port: Peer port
        
        Returns:
            True if connection successful
        """
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_host, peer_port))
            
            with self._lock:
                self.peer_connections[peer_id] = peer_socket
            
            logger.info(f"Connected to peer {peer_id} at {peer_host}:{peer_port}")
            
            # Start receiving thread for this peer
            threading.Thread(
                target=self._receive_from_peer,
                args=(peer_id, peer_socket),
                daemon=True
            ).start()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to peer {peer_id}: {e}")
            return False
    
    def send_to_peer(self, peer_id: str, data: Dict) -> bool:
        """
        Send data to a connected peer
        
        Args:
            peer_id: Peer identifier
            data: Data to send
        
        Returns:
            True if sent
        """
        with self._lock:
            if peer_id not in self.peer_connections:
                logger.warning(f"No connection to peer {peer_id}")
                return False
            
            peer_socket = self.peer_connections[peer_id]
        
        try:
            message = json.dumps(data)
            peer_socket.sendall(message.encode('utf-8') + b'\n')
            return True
        
        except Exception as e:
            logger.error(f"Error sending to peer {peer_id}: {e}")
            self._disconnect_peer(peer_id)
            return False
    
    def _listen_loop(self) -> None:
        """Listen for incoming peer connections"""
        while self.is_listening:
            try:
                peer_socket, address = self.listener_socket.accept()
                
                # Receive peer identification
                data = peer_socket.recv(1024)
                peer_id = data.decode('utf-8').strip()
                
                with self._lock:
                    self.peer_connections[peer_id] = peer_socket
                
                logger.info(f"Accepted connection from peer {peer_id}")
                
                # Start receiving thread
                threading.Thread(
                    target=self._receive_from_peer,
                    args=(peer_id, peer_socket),
                    daemon=True
                ).start()
            
            except Exception as e:
                logger.error(f"Listen error: {e}")
    
    def _receive_from_peer(self, peer_id: str, peer_socket: socket.socket) -> None:
        """Receive data from a peer"""
        buffer = b''
        
        while True:
            try:
                data = peer_socket.recv(4096)
                
                if not data:
                    self._disconnect_peer(peer_id)
                    break
                
                buffer += data
                
                # Process complete messages (newline-delimited)
                while b'\n' in buffer:
                    message_str, buffer = buffer.split(b'\n', 1)
                    
                    try:
                        message = json.loads(message_str.decode('utf-8'))
                        self._handle_message(message)
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from peer {peer_id}")
            
            except Exception as e:
                logger.error(f"Receive error from {peer_id}: {e}")
                self._disconnect_peer(peer_id)
                break
    
    def _disconnect_peer(self, peer_id: str) -> None:
        """Disconnect from a peer"""
        with self._lock:
            if peer_id in self.peer_connections:
                try:
                    self.peer_connections[peer_id].close()
                except:
                    pass
                del self.peer_connections[peer_id]
        
        logger.info(f"Disconnected from peer {peer_id}")
    
    def _handle_message(self, message: Dict) -> None:
        """Handle message from peer"""
        msg_type = message.get('type')
        
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
    
    def register_message_handler(self, msg_type: str, handler: Callable) -> None:
        """Register handler for message type"""
        self.message_handlers[msg_type] = handler
    
    def stop(self) -> None:
        """Stop P2P manager"""
        self.is_listening = False
        
        with self._lock:
            for peer_socket in self.peer_connections.values():
                try:
                    peer_socket.close()
                except:
                    pass
            self.peer_connections.clear()
        
        if self.listener_socket:
            self.listener_socket.close()
        
        logger.info("P2P manager stopped")
