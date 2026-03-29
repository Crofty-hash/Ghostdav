"""
GhostDav Core Configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Server configuration"""
    HOST: str = os.getenv('GHOSTDAV_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('GHOSTDAV_PORT', '8888'))
    MAX_CLIENTS: int = int(os.getenv('GHOSTDAV_MAX_CLIENTS', '100'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'


@dataclass
class P2PConfig:
    """P2P network configuration"""
    LOCAL_PORT: int = int(os.getenv('P2P_PORT', '9999'))
    STUN_SERVERS: list = None
    TURN_SERVERS: list = None
    
    def __post_init__(self):
        if self.STUN_SERVERS is None:
            self.STUN_SERVERS = [
                ('stun.l.google.com', 19302),
                ('stun1.l.google.com', 19302),
            ]
        if self.TURN_SERVERS is None:
            self.TURN_SERVERS = [
                {'urls': 'turn:numb.viagenie.ca', 'username': 'webrtc@live.com', 'password': 'webrtc'},
            ]


@dataclass
class CryptoConfig:
    """Encryption configuration"""
    KEY_SIZE: int = 32  # 256 bits
    NONCE_SIZE: int = 24  # XChaCha20
    ALGORITHM: str = 'ChaCha20-Poly1305'
    KEY_ROTATION_INTERVAL: int = 3600  # 1 hour


@dataclass
class RoutingConfig:
    """Routing configuration"""
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '3600'))
    ALIAS_ROTATION_INTERVAL: int = 300  # 5 minutes
    MAX_ROUTING_HOPS: int = 4
    OBFUSCATION_ENABLED: bool = True
    TRAFFIC_ANALYSIS_RESISTANCE: bool = True


@dataclass
class AppConfig:
    """Application configuration"""
    APP_NAME: str = 'GhostDav'
    VERSION: str = '0.1.0'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Sub-configs
    server: ServerConfig = None
    p2p: P2PConfig = None
    crypto: CryptoConfig = None
    routing: RoutingConfig = None
    
    def __post_init__(self):
        if self.server is None:
            self.server = ServerConfig()
        if self.p2p is None:
            self.p2p = P2PConfig()
        if self.crypto is None:
            self.crypto = CryptoConfig()
        if self.routing is None:
            self.routing = RoutingConfig()


# Global config instance
config = AppConfig()
