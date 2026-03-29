"""
Steganography Embedder - Hide data in images
LSB (Least Significant Bit) + random noise embedding
"""

from PIL import Image
import numpy as np
from typing import Tuple
import secrets


class ImageEmbedder:
    """Embeds hidden messages in images using LSB steganography"""
    
    @staticmethod
    def embed_data(image_path: str, secret_data: bytes, output_path: str) -> bool:
        """
        Embed secret data in an image
        
        Args:
            image_path: Path to input image
            secret_data: Data to hide
            output_path: Path to save image with embedded data
        
        Returns:
            True if successful
        """
        try:
            # Open image
            image = Image.open(image_path).convert('RGB')
            pixels = np.array(image)
            
            # Get dimensions
            height, width, channels = pixels.shape
            max_bytes = (height * width * channels) // 8
            
            if len(secret_data) > max_bytes:
                return False
            
            # Add length header (4 bytes)
            data_length = len(secret_data)
            length_bytes = data_length.to_bytes(4, byteorder='big')
            full_data = length_bytes + secret_data
            
            # Convert data to binary
            binary_data = ''.join(format(byte, '08b') for byte in full_data)
            
            # Embed in LSBs
            flat_pixels = pixels.flatten()
            for i, bit in enumerate(binary_data):
                flat_pixels[i] = (flat_pixels[i] & 0xFE) | int(bit)
            
            # Reshape and save
            embedded_pixels = flat_pixels.reshape(pixels.shape)
            embedded_image = Image.fromarray(embedded_pixels.astype(np.uint8))
            embedded_image.save(output_path)
            
            return True
        
        except Exception as e:
            print(f"Embedding error: {e}")
            return False
    
    @staticmethod
    def extract_data(image_path: str) -> Tuple[bytes, bool]:
        """
        Extract hidden data from image
        
        Args:
            image_path: Path to image with hidden data
        
        Returns:
            Tuple of (extracted_data, success)
        """
        try:
            # Open image
            image = Image.open(image_path).convert('RGB')
            pixels = np.array(image)
            
            # Extract LSBs
            flat_pixels = pixels.flatten()
            binary_data = ''.join(str(pixel & 1) for pixel in flat_pixels)
            
            # Extract length (first 32 bits)
            length_binary = binary_data[:32]
            data_length = int(length_binary, 2)
            
            # Extract secret data
            secret_binary = binary_data[32:32 + (data_length * 8)]
            secret_data = bytes(int(secret_binary[i:i+8], 2) for i in range(0, len(secret_binary), 8))
            
            return secret_data, True
        
        except Exception as e:
            print(f"Extraction error: {e}")
            return b'', False


class Steganographer:
    """High-level steganography interface"""
    
    def __init__(self):
        self.embedder = ImageEmbedder()
    
    def hide_message(self, message: bytes, image_path: str, output_path: str) -> bool:
        """
        Hide a message in an image
        
        Args:
            message: Message to hide
            image_path: Image to hide in
            output_path: Output image path
        
        Returns:
            True if successful
        """
        # Optionally encrypt message first
        return self.embedder.embed_data(image_path, message, output_path)
    
    def reveal_message(self, image_path: str) -> Tuple[bytes, bool]:
        """
        Reveal hidden message from image
        
        Args:
            image_path: Image containing hidden message
        
        Returns:
            Tuple of (message, success)
        """
        return self.embedder.extract_data(image_path)
    
    @staticmethod
    def get_embedding_capacity(image_path: str) -> int:
        """
        Get maximum bytes that can be embedded
        
        Args:
            image_path: Image path
        
        Returns:
            Maximum bytes
        """
        try:
            image = Image.open(image_path).convert('RGB')
            height, width = image.size
            return (height * width * 3) // 8 - 4  # Reserve 4 bytes for length
        except:
            return 0
