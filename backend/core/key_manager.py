"""
Key Manager - Handles session keys and ephemeral key generation
Manages the lifecycle of encryption keys with automatic rotation
"""

import os
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timedelta


@dataclass
class SessionKey:
    """Represents a session encryption key"""
    key: bytes
    session_id: str
    created_at: float
    expires_at: float
    is_active: bool = True
    peer_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if key has expired"""
        return time.time() > self.expires_at


class KeyManager:
    """Manages ephemeral session keys with rotation"""
    
    def __init__(self, key_rotation_interval: int = 3600):
        """
        Initialize key manager
        
        Args:
            key_rotation_interval: Time in seconds before key rotation (default: 1 hour)
        """
        self.keys: Dict[str, SessionKey] = {}
        self.rotation_interval = key_rotation_interval
        self.master_key = secrets.token_bytes(32)  # Master key for key derivation
        
    def generate_session_key(self, session_id: str, peer_id: Optional[str] = None) -> SessionKey:
        """
        Generate a new session key
        
        Args:
            session_id: Unique identifier for this session
            peer_id: Optional peer identifier
        
        Returns:
            SessionKey object
        """
        key = secrets.token_bytes(32)  # 256-bit key
        current_time = time.time()
        expires_at = current_time + self.rotation_interval
        
        session_key = SessionKey(
            key=key,
            session_id=session_id,
            created_at=current_time,
            expires_at=expires_at,
            peer_id=peer_id
        )
        
        self.keys[session_id] = session_key
        return session_key
    
    def get_session_key(self, session_id: str) -> Optional[bytes]:
        """
        Retrieve a session key
        
        Args:
            session_id: Session identifier
        
        Returns:
            The key bytes if valid, None if expired or not found
        """
        session_key = self.keys.get(session_id)
        
        if session_key is None:
            return None
        
        if session_key.is_expired():
            self.revoke_key(session_id)
            return None
        
        return session_key.key
    
    def rotate_key(self, session_id: str) -> Optional[SessionKey]:
        """
        Rotate an existing session key
        
        Args:
            session_id: Session to rotate
        
        Returns:
            New SessionKey or None if session not found
        """
        old_session = self.keys.get(session_id)
        if old_session is None:
            return None
        
        # Create new key with same peer_id
        new_session = self.generate_session_key(session_id, old_session.peer_id)
        return new_session
    
    def revoke_key(self, session_id: str) -> bool:
        """
        Revoke a session key immediately
        
        Args:
            session_id: Session to revoke
        
        Returns:
            True if revoked, False if not found
        """
        if session_id in self.keys:
            self.keys[session_id].is_active = False
            del self.keys[session_id]
            return True
        return False
    
    def cleanup_expired_keys(self) -> int:
        """
        Remove all expired keys
        
        Returns:
            Number of keys cleaned up
        """
        expired_sessions = [
            sid for sid, skey in self.keys.items() 
            if skey.is_expired()
        ]
        
        for session_id in expired_sessions:
            del self.keys[session_id]
        
        return len(expired_sessions)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return sum(1 for key in self.keys.values() if key.is_active)
    
    def derive_key_from_master(self, salt: bytes) -> bytes:
        """
        Derive a key from master key using salt
        
        Args:
            salt: Random salt for key derivation
        
        Returns:
            Derived key bytes
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'ghostdav-key-derivation'
        )
        return hkdf.derive(self.master_key)
