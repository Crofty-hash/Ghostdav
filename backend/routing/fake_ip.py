"""
Fake IP Generator - Generates untraceable routing IDs
Creates fake IP addresses for routing layer obfuscation
"""

import random
import re
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class FakeIP:
    """Represents a fake IP assignment"""
    fake_ip: str
    real_peer_id: str
    created_at: float
    expires_at: Optional[float] = None


class FakeIPGenerator:
    """Generates and manages fake IP addresses for routing"""
    
    # Reserved IP ranges to avoid
    RESERVED_RANGES = [
        ('0.0.0.0', '0.255.255.255'),
        ('10.0.0.0', '10.255.255.255'),
        ('127.0.0.0', '127.255.255.255'),
        ('169.254.0.0', '169.254.255.255'),
        ('172.16.0.0', '172.31.255.255'),
        ('192.0.0.0', '192.0.2.255'),
        ('192.168.0.0', '192.168.255.255'),
        ('224.0.0.0', '255.255.255.255'),
    ]
    
    def __init__(self):
        """Initialize fake IP generator"""
        self.assignments: dict = {}  # fake_ip -> real_peer_id
        self.reverse_lookup: dict = {}  # real_peer_id -> fake_ip
    
    def generate_fake_ip(self, peer_id: str) -> str:
        """
        Generate a fake IP for a peer
        
        Args:
            peer_id: Real peer identifier
        
        Returns:
            Generated fake IP address
        """
        # Check if already assigned
        if peer_id in self.reverse_lookup:
            return self.reverse_lookup[peer_id]
        
        # Generate random IP outside reserved ranges
        while True:
            fake_ip = self._generate_random_ip()
            
            if fake_ip not in self.assignments:
                self.assignments[fake_ip] = peer_id
                self.reverse_lookup[peer_id] = fake_ip
                return fake_ip
    
    def resolve_peer_id(self, fake_ip: str) -> Optional[str]:
        """
        Get real peer ID from fake IP
        
        Args:
            fake_ip: Fake IP address
        
        Returns:
            Real peer ID or None if not found
        """
        return self.assignments.get(fake_ip)
    
    def resolve_fake_ip(self, peer_id: str) -> Optional[str]:
        """
        Get fake IP for a peer
        
        Args:
            peer_id: Real peer ID
        
        Returns:
            Fake IP or None if not assigned
        """
        return self.reverse_lookup.get(peer_id)
    
    def revoke_fake_ip(self, fake_ip: str) -> bool:
        """
        Revoke a fake IP assignment
        
        Args:
            fake_ip: Fake IP to revoke
        
        Returns:
            True if revoked, False if not found
        """
        if fake_ip in self.assignments:
            peer_id = self.assignments[fake_ip]
            del self.assignments[fake_ip]
            del self.reverse_lookup[peer_id]
            return True
        return False
    
    def revoke_peer_assignment(self, peer_id: str) -> bool:
        """
        Revoke fake IP for a specific peer
        
        Args:
            peer_id: Peer to revoke
        
        Returns:
            True if revoked
        """
        if peer_id in self.reverse_lookup:
            fake_ip = self.reverse_lookup[peer_id]
            return self.revoke_fake_ip(fake_ip)
        return False
    
    def get_all_assignments(self) -> dict:
        """Get all active fake IP assignments"""
        return self.assignments.copy()
    
    @staticmethod
    def _generate_random_ip() -> str:
        """
        Generate a random IP address outside reserved ranges
        
        Returns:
            Random IP address string
        """
        while True:
            octets = [random.randint(0, 255) for _ in range(4)]
            ip = '.'.join(str(o) for o in octets)
            
            if not FakeIPGenerator._is_reserved(ip):
                return ip
    
    @staticmethod
    def _is_reserved(ip: str) -> bool:
        """Check if IP is in reserved range"""
        octets = [int(x) for x in ip.split('.')]
        
        for start_str, end_str in FakeIPGenerator.RESERVED_RANGES:
            start_octets = [int(x) for x in start_str.split('.')]
            end_octets = [int(x) for x in end_str.split('.')]
            
            if all(s <= o <= e for s, o, e in zip(start_octets, octets, end_octets)):
                return True
        
        return False
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Check if string is valid IPv4 format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        octets = [int(x) for x in ip.split('.')]
        return all(0 <= o <= 255 for o in octets)
