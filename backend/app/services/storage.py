from typing import List, Optional, Dict
from ..models import Image, ImageVersion, CropData, Pan, AspectRatio, ImageDimensions
import uuid


class InMemoryStorage:
    """In-memory storage for images and versions"""

    def __init__(self):
        self.images: Dict[str, Image] = {}

    def add_image(self, image: Image) -> None:
        self.images[image.id] = image

    def get_image(self, image_id: str) -> Optional[Image]:
        return self.images.get(image_id)

    def get_all_images(self) -> List[Image]:
        return list(self.images.values())

    def delete_image(self, image_id: str) -> bool:
        if image_id in self.images:
            del self.images[image_id]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all images from storage"""
        self.images.clear()

    def has_images(self) -> bool:
        """Check if storage has any images"""
        return len(self.images) > 0

    def add_version(self, image_id: str, version: ImageVersion) -> Optional[Image]:
        """Add a version to an image"""
        image = self.get_image(image_id)
        if image:
            image.versions.append(version)
            return image
        return None

    def get_version(self, image_id: str, version_id: str) -> Optional[ImageVersion]:
        """Get a specific version"""
        image = self.get_image(image_id)
        if image:
            for version in image.versions:
                if version.id == version_id:
                    return version
        return None

    def update_version_crop(self, image_id: str, version_id: str, crop_data: CropData, scale: float = 1.0, pan: Optional[Pan] = None, aspectRatio: Optional[AspectRatio] = None) -> Optional[ImageVersion]:
        """Update crop data for a version"""
        image = self.get_image(image_id)
        if image:
            for version in image.versions:
                if version.id == version_id:
                    version.cropData = crop_data
                    version.scale = scale
                    if pan:
                        version.pan = pan
                    version.aspectRatio = aspectRatio
                    return version
        return None

    def delete_version(self, image_id: str, version_id: str) -> bool:
        """Delete a version from an image"""
        image = self.get_image(image_id)
        if image:
            for i, version in enumerate(image.versions):
                if version.id == version_id:
                    image.versions.pop(i)
                    return True
        return False

    def create_default_version(self, image_id: str, dimensions: ImageDimensions) -> ImageVersion:
        """Create a default version for a new image"""
        version_id = str(uuid.uuid4())
        return ImageVersion(
            id=version_id,
            imageId=image_id,
            name="Original",
            aspectRatio=AspectRatio(width=dimensions.width, height=dimensions.height),
            cropData=CropData(x=0, y=0, width=100, height=100),
            scale=1.0,
            pan=Pan(x=0, y=0),
            processed=False,
            processedPath=None
        )

    def update_version_processed(self, image_id: str, version_id: str, processed_path: str) -> Optional[ImageVersion]:
        """Mark a version as processed"""
        image = self.get_image(image_id)
        if image:
            for version in image.versions:
                if version.id == version_id:
                    version.processed = True
                    version.processedPath = processed_path
                    return version
        return None


# Global storage instance
storage = InMemoryStorage()
