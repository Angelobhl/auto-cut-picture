from typing import List, Optional, Dict
from ..models import Image, ImageVersion, CropData, Pan, AspectRatio, ImageDimensions
from ..db import database  # Import module to get updated variables
from ..db.crud import crud
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)


def _run_async(coro):
    """
    Run a coroutine synchronously.

    If we're inside an async context, use the running loop.
    Otherwise, create a new event loop with asyncio.run().
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(coro)

    # We're inside an async context - need to run in a thread
    # since we can't use asyncio.run() inside a running loop
    import concurrent.futures
    import threading

    # Create a new event loop in a thread
    result = None
    exception = None

    def run_in_thread():
        nonlocal result, exception
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(coro)
            new_loop.close()
        except Exception as e:
            exception = e

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


class SQLiteStorage:
    """
    SQLite-based persistent storage for images and versions.

    Provides the same interface as InMemoryStorage but persists data to SQLite.
    Uses async database operations under the hood.
    """

    async def _get_session(self):
        """Get a database session for operations."""
        if database.AsyncSessionLocal is None:
            raise RuntimeError("Database not initialized. Ensure init_db() was called.")
        return database.AsyncSessionLocal()

    def add_image(self, image: Image) -> None:
        """Add an image to storage (sync wrapper)."""
        return _run_async(self._add_image_async(image))

    async def _add_image_async(self, image: Image) -> None:
        """Async implementation of add_image."""
        async with await self._get_session() as session:
            async with session.begin():
                await crud.create_image(
                    session,
                    image_id=image.id,
                    filename=image.filename,
                    original_path=image.originalPath,
                    width=image.dimensions.width,
                    height=image.dimensions.height,
                )
                # Add all versions
                for version in image.versions:
                    await crud.create_version(
                        session,
                        version_id=version.id,
                        image_id=image.id,
                        name=version.name,
                        crop_data=version.cropData,
                        scale=version.scale,
                        pan=version.pan,
                        aspect_ratio=version.aspectRatio,
                        processed=version.processed,
                        processed_path=version.processedPath,
                    )

    def get_image(self, image_id: str) -> Optional[Image]:
        """Get an image by ID (sync wrapper)."""
        return _run_async(self._get_image_async(image_id))

    async def _get_image_async(self, image_id: str) -> Optional[Image]:
        """Async implementation of get_image."""
        async with await self._get_session() as session:
            async with session.begin():
                db_image = await crud.get_image(session, image_id)
                if db_image:
                    return crud.image_model_to_pydantic(db_image)
                return None

    def get_all_images(self) -> List[Image]:
        """Get all images (sync wrapper)."""
        return _run_async(self._get_all_images_async())

    async def _get_all_images_async(self) -> List[Image]:
        """Async implementation of get_all_images."""
        async with await self._get_session() as session:
            async with session.begin():
                db_images = await crud.get_all_images(session)
                return [crud.image_model_to_pydantic(img) for img in db_images]

    def delete_image(self, image_id: str) -> bool:
        """Delete an image (sync wrapper)."""
        return _run_async(self._delete_image_async(image_id))

    async def _delete_image_async(self, image_id: str) -> bool:
        """Async implementation of delete_image."""
        async with await self._get_session() as session:
            async with session.begin():
                return await crud.delete_image(session, image_id)

    def clear_all(self) -> None:
        """Clear all images from storage (sync wrapper)."""
        return _run_async(self._clear_all_async())

    async def _clear_all_async(self) -> None:
        """Async implementation of clear_all."""
        async with await self._get_session() as session:
            async with session.begin():
                await crud.clear_all(session)

    def has_images(self) -> bool:
        """Check if storage has any images (sync wrapper)."""
        return _run_async(self._has_images_async())

    async def _has_images_async(self) -> bool:
        """Async implementation of has_images."""
        async with await self._get_session() as session:
            async with session.begin():
                return await crud.has_images(session)

    def add_version(self, image_id: str, version: ImageVersion) -> Optional[Image]:
        """Add a version to an image (sync wrapper)."""
        return _run_async(self._add_version_async(image_id, version))

    async def _add_version_async(self, image_id: str, version: ImageVersion) -> Optional[Image]:
        """Async implementation of add_version."""
        async with await self._get_session() as session:
            async with session.begin():
                # Check if image exists
                db_image = await crud.get_image(session, image_id)
                if not db_image:
                    return None

                # Create the version
                await crud.create_version(
                    session,
                    version_id=version.id,
                    image_id=image_id,
                    name=version.name,
                    crop_data=version.cropData,
                    scale=version.scale,
                    pan=version.pan,
                    aspect_ratio=version.aspectRatio,
                    processed=version.processed,
                    processed_path=version.processedPath,
                )

                # Return updated image
                db_image = await crud.get_image(session, image_id)
                return crud.image_model_to_pydantic(db_image) if db_image else None

    def get_version(self, image_id: str, version_id: str) -> Optional[ImageVersion]:
        """Get a specific version (sync wrapper)."""
        return _run_async(self._get_version_async(image_id, version_id))

    async def _get_version_async(self, image_id: str, version_id: str) -> Optional[ImageVersion]:
        """Async implementation of get_version."""
        async with await self._get_session() as session:
            async with session.begin():
                db_version = await crud.get_version(session, image_id, version_id)
                if db_version:
                    return crud.version_model_to_pydantic(db_version)
                return None

    def update_version_crop(
        self,
        image_id: str,
        version_id: str,
        crop_data: CropData,
        scale: float = 1.0,
        pan: Optional[Pan] = None,
        aspectRatio: Optional[AspectRatio] = None,
    ) -> Optional[ImageVersion]:
        """Update crop data for a version (sync wrapper)."""
        return _run_async(
            self._update_version_crop_async(image_id, version_id, crop_data, scale, pan, aspectRatio)
        )

    async def _update_version_crop_async(
        self,
        image_id: str,
        version_id: str,
        crop_data: CropData,
        scale: float = 1.0,
        pan: Optional[Pan] = None,
        aspectRatio: Optional[AspectRatio] = None,
    ) -> Optional[ImageVersion]:
        """Async implementation of update_version_crop."""
        async with await self._get_session() as session:
            async with session.begin():
                db_version = await crud.update_version(
                    session,
                    version_id=version_id,
                    crop_data=crop_data,
                    scale=scale,
                    pan=pan,
                    aspect_ratio=aspectRatio,
                )
                if db_version:
                    return crud.version_model_to_pydantic(db_version)
                return None

    def delete_version(self, image_id: str, version_id: str) -> bool:
        """Delete a version from an image (sync wrapper)."""
        return _run_async(self._delete_version_async(image_id, version_id))

    async def _delete_version_async(self, image_id: str, version_id: str) -> bool:
        """Async implementation of delete_version."""
        async with await self._get_session() as session:
            async with session.begin():
                return await crud.delete_version(session, image_id, version_id)

    def create_default_version(self, image_id: str, dimensions: ImageDimensions) -> ImageVersion:
        """Create a default version for a new image."""
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
            processedPath=None,
        )

    def update_version_processed(
        self, image_id: str, version_id: str, processed_path: str
    ) -> Optional[ImageVersion]:
        """Mark a version as processed (sync wrapper)."""
        return _run_async(
            self._update_version_processed_async(image_id, version_id, processed_path)
        )

    async def _update_version_processed_async(
        self, image_id: str, version_id: str, processed_path: str
    ) -> Optional[ImageVersion]:
        """Async implementation of update_version_processed."""
        async with await self._get_session() as session:
            async with session.begin():
                db_version = await crud.update_version(
                    session,
                    version_id=version_id,
                    processed=True,
                    processed_path=processed_path,
                )
                if db_version:
                    return crud.version_model_to_pydantic(db_version)
                return None


# Global storage instance - singleton pattern
# This is initialized at import time and checks database readiness on each call
class _StorageProxy:
    """
    Proxy class that provides access to the SQLiteStorage singleton.
    Delegates all method calls to the underlying SQLiteStorage instance.
    """
    def __init__(self):
        self._instance: Optional[SQLiteStorage] = None

    def _ensure_initialized(self):
        """Ensure the storage instance is initialized."""
        if self._instance is None:
            if database.AsyncSessionLocal is None:
                raise RuntimeError(
                    "Database not initialized. "
                    "Ensure init_db() was called during application startup."
                )
            self._instance = SQLiteStorage()
            logger.info("SQLite storage initialized (lazy)")
        return self._instance

    def __getattr__(self, name):
        """Delegate attribute access to the underlying storage instance."""
        instance = self._ensure_initialized()
        return getattr(instance, name)


# Global storage proxy - this is what other modules import
storage = _StorageProxy()


def init_storage():
    """
    Initialize the global storage instance.
    This is called during application startup to eagerly initialize storage.
    """
    # Access any method to trigger initialization
    _ = storage._ensure_initialized()
    logger.info("Storage initialization complete")
    return storage


# For backwards compatibility, expose storage at module level
# It will be properly initialized when init_storage() is called
__all__ = ["SQLiteStorage", "InMemoryStorage", "storage", "init_storage"]


class InMemoryStorage:
    """
    In-memory storage for images and versions (kept for backwards compatibility).

    Deprecated: Use SQLiteStorage instead.
    """

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

    def update_version_crop(
        self,
        image_id: str,
        version_id: str,
        crop_data: CropData,
        scale: float = 1.0,
        pan: Optional[Pan] = None,
        aspectRatio: Optional[AspectRatio] = None,
    ) -> Optional[ImageVersion]:
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
            processedPath=None,
        )

    def update_version_processed(
        self, image_id: str, version_id: str, processed_path: str
    ) -> Optional[ImageVersion]:
        """Mark a version as processed"""
        image = self.get_image(image_id)
        if image:
            for version in image.versions:
                if version.id == version_id:
                    version.processed = True
                    version.processedPath = processed_path
                    return version
        return None