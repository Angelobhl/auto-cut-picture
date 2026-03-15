from PIL import Image, ImageOps
import os
import uuid
from typing import Optional, Tuple
from pathlib import Path
import io
import zipfile
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = storage_path
        self.uploads_path = os.path.join(storage_path, "uploads")
        self.processed_path = os.path.join(storage_path, "processed")
        self.thumbnails_path = os.path.join(storage_path, "thumbnails")

        # Ensure directories exist
        os.makedirs(self.uploads_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        os.makedirs(self.thumbnails_path, exist_ok=True)

    def _get_exif_bytes(self, image: Image.Image) -> Optional[bytes]:
        """Extract EXIF data as bytes from image if available."""
        try:
            # Method 1: Get raw EXIF bytes from image.info (most reliable)
            if 'exif' in image.info:
                exif_bytes = image.info['exif']
                logger.info(f"Found EXIF bytes in image.info, length: {len(exif_bytes)}")
                return exif_bytes

            # Method 2: Use getexif() to get Exif object and convert to bytes
            exif = image.getexif()
            if exif:
                exif_bytes = exif.tobytes()
                logger.info(f"Extracted EXIF bytes via getexif(), length: {len(exif_bytes)}")
                return exif_bytes
        except Exception as e:
            logger.warning(f"Could not read EXIF data: {e}")

        return None

    def save_upload(self, file_data: bytes, filename: str) -> Tuple[str, str, Tuple[int, int]]:
        """Save uploaded image and return (image_id, path, dimensions)"""
        image_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()

        # Open image to get dimensions and EXIF
        image = Image.open(io.BytesIO(file_data))
        width, height = image.size

        # Extract EXIF data before processing
        exif_bytes = self._get_exif_bytes(image)

        # Convert to RGB if needed for JPEG (ensures compatibility)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Save original image with EXIF preserved
        # Always use .jpg extension since we save as JPEG format
        safe_filename = f"{image_id}.jpg"
        original_path = os.path.join(self.uploads_path, safe_filename)

        # Save with EXIF data (Pillow expects bytes format)
        if exif_bytes:
            try:
                image.save(original_path, format='JPEG', exif=exif_bytes, quality=90)
                logger.info(f"Saved image with EXIF preserved: {original_path}")
            except Exception as e:
                logger.warning(f"Could not save with EXIF, saving without: {e}")
                image.save(original_path, quality=90)
        else:
            # No EXIF data
            image.save(original_path, quality=90)
            logger.info(f"Saved image without EXIF: {original_path}")

        # Generate thumbnail
        self._generate_thumbnail(image, image_id, ext)

        return image_id, original_path, (width, height)

    def _generate_thumbnail(self, image: Image.Image, image_id: str, ext: str) -> str:
        """Generate and save a thumbnail"""
        # Create thumbnail with max dimension of 300px
        thumbnail_size = (300, 300)
        thumb = image.copy()
        thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # Always use .jpg extension for thumbnails since we save as JPEG format
        thumbnail_path = os.path.join(self.thumbnails_path, f"{image_id}_thumb.jpg")

        # Save thumbnail as JPEG
        if thumb.mode not in ('RGB', 'L'):
            thumb = thumb.convert('RGB')
        thumb.save(thumbnail_path, "JPEG", quality=85)

        return thumbnail_path

    def get_thumbnail_path(self, image_id: str) -> Optional[str]:
        """Get thumbnail path for an image"""
        # Thumbnails are always saved as .jpg
        path = os.path.join(self.thumbnails_path, f"{image_id}_thumb.jpg")
        if os.path.exists(path):
            return path
        return None

    def crop_image(
        self,
        image_id: str,
        version_id: str,
        crop_data: dict,
        scale: float = 1.0,
        pan: Optional[dict] = None,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        preserve_exif: bool = True
    ) -> str:
        """
        Crop and process image based on crop data.

        Args:
            image_id: Original image ID
            version_id: Version ID for naming the output
            crop_data: Dictionary with x, y, width, height (percentages of original)
            scale: Scale factor
            pan: Optional pan offset {x, y}
            target_width: Optional target width in pixels
            target_height: Optional target height in pixels
            preserve_exif: Whether to preserve EXIF data (default: True)
        """
        # Find original image
        original_path = self._find_original_path(image_id)
        if not original_path:
            raise FileNotFoundError(f"Original image not found for image_id: {image_id}")

        # Open original image
        image = Image.open(original_path)
        img_width, img_height = image.size

        # Get EXIF data
        exif_bytes = self._get_exif_bytes(image)

        # Calculate crop coordinates in pixels
        x = int((crop_data['x'] / 100) * img_width)
        y = int((crop_data['y'] / 100) * img_height)
        crop_width = int((crop_data['width'] / 100) * img_width)
        crop_height = int((crop_data['height'] / 100) * img_height)

        # Apply pan if provided
        if pan:
            pan_x = int((pan['x'] / 100) * img_width)
            pan_y = int((pan['y'] / 100) * img_height)
            x += pan_x
            y += pan_y

        # Ensure crop is within image bounds
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        crop_width = min(crop_width, img_width - x)
        crop_height = min(crop_height, img_height - y)

        # Crop the image
        cropped = image.crop((x, y, x + crop_width, y + crop_height))

        # Resize if target dimensions specified
        if target_width and target_height:
            cropped = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
        elif scale != 1.0:
            new_width = int(crop_width * scale)
            new_height = int(crop_height * scale)
            cropped = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB if needed for JPEG output
        if cropped.mode not in ('RGB', 'L'):
            cropped = cropped.convert('RGB')

        # Save processed image
        processed_filename = f"{image_id}_{version_id}_cropped.jpg"
        processed_path = os.path.join(self.processed_path, processed_filename)

        # Save with or without EXIF
        if preserve_exif and exif_bytes:
            try:
                cropped.save(processed_path, format='JPEG', exif=exif_bytes, quality=90)
                logger.info(f"Saved cropped image with EXIF: {processed_path}")
            except Exception as e:
                logger.warning(f"Could not preserve EXIF in cropped image: {e}")
                cropped.save(processed_path, format='JPEG', quality=90)
                logger.info(f"Saved cropped image without EXIF: {processed_path}")
        else:
            cropped.save(processed_path, format='JPEG', quality=90)
            logger.info(f"Saved cropped image without EXIF: {processed_path}")

        return processed_path

    def _find_original_path(self, image_id: str) -> Optional[str]:
        """Find the original image path by image ID"""
        # Original images are always saved as .jpg
        path = os.path.join(self.uploads_path, f"{image_id}.jpg")
        if os.path.exists(path):
            return path
        return None

    def delete_image(self, image_id: str) -> None:
        """Delete all files related to an image"""
        # Delete original
        original_path = self._find_original_path(image_id)
        if original_path and os.path.exists(original_path):
            os.remove(original_path)

        # Delete thumbnail
        thumbnail_path = self.get_thumbnail_path(image_id)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        # Delete EXIF metadata
        exif_data_path = os.path.join(self.uploads_path, f"{image_id}_exif.json")
        if os.path.exists(exif_data_path):
            os.remove(exif_data_path)

        # Delete all processed versions
        for file in os.listdir(self.processed_path):
            if file.startswith(f"{image_id}_") and file.endswith("_cropped.jpg"):
                file_path = os.path.join(self.processed_path, file)
                os.remove(file_path)

    def delete_version(self, image_id: str, version_id: str) -> None:
        """Delete processed file for a specific version"""
        processed_path = os.path.join(self.processed_path, f"{image_id}_{version_id}_cropped.jpg")
        if os.path.exists(processed_path):
            os.remove(processed_path)

    def create_batch_zip(self, version_ids: list, in_memory: bool = False) -> Optional[str]:
        """
        Create a ZIP file containing multiple processed versions.

        Args:
            version_ids: List of (image_id, version_id) tuples
            in_memory: If True, creates ZIP in memory and returns bytes

        Returns:
            Path to ZIP file (or None if in_memory)
        """
        zip_path = os.path.join(self.processed_path, f"batch_{uuid.uuid4()}.zip")

        if in_memory:
            return None  # In-memory implementation not needed for this use case

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_id, version_id in version_ids:
                processed_path = self.get_processed_path(image_id, version_id)
                if processed_path and os.path.exists(processed_path):
                    # Use version_id as filename in ZIP
                    arcname = f"{version_id}.jpg"
                    zipf.write(processed_path, arcname)
                    logger.info(f"Added to ZIP: {arcname}")

        return zip_path

    def cleanup_old_zips(self, max_age_hours: int = 1) -> None:
        """Clean up old batch ZIP files"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for file in os.listdir(self.processed_path):
            if file.startswith("batch_") and file.endswith(".zip"):
                file_path = os.path.join(self.processed_path, file)
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Deleted old ZIP file: {file}")

    def get_processed_path(self, image_id: str, version_id: str) -> Optional[str]:
        """Get processed image path for a version"""
        path = os.path.join(self.processed_path, f"{image_id}_{version_id}_cropped.jpg")
        if os.path.exists(path):
            return path
        return None
