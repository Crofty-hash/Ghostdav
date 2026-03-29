"""
Utilities module - Common helper functions for the core engine
"""

import json
import hashlib
import hmac
from typing import Dict, Any, Optional
import base64
import time
from datetime import datetime


def dict_to_bytes(data: Dict[str, Any]) -> bytes:
    """Convert dictionary to JSON bytes"""
    return json.dumps(data).encode('utf-8')


def bytes_to_dict(data: bytes) -> Dict[str, Any]:
    """Convert JSON bytes to dictionary"""
    return json.loads(data.decode('utf-8'))


def hash_data(data: bytes, algorithm: str = 'sha256') -> str:
    """
    Hash data using specified algorithm
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm ('sha256', 'sha512', etc.)
    
    Returns:
        Hex-encoded hash string
    """
    if algorithm == 'sha256':
        return hashlib.sha256(data).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(data).hexdigest()
    elif algorithm == 'md5':
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def verify_hmac(data: bytes, mac: str, key: bytes, algorithm: str = 'sha256') -> bool:
    """
    Verify HMAC signature
    
    Args:
        data: Original data
        mac: HMAC signature to verify
        key: Secret key
        algorithm: Hash algorithm
    
    Returns:
        True if valid, False otherwise
    """
    if algorithm == 'sha256':
        expected_mac = hmac.new(key, data, hashlib.sha256).hexdigest()
    elif algorithm == 'sha512':
        expected_mac = hmac.new(key, data, hashlib.sha512).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return hmac.compare_digest(mac, expected_mac)


def generate_hmac(data: bytes, key: bytes, algorithm: str = 'sha256') -> str:
    """
    Generate HMAC signature
    
    Args:
        data: Data to sign
        key: Secret key
        algorithm: Hash algorithm
    
    Returns:
        Hex-encoded HMAC
    """
    if algorithm == 'sha256':
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    elif algorithm == 'sha512':
        return hmac.new(key, data, hashlib.sha512).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def encode_to_base64(data: bytes) -> str:
    """Safely encode bytes to base64 string"""
    return base64.b64encode(data).decode('utf-8')


def decode_from_base64(data: str) -> bytes:
    """Safely decode base64 string to bytes"""
    return base64.b64decode(data.encode('utf-8'))


def get_current_timestamp() -> float:
    """Get current Unix timestamp"""
    return time.time()


def get_readable_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'


def is_valid_ipv4(ip: str) -> bool:
    """Check if string is valid IPv4 address"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    return True


def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string for logging"""
    if len(text) > max_length:
        return text[:max_length - 3] + '...'
    return text


class Logger:
    """Simple logging utility"""
    
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    
    @staticmethod
    def log(level: str, message: str, module: str = 'GhostDav') -> None:
        """Log a message with timestamp"""
        timestamp = get_readable_timestamp()
        print(f"[{timestamp}] [{module}] {level}: {message}")
    
    @staticmethod
    def debug(message: str, module: str = 'GhostDav') -> None:
        Logger.log(Logger.DEBUG, message, module)
    
    @staticmethod
    def info(message: str, module: str = 'GhostDav') -> None:
        Logger.log(Logger.INFO, message, module)
    
    @staticmethod
    def warning(message: str, module: str = 'GhostDav') -> None:
        Logger.log(Logger.WARNING, message, module)
    
    @staticmethod
    def error(message: str, module: str = 'GhostDav') -> None:
        Logger.log(Logger.ERROR, message, module)
