"""
Steganography Extractor - Extract hidden data from images
"""

from PIL import Image
import numpy as np
from typing import Tuple, Optional


class StegoExtractor:
    """Extracts hidden data from steganographic images"""
    
    @staticmethod
    def extract(image_path: str, header_bytes: int = 4) -> Tuple[Optional[bytes], bool]:
        """
        Extract hidden data from image
        
        Args:
            image_path: Path to image
            header_bytes: Bytes for length header
        
        Returns:
            Tuple of (data, success)
        """
        try:
            image = Image.open(image_path).convert('RGB')
            pixels = np.array(image)
            
            # Extract LSBs
            flat_pixels = pixels.flatten()
            binary_str = ''.join(str(p & 1) for p in flat_pixels)
            
            # Extract length header
            if len(binary_str) < header_bytes * 8:
                return None, False
            
            header_binary = binary_str[:header_bytes * 8]
            data_length = int(header_binary, 2)
            
            # Validate
            if data_length > len(binary_str) // 8:
                return None, False
            
            # Extract data
            data_binary = binary_str[header_bytes * 8:header_bytes * 8 + data_length * 8]
            
            # Convert binary to bytes
            data = bytes(int(data_binary[i:i+8], 2) for i in range(0, len(data_binary), 8))
            
            return data, True
        
        except Exception as e:
            print(f"Extraction error: {e}")
            return None, False
    
    @staticmethod
    def verify_steganographic_image(image_path: str) -> bool:
        """
        Check if image likely contains hidden data
        
        Args:
            image_path: Image path
        
        Returns:
            True if extraction is possible
        """
        try:
            data, success = StegoExtractor.extract(image_path)
            return success and data is not None
        except:
            return False
