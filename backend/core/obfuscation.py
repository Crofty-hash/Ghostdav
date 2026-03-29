"""
Obfuscation module - Padding and noise injection for traffic analysis resistance
Implements constant-size padding and random noise to prevent pattern detection
"""

import os
import secrets
from typing import Tuple
import struct


class Obfuscator:
    """Handles message obfuscation through padding and noise injection"""
    
    # Predefined padding sizes to prevent traffic analysis
    STANDARD_SIZES = [512, 1024, 2048, 4096, 8192, 16384]
    
    @staticmethod
    def add_padding(data: bytes, target_size: int = None) -> Tuple[bytes, int]:
        """
        Add PKCS7 padding to data, optionally to a specific size
        
        Args:
            data: Input data to pad
            target_size: Optional target size (will choose next standard size if not provided)
        
        Returns:
            Tuple of (padded_data, original_length)
        """
        original_length = len(data)
        
        if target_size is None:
            # Choose next standard size that fits
            target_size = Obfuscator.get_suitable_size(original_length)
        
        # Add PKCS7 padding
        padding_length = target_size - original_length
        if padding_length <= 0:
            padding_length = target_size
            target_size = original_length + target_size
        
        padding = bytes([padding_length]) * padding_length
        padded_data = data + padding
        
        return padded_data, original_length
    
    @staticmethod
    def remove_padding(padded_data: bytes) -> bytes:
        """
        Remove PKCS7 padding from data
        
        Args:
            padded_data: Padded data
        
        Returns:
            Original unpadded data
        """
        if not padded_data:
            return padded_data
        
        padding_length = padded_data[-1]
        
        # Validate padding
        if padding_length > len(padded_data) or padding_length == 0:
            return padded_data
        
        # Check all padding bytes are correct (constant-time)
        for i in range(padding_length):
            if padded_data[-(i + 1)] != padding_length:
                return padded_data
        
        return padded_data[:-padding_length]
    
    @staticmethod
    def add_noise(data: bytes, noise_ratio: float = 0.1) -> bytes:
        """
        Add random noise to data to break patterns
        
        Args:
            data: Input data
            noise_ratio: Proportion of noise to add (0.0-1.0)
        
        Returns:
            Data with noise injected
        """
        if noise_ratio <= 0 or noise_ratio >= 1:
            return data
        
        noise_size = int(len(data) * noise_ratio)
        noise = os.urandom(noise_size)
        
        # Insert noise at random positions
        insertion_point = secrets.randbelow(len(data)) if data else 0
        result = data[:insertion_point] + noise + data[insertion_point:]
        
        return result
    
    @staticmethod
    def extract_noise(data_with_noise: bytes, original_size: int, noise_ratio: float = 0.1) -> bytes:
        """
        Extract original data from noisy data (requires metadata about noise)
        
        Note: This requires prior knowledge of where noise was inserted.
        For real implementation, store noise metadata in header.
        
        Args:
            data_with_noise: Data with injected noise
            original_size: Size of original data before noise
            noise_ratio: Proportion of noise that was added
        
        Returns:
            Original data (best effort)
        """
        # This is simplified - real implementation would need metadata
        # For now, assume noise is appended
        expected_noise_size = int(original_size * noise_ratio)
        return data_with_noise[:-expected_noise_size]
    
    @staticmethod
    def get_suitable_size(data_size: int) -> int:
        """
        Get the next suitable standard size for constant-size padding
        
        Args:
            data_size: Size of data to be padded
        
        Returns:
            Next standard size that can accommodate the data
        """
        for size in Obfuscator.STANDARD_SIZES:
            if data_size <= size:
                return size
        
        # If data exceeds all standard sizes, round to next multiple of 8192
        return ((data_size // 8192) + 1) * 8192
    
    @staticmethod
    def create_obfuscated_packet(data: bytes, add_random_noise: bool = True) -> bytes:
        """
        Create a fully obfuscated packet with padding and optionally noise
        
        Args:
            data: Original message data
            add_random_noise: Whether to inject random noise
        
        Returns:
            Obfuscated packet ready for transmission
        """
        # Add padding
        padded_data, original_length = Obfuscator.add_padding(data)
        
        # Store original length in a 4-byte header
        length_bytes = struct.pack('>I', original_length)
        
        # Add noise if desired
        if add_random_noise:
            padded_data = Obfuscator.add_noise(padded_data, noise_ratio=0.05)
        
        return length_bytes + padded_data
    
    @staticmethod
    def extract_obfuscated_packet(packet: bytes) -> bytes:
        """
        Extract original data from an obfuscated packet
        
        Args:
            packet: Obfuscated packet
        
        Returns:
            Original data
        """
        if len(packet) < 4:
            return b''
        
        # Read original length
        original_length = struct.unpack('>I', packet[:4])[0]
        
        # Extract data (remove header)
        data_with_padding = packet[4:]
        
        # Remove padding
        data = Obfuscator.remove_padding(data_with_padding)
        
        # Trim to original length
        return data[:original_length]


class TrafficAnalysisResistance:
    """Additional measures to resist traffic analysis"""
    
    @staticmethod
    def generate_decoys(target_size: int, count: int = 1) -> list:
        """
        Generate decoy packets of random size to mix with real traffic
        
        Args:
            target_size: Target size for decoys
            count: Number of decoys to generate
        
        Returns:
            List of decoy byte packets
        """
        decoys = []
        for _ in range(count):
            # Random size between 50% and target_size
            size = secrets.randbelow(target_size // 2, target_size)
            decoy = os.urandom(size)
            decoys.append(decoy)
        
        return decoys
    
    @staticmethod
    def add_timing_obfuscation(send_func, delay_range: Tuple[float, float] = (0.1, 1.0)):
        """
        Wrapper to add random delays to message sending to resist timing analysis
        
        Args:
            send_func: Function that sends data
            delay_range: Tuple of (min_delay, max_delay) in seconds
        
        Returns:
            Wrapped function with timing obfuscation
        """
        import time
        import random
        
        def _send_with_delay(data):
            delay = random.uniform(*delay_range)
            time.sleep(delay)
            return send_func(data)
        
        return _send_with_delay
