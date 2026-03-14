"""
CRUD operations for the database.
"""
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import ImageModel, ImageVersionModel
from ..models import (
    Image, ImageVersion, CropData, Pan, AspectRatio, ImageDimensions
)
import uuid


class CRUD:
    """CRUD operations for images and versions."""

    # ==================== Image Operations ====================

    async def create_image(
        self,
        db: AsyncSession,
        image_id: str,
        filename: str,
        original_path: str,
        width: int,
        height: int,
    ) -> ImageModel:
        """Create a new image record."""
        db_image = ImageModel(
            id=image_id,
            filename=filename,
            original_path=original_path,
            width=width,
            height=height,
        )
        db.add(db_image)
        await db.flush()
        return db_image

    async def get_image(self, db: AsyncSession, image_id: str) -> Optional[ImageModel]:
        """Get an image by ID with versions loaded."""
        result = await db.execute(
            select(ImageModel)
            .options(selectinload(ImageModel.versions))
            .where(ImageModel.id == image_id)
        )
        return result.scalar_one_or_none()

    async def get_all_images(self, db: AsyncSession) -> List[ImageModel]:
        """Get all images with versions loaded."""
        result = await db.execute(
            select(ImageModel)
            .options(selectinload(ImageModel.versions))
            .order_by(ImageModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_image(self, db: AsyncSession, image_id: str) -> bool:
        """Delete an image and all its versions."""
        result = await db.execute(
            delete(ImageModel).where(ImageModel.id == image_id)
        )
        return result.rowcount > 0

    async def clear_all(self, db: AsyncSession) -> int:
        """Delete all images. Returns count of deleted images."""
        result = await db.execute(delete(ImageModel))
        return result.rowcount

    async def has_images(self, db: AsyncSession) -> bool:
        """Check if there are any images in the database."""
        result = await db.execute(select(ImageModel.id).limit(1))
        return result.scalar_one_or_none() is not None

    # ==================== Version Operations ====================

    async def create_version(
        self,
        db: AsyncSession,
        version_id: str,
        image_id: str,
        name: str,
        crop_data: CropData,
        scale: float = 1.0,
        pan: Optional[Pan] = None,
        aspect_ratio: Optional[AspectRatio] = None,
        processed: bool = False,
        processed_path: Optional[str] = None,
    ) -> ImageVersionModel:
        """Create a new version record."""
        db_version = ImageVersionModel(
            id=version_id,
            image_id=image_id,
            name=name,
            aspect_width=aspect_ratio.width if aspect_ratio else None,
            aspect_height=aspect_ratio.height if aspect_ratio else None,
            crop_x=crop_data.x,
            crop_y=crop_data.y,
            crop_width=crop_data.width,
            crop_height=crop_data.height,
            scale=scale,
            pan_x=pan.x if pan else 0,
            pan_y=pan.y if pan else 0,
            processed=processed,
            processed_path=processed_path,
        )
        db.add(db_version)
        await db.flush()
        return db_version

    async def get_version(
        self, db: AsyncSession, image_id: str, version_id: str
    ) -> Optional[ImageVersionModel]:
        """Get a specific version by image_id and version_id."""
        result = await db.execute(
            select(ImageVersionModel)
            .where(ImageVersionModel.id == version_id)
            .where(ImageVersionModel.image_id == image_id)
        )
        return result.scalar_one_or_none()

    async def update_version(
        self,
        db: AsyncSession,
        version_id: str,
        crop_data: Optional[CropData] = None,
        scale: Optional[float] = None,
        pan: Optional[Pan] = None,
        aspect_ratio: Optional[AspectRatio] = None,
        processed: Optional[bool] = None,
        processed_path: Optional[str] = None,
    ) -> Optional[ImageVersionModel]:
        """Update a version's fields."""
        db_version = await db.get(ImageVersionModel, version_id)
        if not db_version:
            return None

        if crop_data:
            db_version.crop_x = crop_data.x
            db_version.crop_y = crop_data.y
            db_version.crop_width = crop_data.width
            db_version.crop_height = crop_data.height

        if scale is not None:
            db_version.scale = scale

        if pan:
            db_version.pan_x = pan.x
            db_version.pan_y = pan.y

        if aspect_ratio:
            db_version.aspect_width = aspect_ratio.width
            db_version.aspect_height = aspect_ratio.height
        elif aspect_ratio is None and crop_data is None:
            # Explicitly set to None only if not updating other fields
            pass

        if processed is not None:
            db_version.processed = processed

        if processed_path is not None:
            db_version.processed_path = processed_path

        await db.flush()
        return db_version

    async def delete_version(
        self, db: AsyncSession, image_id: str, version_id: str
    ) -> bool:
        """Delete a version."""
        result = await db.execute(
            delete(ImageVersionModel)
            .where(ImageVersionModel.id == version_id)
            .where(ImageVersionModel.image_id == image_id)
        )
        return result.rowcount > 0

    # ==================== Helper Methods ====================

    def image_model_to_pydantic(self, db_image: ImageModel) -> Image:
        """Convert SQLAlchemy ImageModel to Pydantic Image."""
        versions = [
            self.version_model_to_pydantic(v) for v in db_image.versions
        ]
        return Image(
            id=db_image.id,
            filename=db_image.filename,
            originalPath=db_image.original_path,
            dimensions=ImageDimensions(width=db_image.width, height=db_image.height),
            versions=versions,
        )

    def version_model_to_pydantic(self, db_version: ImageVersionModel) -> ImageVersion:
        """Convert SQLAlchemy ImageVersionModel to Pydantic ImageVersion."""
        aspect_ratio = None
        if db_version.aspect_width is not None and db_version.aspect_height is not None:
            aspect_ratio = AspectRatio(
                width=db_version.aspect_width,
                height=db_version.aspect_height,
            )

        return ImageVersion(
            id=db_version.id,
            imageId=db_version.image_id,
            name=db_version.name,
            aspectRatio=aspect_ratio,
            cropData=CropData(
                x=db_version.crop_x,
                y=db_version.crop_y,
                width=db_version.crop_width,
                height=db_version.crop_height,
            ),
            scale=db_version.scale,
            pan=Pan(x=db_version.pan_x, y=db_version.pan_y),
            processed=db_version.processed,
            processedPath=db_version.processed_path,
        )


# Global CRUD instance
crud = CRUD()