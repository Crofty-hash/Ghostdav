"""
STUN Client - NAT traversal using STUN (Session Traversal Utilities for NAT)
"""

import socket
import struct
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class STUNClient:
    """STUN client for NAT traversal and external IP discovery"""
    
    # Well-known STUN servers
    DEFAULT_STUN_SERVERS = [
        ('stun.l.google.com', 19302),
        ('stun1.l.google.com', 19302),
        ('stun2.l.google.com', 19302),
        ('stun3.l.google.com', 19302),
    ]
    
    # STUN message types
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    
    def __init__(self, stun_servers: list = None):
        """
        Initialize STUN client
        
        Args:
            stun_servers: List of (host, port) tuples
        """
        self.stun_servers = stun_servers or self.DEFAULT_STUN_SERVERS
        self.public_ip = None
        self.public_port = None
    
    def get_external_address(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Discover external IP and port through STUN
        
        Returns:
            Tuple of (ip, port) or (None, None) if discovery failed
        """
        for stun_host, stun_port in self.stun_servers:
            try:
                ip, port = self._query_stun_server(stun_host, stun_port)
                if ip and port:
                    self.public_ip = ip
                    self.public_port = port
                    logger.info(f"External address discovered: {ip}:{port}")
                    return ip, port
            
            except Exception as e:
                logger.warning(f"STUN query to {stun_host}:{stun_port} failed: {e}")
        
        logger.error("Failed to discover external address via STUN")
        return None, None
    
    def _query_stun_server(self, host: str, port: int) -> Tuple[str, int]:
        """
        Query a STUN server for external address
        
        Returns:
            Tuple of (ip, port)
        """
        # Create STUN binding request
        stun_request = self._create_stun_request()
        
        # Send request
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        try:
            sock.sendto(stun_request, (host, port))
            response, _ = sock.recvfrom(512)
            
            # Parse response
            ip, port = self._parse_stun_response(response)
            return ip, port
        
        finally:
            sock.close()
    
    def _create_stun_request(self) -> bytes:
        """Create STUN binding request message"""
        # STUN message header: type(2) + length(2) + magic cookie(4) + transaction_id(12)
        msg_type = struct.pack('!H', self.BINDING_REQUEST)
        msg_length = struct.pack('!H', 0)  # No attributes
        magic_cookie = b'\x21\x12\xa4\x42'
        transaction_id = b'\x00' * 12
        
        return msg_type + msg_length + magic_cookie + transaction_id
    
    def _parse_stun_response(self, response: bytes) -> Tuple[str, int]:
        """
        Parse STUN response to extract external address
        
        Returns:
            Tuple of (ip, port)
        """
        # Skip header (20 bytes)
        if len(response) < 20:
            raise ValueError("Invalid STUN response")
        
        # Parse attributes
        offset = 20
        while offset < len(response):
            attr_type, attr_len = struct.unpack('!HH', response[offset:offset + 4])
            offset += 4
            
            # XOR-MAPPED-ADDRESS (0x0020)
            if attr_type == 0x0020:
                return self._parse_xor_address(response[offset:offset + attr_len])
            
            # MAPPED-ADDRESS (0x0001)
            elif attr_type == 0x0001:
                return self._parse_address(response[offset:offset + attr_len])
            
            # Skip to next attribute (with padding)
            offset += (attr_len + 3) & ~3
        
        raise ValueError("No address attribute in STUN response")
    
    def _parse_address(self, data: bytes) -> Tuple[str, int]:
        """Parse MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            raise ValueError("Invalid address attribute")
        
        family = data[1]  # IPv4=1, IPv6=2
        port = struct.unpack('!H', data[2:4])[0]
        
        if family == 1:  # IPv4
            ip = '.'.join(str(b) for b in data[4:8])
            return ip, port
        
        raise ValueError(f"Unsupported address family: {family}")
    
    def _parse_xor_address(self, data: bytes) -> Tuple[str, int]:
        """Parse XOR-MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            raise ValueError("Invalid XOR address attribute")
        
        family = data[1]
        xor_port = struct.unpack('!H', data[2:4])[0]
        magic_cookie = 0x2112a442
        
        # XOR the port
        port = xor_port ^ (magic_cookie >> 16)
        
        if family == 1:  # IPv4
            xor_ip_bytes = data[4:8]
            magic_bytes = struct.pack('!I', magic_cookie)
            ip_bytes = bytes(a ^ b for a, b in zip(xor_ip_bytes, magic_bytes))
            ip = '.'.join(str(b) for b in ip_bytes)
            return ip, port
        
        raise ValueError(f"Unsupported address family: {family}")
