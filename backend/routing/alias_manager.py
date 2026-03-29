"""
Alias Manager - Random endpoint masking
Maps peers to temporary aliases for identity obfuscation during routing
"""

import secrets
import string
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Alias:
    """Represents a peer alias"""
    alias: str
    peer_id: str
    created_at: float
    expires_at: Optional[float] = None
    rotation_count: int = 0


class AliasManager:
    """Manages dynamic aliases for endpoint masking"""
    
    def __init__(self, alias_length: int = 16, rotation_interval: int = 300):
        """
        Initialize alias manager
        
        Args:
            alias_length: Length of generated aliases
            rotation_interval: Seconds before alias rotation
        """
        self.alias_length = alias_length
        self.rotation_interval = rotation_interval
        self.aliases: Dict[str, Alias] = {}  # alias -> Alias object
        self.peer_aliases: Dict[str, str] = {}  # peer_id -> current alias
    
    def generate_alias(self, peer_id: str) -> str:
        """
        Generate a new alias for a peer
        
        Args:
            peer_id: Peer identifier
        
        Returns:
            Generated alias string
        """
        # Check if peer already has active alias
        if peer_id in self.peer_aliases:
            current_alias = self.peer_aliases[peer_id]
            if current_alias in self.aliases:
                alias_obj = self.aliases[current_alias]
                if not alias_obj.expires_at or time.time() < alias_obj.expires_at:
                    return current_alias
        
        # Generate new unique alias
        while True:
            alias = self._generate_random_alias()
            if alias not in self.aliases:
                break
        
        # Create alias object
        current_time = time.time()
        alias_obj = Alias(
            alias=alias,
            peer_id=peer_id,
            created_at=current_time,
            expires_at=current_time + self.rotation_interval
        )
        
        self.aliases[alias] = alias_obj
        self.peer_aliases[peer_id] = alias
        
        return alias
    
    def resolve_peer_id(self, alias: str) -> Optional[str]:
        """
        Resolve alias to peer ID
        
        Args:
            alias: Alias to resolve
        
        Returns:
            Peer ID or None if not found or expired
        """
        if alias not in self.aliases:
            return None
        
        alias_obj = self.aliases[alias]
        
        # Check if expired
        if alias_obj.expires_at and time.time() > alias_obj.expires_at:
            self._revoke_alias(alias)
            return None
        
        return alias_obj.peer_id
    
    def rotate_alias(self, peer_id: str) -> str:
        """
        Rotate (refresh) an alias for a peer
        
        Args:
            peer_id: Peer to rotate alias for
        
        Returns:
            New alias
        """
        # Revoke old alias if exists
        if peer_id in self.peer_aliases:
            old_alias = self.peer_aliases[peer_id]
            self._revoke_alias(old_alias)
        
        # Generate new alias
        return self.generate_alias(peer_id)
    
    def revoke_peer_aliases(self, peer_id: str) -> bool:
        """
        Revoke all aliases for a peer
        
        Args:
            peer_id: Peer to revoke
        
        Returns:
            True if revoked
        """
        if peer_id in self.peer_aliases:
            alias = self.peer_aliases[peer_id]
            return self._revoke_alias(alias)
        return False
    
    def cleanup_expired_aliases(self) -> int:
        """
        Remove expired aliases
        
        Returns:
            Number of aliases cleaned up
        """
        current_time = time.time()
        expired = [
            alias for alias, obj in self.aliases.items()
            if obj.expires_at and current_time > obj.expires_at
        ]
        
        for alias in expired:
            self._revoke_alias(alias)
        
        return len(expired)
    
    def _revoke_alias(self, alias: str) -> bool:
        """Internal method to revoke an alias"""
        if alias in self.aliases:
            alias_obj = self.aliases[alias]
            if alias_obj.peer_id in self.peer_aliases:
                del self.peer_aliases[alias_obj.peer_id]
            del self.aliases[alias]
            return True
        return False
    
    @staticmethod
    def _generate_random_alias() -> str:
        """Generate random alias string"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(16))
    
    def get_stats(self) -> dict:
        """Get alias manager statistics"""
        current_time = time.time()
        active_count = sum(
            1 for a in self.aliases.values()
            if not a.expires_at or current_time < a.expires_at
        )
        
        return {
            'total_aliases': len(self.aliases),
            'active_aliases': active_count,
            'total_peers': len(self.peer_aliases),
        }
