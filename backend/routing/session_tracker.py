"""
Session Tracker - Tracks active P2P sessions and connections
In-memory session management for the routing layer
"""

import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class SessionState(Enum):
    """Session states"""
    PENDING = "pending"
    ESTABLISHED = "established"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class Session:
    """Represents an active P2P session"""
    session_id: str
    peer1_id: str
    peer2_id: str
    created_at: float
    last_activity: float
    state: SessionState = SessionState.PENDING
    expires_at: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    message_count: int = 0
    bytes_transferred: int = 0


class SessionTracker:
    """Tracks active P2P sessions and communication state"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session tracker
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, Session] = {}
        self.peer_sessions: Dict[str, List[str]] = {}  # peer_id -> list of session_ids
        self.session_timeout = session_timeout
        self.session_counter = 0
    
    def create_session(self, peer1_id: str, peer2_id: str, 
                      metadata: Dict = None) -> str:
        """
        Create a new P2P session
        
        Args:
            peer1_id: First peer ID
            peer2_id: Second peer ID
            metadata: Optional metadata
        
        Returns:
            Session ID
        """
        session_id = f"session_{int(time.time())}_{self.session_counter}"
        self.session_counter += 1
        
        current_time = time.time()
        session = Session(
            session_id=session_id,
            peer1_id=peer1_id,
            peer2_id=peer2_id,
            created_at=current_time,
            last_activity=current_time,
            expires_at=current_time + self.session_timeout,
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        
        # Track session for both peers
        if peer1_id not in self.peer_sessions:
            self.peer_sessions[peer1_id] = []
        if peer2_id not in self.peer_sessions:
            self.peer_sessions[peer2_id] = []
        
        self.peer_sessions[peer1_id].append(session_id)
        self.peer_sessions[peer2_id].append(session_id)
        
        return session_id
    
    def activate_session(self, session_id: str) -> bool:
        """
        Activate a pending session
        
        Args:
            session_id: Session to activate
        
        Returns:
            True if activated
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.state = SessionState.ESTABLISHED
        session.last_activity = time.time()
        return True
    
    def mark_session_active(self, session_id: str) -> bool:
        """
        Mark session as actively communicating
        
        Args:
            session_id: Session ID
        
        Returns:
            True if marked
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if session.state not in [SessionState.ESTABLISHED, SessionState.ACTIVE]:
            return False
        
        session.state = SessionState.ACTIVE
        session.last_activity = time.time()
        return True
    
    def record_message(self, session_id: str, bytes_count: int) -> bool:
        """
        Record message transmission in session
        
        Args:
            session_id: Session ID
            bytes_count: Bytes transferred
        
        Returns:
            True if recorded
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.message_count += 1
        session.bytes_transferred += bytes_count
        session.last_activity = time.time()
        return True
    
    def close_session(self, session_id: str) -> bool:
        """
        Close a session
        
        Args:
            session_id: Session to close
        
        Returns:
            True if closed
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.state = SessionState.CLOSED
        session.last_activity = time.time()
        return True
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information
        
        Args:
            session_id: Session ID
        
        Returns:
            Session info dict or None
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_time = time.time()
        
        return {
            'session_id': session_id,
            'peer1': session.peer1_id,
            'peer2': session.peer2_id,
            'state': session.state.value,
            'duration_seconds': int(current_time - session.created_at),
            'messages': session.message_count,
            'bytes_transferred': session.bytes_transferred,
            'idle_seconds': int(current_time - session.last_activity)
        }
    
    def get_peer_sessions(self, peer_id: str) -> List[dict]:
        """
        Get all sessions for a peer
        
        Args:
            peer_id: Peer ID
        
        Returns:
            List of session info dicts
        """
        if peer_id not in self.peer_sessions:
            return []
        
        sessions = []
        for session_id in self.peer_sessions[peer_id]:
            info = self.get_session_info(session_id)
            if info:
                sessions.append(info)
        
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired = [
            session_id for session_id, session in self.sessions.items()
            if session.expires_at and current_time > session.expires_at
        ]
        
        for session_id in expired:
            session = self.sessions[session_id]
            
            # Cleanup from peer tracking
            for peer_id in [session.peer1_id, session.peer2_id]:
                if peer_id in self.peer_sessions:
                    self.peer_sessions[peer_id].remove(session_id)
            
            del self.sessions[session_id]
        
        return len(expired)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return sum(
            1 for s in self.sessions.values()
            if s.state in [SessionState.ESTABLISHED, SessionState.ACTIVE]
        )
    
    def get_stats(self) -> dict:
        """Get tracker statistics"""
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': self.get_active_sessions_count(),
            'total_peers': len(self.peer_sessions),
            'total_messages': sum(s.message_count for s in self.sessions.values()),
            'total_bytes': sum(s.bytes_transferred for s in self.sessions.values())
        }
