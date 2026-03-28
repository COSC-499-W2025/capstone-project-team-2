"""
project_thumbnails.py
=====================

Module for managing project thumbnail images.

Provides functionality to:
- Upload and validate thumbnail images
- Store thumbnails in the filesystem
- Associate thumbnails with project insights
- Retrieve and display thumbnails
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None
    print("[WARNING] PIL/Pillow not installed. Install with: pip install Pillow")


class ThumbnailManager:
    """
    Manages thumbnail images for project insights.
    
    Handles validation, storage, retrieval, and association with projects.
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Maximum file size (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Thumbnail dimensions (width, height) for standardization
    THUMBNAIL_SIZE = (400, 300)
    
    def __init__(self, storage_dir: Path | str = "User_config_files/thumbnails"):
        """
        Initialize the thumbnail manager.
        
        Args:
            storage_dir: Directory where thumbnails will be stored
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_image(self, image_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate an image file for use as a thumbnail.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if Image is None:
            return False, "PIL/Pillow not installed. Run: pip install Pillow"
        
        # Check if file exists
        if not image_path.exists():
            return False, f"File not found: {image_path}"
        
        # Check file extension
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format. Use: {', '.join(self.SUPPORTED_FORMATS)}"
        
        # Check file size
        file_size = image_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"
        
        # Try to open with PIL to validate it's a real image
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    def add_thumbnail(
        self, 
        project_id: str, 
        image_path: Path | str,
        resize: bool = True
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Add a thumbnail for a project.
        
        Args:
            project_id: Unique identifier for the project
            image_path: Path to the source image
            resize: Whether to resize the image to standard thumbnail size
            
        Returns:
            Tuple of (success, error_message, thumbnail_path)
        """
        if Image is None:
            return False, "PIL/Pillow not installed. Run: pip install Pillow", None
        
        image_path = Path(image_path)
        
        # Validate the image
        is_valid, error = self.validate_image(image_path)
        if not is_valid:
            return False, error, None
        
        try:
            # Create sanitized filename
            safe_id = self._sanitize_filename(project_id)
            ext = image_path.suffix.lower()
            thumbnail_path = self.storage_dir / f"{safe_id}{ext}"
            
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if ext in {'.jpg', '.jpeg'} and img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                    img = rgb_img
                
                # Resize if requested
                if resize:
                    img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save the thumbnail
                img.save(thumbnail_path, optimize=True, quality=85)
            
            return True, None, thumbnail_path
            
        except Exception as e:
            return False, f"Failed to process image: {str(e)}", None
    
    def get_thumbnail_path(self, project_id: str) -> Optional[Path]:
        """
        Get the path to a project's thumbnail if it exists.
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            Path to thumbnail or None if not found
        """
        safe_id = self._sanitize_filename(project_id)
        
        # Check all supported formats
        for ext in self.SUPPORTED_FORMATS:
            thumbnail_path = self.storage_dir / f"{safe_id}{ext}"
            if thumbnail_path.exists():
                return thumbnail_path
        
        return None
    
    def get_thumbnail_base64(self, project_id: str) -> Optional[str]:
        """
        Get a project's thumbnail as a base64-encoded string.
        
        Useful for embedding in JSON or HTML.
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            Base64-encoded image string or None if not found
        """
        thumbnail_path = self.get_thumbnail_path(project_id)
        if not thumbnail_path:
            return None
        
        try:
            with open(thumbnail_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception:
            return None
    
    def delete_thumbnail(self, project_id: str) -> bool:
        """
        Delete a project's thumbnail.
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            True if thumbnail was deleted, False if not found
        """
        thumbnail_path = self.get_thumbnail_path(project_id)
        if not thumbnail_path:
            return False
        
        try:
            thumbnail_path.unlink()
            return True
        except Exception:
            return False
    
    def list_thumbnails(self) -> Dict[str, Path]:
        """
        List all stored thumbnails.
        
        Returns:
            Dictionary mapping project IDs to thumbnail paths
        """
        thumbnails = {}
        
        for ext in self.SUPPORTED_FORMATS:
            for thumbnail_path in self.storage_dir.glob(f"*{ext}"):
                project_id = thumbnail_path.stem
                thumbnails[project_id] = thumbnail_path
        
        return thumbnails
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be filesystem-safe.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        safe_name = safe_name.strip('. ')
        
        # Limit length
        if len(safe_name) > 200:
            safe_name = safe_name[:200]
        
        return safe_name


def add_thumbnail_to_insight(
    insight_dict: Dict[str, Any],
    thumbnail_manager: ThumbnailManager
) -> Dict[str, Any]:
    """
    Add thumbnail information to a project insight dictionary.
    
    Args:
        insight_dict: Project insight dictionary
        thumbnail_manager: ThumbnailManager instance
        
    Returns:
        Updated insight dictionary with thumbnail info
    """
    project_id = insight_dict.get('id')
    if not project_id:
        return insight_dict
    
    thumbnail_path = thumbnail_manager.get_thumbnail_path(project_id)
    if thumbnail_path:
        insight_dict['thumbnail'] = {
            'path': str(thumbnail_path),
            'filename': thumbnail_path.name,
            'exists': True
        }
    else:
        insight_dict['thumbnail'] = {
            'path': None,
            'filename': None,
            'exists': False
        }
    
    return insight_dict


__all__ = [
    'ThumbnailManager',
    'add_thumbnail_to_insight'
]