"""
Steganography - Hide messages in images
Implements LSB (Least Significant Bit) steganography for image-based message hiding
"""

from typing import Optional, Tuple, Union
import os
from PIL import Image
import numpy as np
from dataclasses import dataclass
import base64


@dataclass
class StegoResult:
    """Result of steganography operation"""
    success: bool
    image_path: Optional[str] = None
    message_size: int = 0
    capacity: int = 0
    error: Optional[str] = None


class Steganographer:
    """LSB Steganography implementation for hiding data in images"""
    
    # Maximum message size as percentage of image capacity
    MAX_MESSAGE_RATIO = 0.8
    
    def __init__(self, bits_per_pixel: int = 1):
        """
        Initialize steganographer
        
        Args:
            bits_per_pixel: Number of LSB bits to use per pixel (1-8)
        """
        if not 1 <= bits_per_pixel <= 8:
            raise ValueError("bits_per_pixel must be between 1 and 8")
        
        self.bits_per_pixel = bits_per_pixel
        self.mask = (1 << bits_per_pixel) - 1  # e.g., 1 for 1 bit, 3 for 2 bits, etc.
    
    def calculate_capacity(self, image_path: str) -> int:
        """
        Calculate maximum message capacity for an image
        
        Args:
            image_path: Path to image file
        
        Returns:
            Maximum bytes that can be hidden
        """
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGB')  # Ensure RGB mode
                width, height = img.size
                total_pixels = width * height
                
                # Each pixel has 3 channels (RGB), each can hold bits_per_pixel bits
                total_bits = total_pixels * 3 * self.bits_per_pixel
                max_bytes = total_bits // 8
                
                return int(max_bytes * self.MAX_MESSAGE_RATIO)
        except Exception as e:
            raise ValueError(f"Cannot calculate capacity for {image_path}: {e}")
    
    def embed_message(self, image_path: str, message: Union[str, bytes], 
                     output_path: Optional[str] = None) -> StegoResult:
        """
        Embed a message into an image using LSB steganography
        
        Args:
            image_path: Path to carrier image
            message: Message to hide (string or bytes)
            output_path: Path for output image (optional)
        
        Returns:
            StegoResult with operation status
        """
        try:
            # Convert message to bytes if needed
            if isinstance(message, str):
                message_bytes = message.encode('utf-8')
            else:
                message_bytes = message
            
            # Add length prefix (4 bytes)
            length_prefix = len(message_bytes).to_bytes(4, 'big')
            data_to_hide = length_prefix + message_bytes
            
            # Check capacity
            capacity = self.calculate_capacity(image_path)
            if len(data_to_hide) > capacity:
                return StegoResult(
                    success=False,
                    error=f"Message too large ({len(data_to_hide)} bytes) for image capacity ({capacity} bytes)"
                )
            
            # Load image
            with Image.open(image_path) as img:
                img = img.convert('RGB')
                pixels = np.array(img)
                
                # Convert data to bit stream
                bit_stream = self._bytes_to_bits(data_to_hide)
                
                # Embed bits
                flat_pixels = pixels.flatten()
                bit_index = 0
                
                for i in range(len(flat_pixels)):
                    if bit_index >= len(bit_stream):
                        break
                    
                    # Get current pixel value
                    pixel_value = flat_pixels[i]
                    
                    # Clear LSBs and embed new bits
                    bits_to_embed = min(self.bits_per_pixel, len(bit_stream) - bit_index)
                    embedded_value = pixel_value & ~self.mask
                    
                    # Extract bits from stream
                    bit_chunk = 0
                    for j in range(bits_to_embed):
                        if bit_index + j < len(bit_stream):
                            bit_chunk |= (bit_stream[bit_index + j] << j)
                    
                    embedded_value |= bit_chunk
                    flat_pixels[i] = embedded_value
                    bit_index += bits_to_embed
                
                # Reshape back to image
                new_pixels = flat_pixels.reshape(pixels.shape)
                stego_image = Image.fromarray(new_pixels.astype('uint8'), 'RGB')
                
                # Save output
                if output_path is None:
                    base_name = os.path.splitext(image_path)[0]
                    output_path = f"{base_name}_stego.png"
                
                stego_image.save(output_path, 'PNG')
                
                return StegoResult(
                    success=True,
                    image_path=output_path,
                    message_size=len(message_bytes),
                    capacity=capacity
                )
                
        except Exception as e:
            return StegoResult(
                success=False,
                error=f"Failed to embed message: {str(e)}"
            )
    
    def extract_message(self, image_path: str) -> Union[str, bytes, None]:
        """
        Extract hidden message from steganographic image
        
        Args:
            image_path: Path to steganographic image
        
        Returns:
            Extracted message or None if failed
        """
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGB')
                pixels = np.array(img).flatten()
                
                # Extract bits
                bit_stream = []
                
                for pixel_value in pixels:
                    # Extract LSBs
                    extracted_bits = pixel_value & self.mask
                    
                    # Convert to individual bits
                    for j in range(self.bits_per_pixel):
                        bit = (extracted_bits >> j) & 1
                        bit_stream.append(bit)
                        
                        # Check if we have enough for length prefix
                        if len(bit_stream) >= 32:  # 4 bytes * 8 bits
                            break
                    
                    if len(bit_stream) >= 32:
                        break
                
                # Convert bits to bytes
                data_bytes = self._bits_to_bytes(bit_stream)
                
                if len(data_bytes) < 4:
                    return None
                
                # Extract length
                message_length = int.from_bytes(data_bytes[:4], 'big')
                
                if len(data_bytes) < 4 + message_length:
                    return None
                
                # Extract message
                message_bytes = data_bytes[4:4 + message_length]
                
                # Try to decode as UTF-8 string
                try:
                    return message_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    return message_bytes
                    
        except Exception as e:
            print(f"Failed to extract message: {e}")
            return None
    
    def embed_file(self, image_path: str, file_path: str, 
                  output_path: Optional[str] = None) -> StegoResult:
        """
        Embed a file's contents into an image
        
        Args:
            image_path: Path to carrier image
            file_path: Path to file to hide
            output_path: Path for output image
        
        Returns:
            StegoResult with operation status
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Add filename to the data
            filename = os.path.basename(file_path).encode('utf-8')
            filename_length = len(filename).to_bytes(2, 'big')
            
            combined_data = filename_length + filename + file_data
            
            return self.embed_message(image_path, combined_data, output_path)
            
        except Exception as e:
            return StegoResult(
                success=False,
                error=f"Failed to embed file: {str(e)}"
            )
    
    def extract_file(self, image_path: str, output_dir: str = ".") -> Optional[str]:
        """
        Extract a hidden file from steganographic image
        
        Args:
            image_path: Path to steganographic image
            output_dir: Directory to save extracted file
        
        Returns:
            Path to extracted file or None if failed
        """
        data = self.extract_message(image_path)
        if not isinstance(data, bytes):
            return None
        
        try:
            if len(data) < 2:
                return None
            
            # Extract filename
            filename_length = int.from_bytes(data[:2], 'big')
            if len(data) < 2 + filename_length:
                return None
            
            filename = data[2:2 + filename_length].decode('utf-8')
            file_data = data[2 + filename_length:]
            
            # Save file
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            return output_path
            
        except Exception as e:
            print(f"Failed to extract file: {e}")
            return None
    
    def _bytes_to_bits(self, data: bytes) -> list:
        """Convert bytes to bit list"""
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits
    
    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert bit list to bytes"""
        bytes_list = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte |= (bits[i + j] << (7 - j))
            bytes_list.append(byte)
        return bytes(bytes_list)


# Convenience functions

def hide_message_in_image(image_path: str, message: str, output_path: Optional[str] = None) -> StegoResult:
    """
    Convenience function to hide a text message in an image
    
    Args:
        image_path: Path to carrier image
        message: Text message to hide
        output_path: Optional output path
    
    Returns:
        StegoResult
    """
    stego = Steganographer()
    return stego.embed_message(image_path, message, output_path)


def reveal_message_from_image(image_path: str) -> Optional[str]:
    """
    Convenience function to extract a text message from an image
    
    Args:
        image_path: Path to steganographic image
    
    Returns:
        Extracted message or None
    """
    stego = Steganographer()
    return stego.extract_message(image_path)


def hide_file_in_image(image_path: str, file_path: str, output_path: Optional[str] = None) -> StegoResult:
    """
    Convenience function to hide a file in an image
    
    Args:
        image_path: Path to carrier image
        file_path: Path to file to hide
        output_path: Optional output path
    
    Returns:
        StegoResult
    """
    stego = Steganographer()
    return stego.embed_file(image_path, file_path, output_path)


def reveal_file_from_image(image_path: str, output_dir: str = ".") -> Optional[str]:
    """
    Convenience function to extract a file from an image
    
    Args:
        image_path: Path to steganographic image
        output_dir: Directory to save extracted file
    
    Returns:
        Path to extracted file or None
    """
    stego = Steganographer()
    return stego.extract_file(image_path, output_dir)