"""
Packet Builder - Wraps messages for each routing stage
Builds layered packets with obfuscation, fake IPs, aliases, and relay headers
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
import json
import base64
import time
from .fake_ip import FakeIPGenerator
from .alias_manager import AliasManager


@dataclass
class PacketLayer:
    """Represents a single layer in the packet"""
    layer_type: str  # 'obfuscation', 'fake_ip', 'alias', 'relay'
    headers: Dict[str, Any]
    payload: bytes
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class PacketBuilder:
    """Builds multi-layer packets for routing stages"""
    
    def __init__(self, fake_ip_gen: Optional[FakeIPGenerator] = None,
                 alias_mgr: Optional[AliasManager] = None):
        """
        Initialize packet builder
        
        Args:
            fake_ip_gen: Fake IP generator instance
            alias_mgr: Alias manager instance
        """
        self.fake_ip_gen = fake_ip_gen
        self.alias_mgr = alias_mgr
    
    def build_stage1_packet(self, message_data: bytes, obfuscation_params: Optional[Dict] = None) -> PacketLayer:
        """
        Build Stage 1: Obfuscation layer
        Adds padding and noise to constant-size packets
        
        Args:
            message_data: Raw message data
            obfuscation_params: Obfuscation parameters
        
        Returns:
            PacketLayer for stage 1
        """
        if obfuscation_params is None:
            obfuscation_params = {}
        
        # Add padding to make constant size (e.g., 1024 bytes)
        target_size = obfuscation_params.get('target_size', 1024)
        padding_size = max(0, target_size - len(message_data))
        padding = b'\x00' * padding_size
        
        # Add noise (random bytes)
        noise_size = obfuscation_params.get('noise_size', 64)
        import os
        noise = os.urandom(noise_size)
        
        payload = message_data + padding + noise
        
        headers = {
            'stage': 1,
            'type': 'obfuscation',
            'original_size': len(message_data),
            'padding_size': padding_size,
            'noise_size': noise_size,
            'timestamp': time.time()
        }
        
        return PacketLayer(
            layer_type='obfuscation',
            headers=headers,
            payload=payload
        )
    
    def build_stage2_packet(self, inner_packet: PacketLayer, destination_peer: str) -> PacketLayer:
        """
        Build Stage 2: Fake IP layer
        Assigns untraceable fake IP addresses
        
        Args:
            inner_packet: Inner packet from stage 1
            destination_peer: Destination peer ID
        
        Returns:
            PacketLayer for stage 2
        """
        if not self.fake_ip_gen:
            raise ValueError("Fake IP generator not provided")
        
        fake_ip = self.fake_ip_gen.generate_fake_ip(destination_peer)
        
        headers = {
            'stage': 2,
            'type': 'fake_ip',
            'fake_ip': fake_ip,
            'real_destination': destination_peer,
            'timestamp': time.time()
        }
        
        # Wrap the inner packet
        wrapped_payload = self._wrap_packet(inner_packet, headers)
        
        return PacketLayer(
            layer_type='fake_ip',
            headers=headers,
            payload=wrapped_payload
        )
    
    def build_stage3_packet(self, inner_packet: PacketLayer, destination_peer: str) -> PacketLayer:
        """
        Build Stage 3: Alias layer
        Maps to temporary aliases for identity masking
        
        Args:
            inner_packet: Inner packet from stage 2
            destination_peer: Destination peer ID
        
        Returns:
            PacketLayer for stage 3
        """
        if not self.alias_mgr:
            raise ValueError("Alias manager not provided")
        
        alias = self.alias_mgr.generate_alias(destination_peer)
        
        headers = {
            'stage': 3,
            'type': 'alias',
            'alias': alias,
            'real_destination': destination_peer,
            'timestamp': time.time()
        }
        
        # Wrap the inner packet
        wrapped_payload = self._wrap_packet(inner_packet, headers)
        
        return PacketLayer(
            layer_type='alias',
            headers=headers,
            payload=wrapped_payload
        )
    
    def build_stage4_packet(self, inner_packet: PacketLayer, relay_hops: list) -> PacketLayer:
        """
        Build Stage 4: Relay layer
        Prepares for multi-hop TURN relay routing
        
        Args:
            inner_packet: Inner packet from stage 3
            relay_hops: List of relay hop addresses
        
        Returns:
            PacketLayer for stage 4
        """
        headers = {
            'stage': 4,
            'type': 'relay',
            'hops': relay_hops,
            'current_hop': 0,
            'timestamp': time.time()
        }
        
        # Wrap the inner packet
        wrapped_payload = self._wrap_packet(inner_packet, headers)
        
        return PacketLayer(
            layer_type='relay',
            headers=headers,
            payload=wrapped_payload
        )
    
    def build_complete_packet(self, message_data: bytes, destination_peer: str,
                            relay_hops: Optional[list] = None) -> PacketLayer:
        """
        Build a complete 4-stage packet
        
        Args:
            message_data: Raw message data
            destination_peer: Final destination peer
            relay_hops: Optional relay hops for stage 4
        
        Returns:
            Complete 4-layer packet
        """
        # Stage 1: Obfuscation
        stage1 = self.build_stage1_packet(message_data)
        
        # Stage 2: Fake IP
        stage2 = self.build_stage2_packet(stage1, destination_peer)
        
        # Stage 3: Alias
        stage3 = self.build_stage3_packet(stage2, destination_peer)
        
        # Stage 4: Relay
        if relay_hops is None:
            relay_hops = []
        stage4 = self.build_stage4_packet(stage3, relay_hops)
        
        return stage4
    
    def unwrap_packet(self, packet: PacketLayer) -> Dict[str, Any]:
        """
        Unwrap a packet layer by layer to extract original message
        
        Args:
            packet: Packet to unwrap
        
        Returns:
            Dictionary with unwrapped data and metadata
        """
        current_packet = packet
        layers = []
        
        # Unwrap all layers
        while current_packet:
            layers.append({
                'type': current_packet.layer_type,
                'headers': current_packet.headers
            })
            
            # Try to unwrap inner packet
            inner_data = self._unwrap_packet(current_packet)
            if inner_data:
                current_packet = inner_data.get('packet')
            else:
                break
        
        return {
            'layers': layers,
            'original_message': current_packet.payload if current_packet else None
        }
    
    def _wrap_packet(self, inner_packet: PacketLayer, headers: Dict) -> bytes:
        """
        Wrap an inner packet with headers
        
        Args:
            inner_packet: Inner packet to wrap
            headers: Headers to add
        
        Returns:
            Wrapped payload bytes
        """
        header_json = json.dumps(headers).encode('utf-8')
        header_size = len(header_json)
        
        # Format: [header_size (4 bytes)] [header_json] [inner_payload]
        return (
            header_size.to_bytes(4, 'big') +
            header_json +
            inner_packet.payload
        )
    
    def _unwrap_packet(self, packet: PacketLayer) -> Optional[Dict]:
        """
        Unwrap a single packet layer
        
        Args:
            packet: Packet to unwrap
        
        Returns:
            Unwrapped data or None
        """
        if len(packet.payload) < 4:
            return None
        
        header_size = int.from_bytes(packet.payload[:4], 'big')
        if len(packet.payload) < 4 + header_size:
            return None
        
        header_json = packet.payload[4:4 + header_size]
        inner_payload = packet.payload[4 + header_size:]
        
        try:
            headers = json.loads(header_json.decode('utf-8'))
            
            # Create inner packet
            inner_packet = PacketLayer(
                layer_type=headers.get('type', 'unknown'),
                headers=headers,
                payload=inner_payload
            )
            
            return {'packet': inner_packet, 'headers': headers}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None