"""
Image Handler - Image processing utilities
"""

from PIL import Image
import os
from typing import Optional, Tuple


class ImageHandler:
    """Handles image processing and validation"""
    
    # Supported formats
    SUPPORTED_FORMATS = ['PNG', 'JPG', 'JPEG', 'BMP', 'TIFF']
    
    @staticmethod
    def load_image(image_path: str) -> Optional[Image.Image]:
        """
        Load an image
        
        Args:
            image_path: Path to image
        
        Returns:
            PIL Image object or None
        """
        try:
            if not os.path.exists(image_path):
                return None
            
            image = Image.open(image_path)
            return image
        
        except Exception as e:
            print(f"Failed to load image: {e}")
            return None
    
    @staticmethod
    def validate_image(image_path: str) -> bool:
        """
        Validate image is supported and readable
        
        Args:
            image_path: Image path
        
        Returns:
            True if valid
        """
        try:
            image = Image.open(image_path)
            return image.format in ImageHandler.SUPPORTED_FORMATS
        except:
            return False
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
        """
        Get image dimensions
        
        Args:
            image_path: Image path
        
        Returns:
            Tuple of (width, height) or None
        """
        try:
            image = Image.open(image_path)
            return image.size
        except:
            return None
    
    @staticmethod
    def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
        """
        Resize image
        
        Args:
            image: PIL Image
            width: Target width
            height: Target height
        
        Returns:
            Resized image
        """
        return image.resize((width, height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def convert_to_rgb(image: Image.Image) -> Image.Image:
        """
        Convert image to RGB
        
        Args:
            image: PIL Image
        
        Returns:
            RGB image
        """
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image
