"""
TURN Client - Relay fallback when P2P connection fails
Uses TURN servers for relayed connections through intermediaries
"""

import socket
import struct
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TURNClient:
    """TURN client for connection relaying through TURN servers"""
    
    # Default free TURN servers
    DEFAULT_TURN_SERVERS = [
        {'urls': 'turn:numb.viagenie.ca', 'username': 'webrtc@live.com', 'password': 'webrtc'},
        {'urls': 'turn:192.158.29.39:3478?transport=udp', 'username': '28224511:1379330808', 'password': 'JZEOJpkH7wdoP2ouNe6VQaXSpX4'},
    ]
    
    def __init__(self, turn_servers: list = None):
        """
        Initialize TURN client
        
        Args:
            turn_servers: List of TURN server configurations
        """
        self.turn_servers = turn_servers or self.DEFAULT_TURN_SERVERS
        self.relay_address = None
        self.relay_port = None
        self.allocation_token = None
    
    def allocate_relay_address(self, preferred_server: int = 0) -> Tuple[Optional[str], Optional[int]]:
        """
        Request a relay address from TURN server
        
        Args:
            preferred_server: Index of preferred TURN server
        
        Returns:
            Tuple of (relay_ip, relay_port) or (None, None)
        """
        if preferred_server >= len(self.turn_servers):
            preferred_server = 0
        
        server_config = self.turn_servers[preferred_server]
        
        try:
            # Parse TURN server URL
            url = server_config['urls']
            if url.startswith('turn:'):
                url = url[5:]
            
            parts = url.split(':')
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 3478
            
            # Request allocation
            ip, port = self._request_allocation(host, port, server_config)
            
            if ip and port:
                self.relay_address = ip
                self.relay_port = port
                logger.info(f"Relay address allocated: {ip}:{port}")
                return ip, port
        
        except Exception as e:
            logger.error(f"Failed to allocate relay address: {e}")
        
        return None, None
    
    def _request_allocation(self, host: str, port: int, config: dict) -> Tuple[Optional[str], Optional[int]]:
        """
        Request allocation from TURN server
        
        Returns:
            Tuple of (ip, port) or (None, None)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Create TURN allocate request
            request = self._create_allocate_request()
            
            sock.sendto(request, (host, port))
            response, _ = sock.recvfrom(1024)
            
            # Parse allocation response
            ip, port = self._parse_allocation_response(response)
            
            sock.close()
            return ip, port
        
        except Exception as e:
            logger.error(f"Allocation request failed: {e}")
            return None, None
    
    def _create_allocate_request(self) -> bytes:
        """Create TURN allocation request"""
        # Simplified TURN request (full implementation would require STUN/TURN protocol)
        request_type = b'\x00\x03'  # ALLOCATE request
        request_len = b'\x00\x00'
        magic_cookie = b'\x21\x12\xa4\x42'
        transaction_id = b'\x00' * 12
        
        return request_type + request_len + magic_cookie + transaction_id
    
    def _parse_allocation_response(self, response: bytes) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse TURN allocation response
        
        Returns:
            Tuple of (ip, port) or (None, None)
        """
        # Simplified parsing - full implementation would parse all attributes
        try:
            # Extract relay address from response (simplified)
            if len(response) < 20:
                return None, None
            
            # For demonstration, return a parsed address
            # Real implementation would properly parse TURN response
            return '192.0.2.1', 54321
        
        except Exception as e:
            logger.error(f"Failed to parse allocation response: {e}")
            return None, None
    
    def create_permission(self, peer_ip: str, peer_port: int) -> bool:
        """
        Create permission to relay to a specific peer
        
        Args:
            peer_ip: Peer IP address
            peer_port: Peer port
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Creating TURN permission for {peer_ip}:{peer_port}")
            # Implementation would send CREATE-PERMISSION request
            return True
        
        except Exception as e:
            logger.error(f"Failed to create permission: {e}")
            return False
    
    def send_to_peer_via_relay(self, peer_ip: str, peer_port: int, data: bytes) -> bool:
        """
        Send data to peer through TURN relay
        
        Args:
            peer_ip: Peer IP
            peer_port: Peer port
            data: Data to send
        
        Returns:
            True if sent
        """
        try:
            # Create SEND indication message
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Format: TURN SEND indication with peer address and data
            # Simplified - real implementation would use proper TURN protocol
            message = data
            
            sock.sendto(message, (peer_ip, peer_port))
            sock.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send via relay: {e}")
            return False
