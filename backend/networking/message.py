"""
Message Structure - GhostDav protocol message definitions
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import time
import struct
import json


class MessageType(Enum):
    """Message types in GhostDav protocol"""
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    HEARTBEAT = "HEARTBEAT"
    ACK = "ACK"
    TEXT = "TEXT"
    VOICE = "VOICE"
    VIDEO = "VIDEO"
    STEGO = "STEGO"


class EncryptionType(Enum):
    """Encryption algorithms"""
    CHACHA20_POLY1305 = "CHACHA20_POLY1305"
    AES_256_GCM = "AES_256_GCM"


@dataclass
class MessageHeader:
    """Message header structure"""
    message_type: MessageType
    length: int
    version: str = "1.0"
    sequence_number: int = 0
    timestamp: float = None
    flags: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class MessagePayload:
    """Message payload structure"""
    encryption_type: EncryptionType
    nonce: bytes
    ciphertext: bytes
    auth_tag: bytes


@dataclass
class MessageMetadata:
    """Optional metadata for routing and additional info"""
    router_instructions: Optional[Dict[str, Any]] = None
    aliases: Optional[Dict[str, str]] = None
    fake_ip: Optional[str] = None
    hop_count: int = 0


@dataclass
class GhostDavMessage:
    """Complete GhostDav message structure"""
    header: MessageHeader
    payload: MessagePayload
    metadata: Optional[MessageMetadata] = None

    def to_bytes(self) -> bytes:
        """Serialize message to bytes according to protocol"""
        # Header: 20 bytes
        msg_type_bytes = self.header.message_type.value.encode('utf-8').ljust(2, b'\x00')[:2]
        length_bytes = struct.pack('>H', self.header.length)  # 2 bytes, big-endian
        version_bytes = self.header.version.encode('utf-8').ljust(2, b'\x00')[:2]
        seq_bytes = struct.pack('>I', self.header.sequence_number)  # 4 bytes
        timestamp_bytes = struct.pack('>d', self.header.timestamp)  # 8 bytes
        flags_bytes = struct.pack('>H', self.header.flags)  # 2 bytes

        header_bytes = msg_type_bytes + length_bytes + version_bytes + seq_bytes + timestamp_bytes + flags_bytes

        # Payload
        enc_type_byte = struct.pack('B', list(EncryptionType).index(self.payload.encryption_type))
        payload_bytes = enc_type_byte + self.payload.nonce + self.payload.ciphertext + self.payload.auth_tag

        # Metadata (optional)
        metadata_bytes = b''
        if self.metadata:
            metadata_json = json.dumps({
                'router_instructions': self.metadata.router_instructions,
                'aliases': self.metadata.aliases,
                'fake_ip': self.metadata.fake_ip,
                'hop_count': self.metadata.hop_count
            }).encode('utf-8')
            metadata_bytes = struct.pack('>I', len(metadata_json)) + metadata_json  # Length prefixed

        return header_bytes + payload_bytes + metadata_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'GhostDavMessage':
        """Deserialize message from bytes"""
        if len(data) < 20:
            raise ValueError("Message too short")

        # Parse header
        msg_type_str = data[0:2].decode('utf-8').rstrip('\x00')
        try:
            msg_type = MessageType(msg_type_str)
        except ValueError:
            raise ValueError(f"Unknown message type: {msg_type_str}")

        length = struct.unpack('>H', data[2:4])[0]
        version = data[4:6].decode('utf-8').rstrip('\x00')
        seq_num = struct.unpack('>I', data[6:10])[0]
        timestamp = struct.unpack('>d', data[10:18])[0]
        flags = struct.unpack('>H', data[18:20])[0]

        header = MessageHeader(
            message_type=msg_type,
            length=length,
            version=version,
            sequence_number=seq_num,
            timestamp=timestamp,
            flags=flags
        )

        # Parse payload
        offset = 20
        enc_type_idx = struct.unpack('B', data[offset:offset+1])[0]
        enc_type = list(EncryptionType)[enc_type_idx]
        offset += 1

        nonce = data[offset:offset+24]
        offset += 24

        # Ciphertext length = total length - header - enc_type - nonce - auth_tag - metadata_length
        # But for simplicity, assume ciphertext until auth_tag
        # This is simplified; in real protocol, length field helps
        auth_tag_start = offset + length - 16  # Assuming auth_tag is 16 bytes
        ciphertext = data[offset:auth_tag_start]
        auth_tag = data[auth_tag_start:auth_tag_start+16]
        offset = auth_tag_start + 16

        payload = MessagePayload(
            encryption_type=enc_type,
            nonce=nonce,
            ciphertext=ciphertext,
            auth_tag=auth_tag
        )

        # Metadata
        metadata = None
        if offset < len(data):
            metadata_len = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            metadata_json = data[offset:offset+metadata_len]
            metadata_dict = json.loads(metadata_json.decode('utf-8'))
            metadata = MessageMetadata(**metadata_dict)

        return cls(header=header, payload=payload, metadata=metadata)


# Convenience functions for creating specific message types

def create_connect_message(client_id: str, public_key: bytes) -> GhostDavMessage:
    """Create a CONNECT message"""
    # Simplified: plaintext for now
    payload_data = json.dumps({'client_id': client_id, 'public_key': base64.b64encode(public_key).decode()}).encode()
    payload = MessagePayload(
        encryption_type=EncryptionType.CHACHA20_POLY1305,
        nonce=b'\x00' * 24,  # Placeholder
        ciphertext=payload_data,
        auth_tag=b'\x00' * 16  # Placeholder
    )
    header = MessageHeader(
        message_type=MessageType.CONNECT,
        length=len(payload_data)
    )
    return GhostDavMessage(header=header, payload=payload)

def create_text_message(sender: str, recipient: str, text: str) -> GhostDavMessage:
    """Create a TEXT message"""
    payload_data = json.dumps({'sender': sender, 'recipient': recipient, 'text': text}).encode()
    payload = MessagePayload(
        encryption_type=EncryptionType.CHACHA20_POLY1305,
        nonce=b'\x00' * 24,
        ciphertext=payload_data,
        auth_tag=b'\x00' * 16
    )
    header = MessageHeader(
        message_type=MessageType.TEXT,
        length=len(payload_data)
    )
    return GhostDavMessage(header=header, payload=payload)

def create_ack_message(sequence_number: int) -> GhostDavMessage:
    """Create an ACK message"""
    payload_data = json.dumps({'acked_seq': sequence_number}).encode()
    payload = MessagePayload(
        encryption_type=EncryptionType.CHACHA20_POLY1305,
        nonce=b'\x00' * 24,
        ciphertext=payload_data,
        auth_tag=b'\x00' * 16
    )
    header = MessageHeader(
        message_type=MessageType.ACK,
        length=len(payload_data),
        sequence_number=sequence_number
    )
    return GhostDavMessage(header=header, payload=payload)</content>
<parameter name="filePath">/home/davido/GhostDav/backend/networking/message.py