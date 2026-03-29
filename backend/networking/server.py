"""
Socket Server - P2P server implementation
First device online becomes the server and routes messages between peers
"""

import socket
import threading
import json
from typing import Dict, Callable, Optional, Tuple
from dataclasses import dataclass
import selectors
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    """Represents an active client connection"""
    client_id: str
    socket: socket.socket
    address: Tuple[str, int]
    connected_at: float
    last_heartbeat: float
    is_authenticated: bool = False


class SocketServer:
    """P2P Socket Server - Router and message relay"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, max_clients: int = 100):
        """
        Initialize socket server
        
        Args:
            host: Bind address
            port: Listen port
            max_clients: Maximum concurrent connections
        """
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.server_socket = None
        self.clients: Dict[str, ClientConnection] = {}
        self.is_running = False
        self.selector = selectors.DefaultSelector()
        self.message_handlers: Dict[str, Callable] = {}
        self.lock = threading.RLock()
        
    def start(self) -> None:
        """Start the server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        
        self.is_running = True
        logger.info(f"Server started on {self.host}:{self.port}")
        
        # Register server socket with selector
        self.selector.register(self.server_socket, selectors.EVENT_READ, data=None)
        
        # Start accept loop
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()
    
    def stop(self) -> None:
        """Stop the server"""
        self.is_running = False
        
        with self.lock:
            for client_conn in self.clients.values():
                try:
                    client_conn.socket.close()
                except:
                    pass
        
        if self.server_socket:
            self.server_socket.close()
        
        self.selector.close()
        logger.info("Server stopped")
    
    def _accept_loop(self) -> None:
        """Main accept loop"""
        while self.is_running:
            try:
                events = self.selector.select(timeout=1.0)
                
                for key, mask in events:
                    if key.data is None:
                        # Server socket - accept new connection
                        self._accept_connection()
                    else:
                        # Client socket - handle data
                        client_conn = key.data
                        self._handle_client_data(client_conn)
            
            except Exception as e:
                logger.error(f"Accept loop error: {e}")
    
    def _accept_connection(self) -> None:
        """Accept a new client connection"""
        try:
            client_socket, address = self.server_socket.accept()
            logger.info(f"New connection from {address}")
            
            # Create client connection object
            client_id = f"{address[0]}:{address[1]}"
            import time
            conn = ClientConnection(
                client_id=client_id,
                socket=client_socket,
                address=address,
                connected_at=time.time(),
                last_heartbeat=time.time()
            )
            
            with self.lock:
                if len(self.clients) < self.max_clients:
                    self.clients[client_id] = conn
                    self.selector.register(client_socket, selectors.EVENT_READ, data=conn)
                else:
                    client_socket.close()
                    logger.warning("Max clients reached")
        
        except Exception as e:
            logger.error(f"Accept error: {e}")
    
    def _handle_client_data(self, client_conn: ClientConnection) -> None:
        """Handle incoming data from a client"""
        try:
            data = client_conn.socket.recv(4096)
            
            if not data:
                # Client disconnected
                self._disconnect_client(client_conn.client_id)
                return
            
            # Parse message
            try:
                message = json.loads(data.decode('utf-8'))
                self._route_message(client_conn, message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_conn.client_id}")
        
        except Exception as e:
            logger.error(f"Data handling error: {e}")
            self._disconnect_client(client_conn.client_id)
    
    def _route_message(self, sender: ClientConnection, message: Dict) -> None:
        """Route message to destination client"""
        msg_type = message.get('type')
        
        # Call registered handler if exists
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](sender, message)
        
        # Check if message is for a specific client
        target_id = message.get('target')
        if target_id and target_id in self.clients:
            target = self.clients[target_id]
            try:
                target.socket.sendall(json.dumps(message).encode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to send to {target_id}: {e}")

    
    def _disconnect_client(self, client_id: str) -> None:
        """Disconnect a client"""
        with self.lock:
            if client_id in self.clients:
                conn = self.clients[client_id]
                self.selector.unregister(conn.socket)
                conn.socket.close()
                del self.clients[client_id]
                logger.info(f"Client {client_id} disconnected")
    
    def register_message_handler(self, msg_type: str, handler: Callable) -> None:
        """Register a handler for a message type"""
        self.message_handlers[msg_type] = handler
    
    def broadcast_message(self, message: Dict, exclude_client: Optional[str] = None) -> None:
        """Broadcast message to all connected clients"""
        with self.lock:
            for client_id, client_conn in self.clients.items():
                if exclude_client and client_id == exclude_client:
                    continue
                
                try:
                    client_conn.socket.sendall(json.dumps(message).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Broadcast error to {client_id}: {e}")
    
    def get_connected_clients_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)
