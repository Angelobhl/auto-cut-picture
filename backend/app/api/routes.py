from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

from ..models import (
    Image, ImageVersion, VersionCreateRequest, CropUpdateRequest,
    BatchProcessRequest, BatchDownloadRequest, AnalyzeRequest, AnalyzeResponse,
    ImageDimensions
)
from ..services.image_processor import ImageProcessor
from ..services.composition_api import CompositionAPI
from ..services.storage import storage
from ..config.settings import settings

router = APIRouter()

# Initialize services
image_processor = ImageProcessor(storage_path=settings.STORAGE_PATH)
composition_api = CompositionAPI()


@router.post("/images/upload", response_model=List[Image])
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload multiple images"""
    uploaded_images = []

    logger.info(f"Received {len(files)} files for upload")

    for file in files:
        try:
            logger.info(f"Processing file: {file.filename}, size: {file.size}")

            # Read file data
            file_data = await file.read()
            logger.info(f"Read {len(file_data)} bytes")

            # Save image and get info
            image_id, original_path, dimensions = image_processor.save_upload(
                file_data, file.filename
            )
            logger.info(f"Saved image: {image_id}, path: {original_path}, dimensions: {dimensions}")

            # Create default version
            default_version = storage.create_default_version(image_id, ImageDimensions(
                width=dimensions[0],
                height=dimensions[1]
            ))

            # Create image object
            image = Image(
                id=image_id,
                filename=file.filename,
                originalPath=original_path,
                dimensions=ImageDimensions(
                    width=dimensions[0],
                    height=dimensions[1]
                ),
                versions=[default_version]
            )

            # Store in memory
            storage.add_image(image)
            uploaded_images.append(image)
            logger.info(f"Successfully processed {file.filename}")

        except Exception as e:
            import traceback
            logger.error(f"Error uploading {file.filename}: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(status_code=400, detail=f"Error uploading {file.filename}: {str(e)}")

    logger.info(f"Upload complete: {len(uploaded_images)} images")
    return uploaded_images

    return uploaded_images


@router.get("/images", response_model=List[Image])
async def get_images():
    """Get all images"""
    return storage.get_all_images()


@router.get("/images/{image_id}", response_model=Image)
async def get_image(image_id: str):
    """Get a specific image"""
    image = storage.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.get("/images/{image_id}/versions", response_model=List[ImageVersion])
async def get_image_versions(image_id: str):
    """Get all versions for an image"""
    image = storage.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image.versions


@router.post("/images/{image_id}/versions", response_model=ImageVersion)
async def create_version(image_id: str, request: VersionCreateRequest):
    """Create a new version for an image"""
    image = storage.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get image dimensions
    dimensions = image.dimensions

    # Calculate default crop based on aspect ratio
    if request.cropData:
        # Calculate crop that matches the aspect ratio
        target_ratio = request.cropData.width / request.cropData.height
        image_ratio = dimensions.width / dimensions.height

        if image_ratio > target_ratio:
            # Image is wider - crop sides
            crop_height = request.cropData.height
            crop_width = crop_height * target_ratio / image_ratio
            crop_x = request.cropData.x
            crop_y = request.cropData.y
        else:
            # Image is taller - crop top/bottom
            crop_width = request.cropData.width
            crop_height = crop_width * image_ratio / target_ratio
            crop_x = request.cropData.x
            crop_y = request.cropData.y

        crop_data = {
            "x": crop_x,
            "y": crop_y,
            "width": crop_width,
            "height": crop_height
        }
        # crop_data = {
        #     "x": request.cropData.x,
        #     "y": request.cropData.y,
        #     "width": request.cropData.width,
        #     "height": request.cropData.height
        # }
    else:
        # Freeform - use full image
        crop_data = {
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100
        }

    version = ImageVersion(
        id=str(uuid.uuid4()),
        imageId=image_id,
        name=request.name,
        aspectRatio=request.aspectRatio,
        cropData=crop_data,
        scale=1.0,
        pan={"x": 0, "y": 0},
        processed=False,
        processedPath=None
    )

    storage.add_version(image_id, version)
    return version


@router.post("/images/{image_id}/versions/{version_id}/crop", response_model=ImageVersion)
async def update_crop(image_id: str, version_id: str, request: CropUpdateRequest):
    """Update crop data for a version"""
    version = storage.update_version_crop(
        image_id, version_id,
        request.cropData,
        request.scale,
        request.pan,
        request.aspectRatio
    )

    if not version:
        raise HTTPException(status_code=404, detail="Image or version not found")

    return version


@router.delete("/images/{image_id}/versions/{version_id}")
async def delete_version(image_id: str, version_id: str):
    """Delete a version"""
    # Delete from storage
    success = storage.delete_version(image_id, version_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image or version not found")

    # Delete processed file
    image_processor.delete_version(image_id, version_id)

    return {"message": "Version deleted"}


@router.post("/images/{image_id}/analyze", response_model=AnalyzeResponse)
async def analyze_image(image_id: str, request: AnalyzeRequest):
    """Analyze image for smart composition"""
    image = storage.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Analyze image
    result = await composition_api.analyze_image(
        image.originalPath,
        image_id,
        request.aspectRatios
    )

    return result


@router.post("/images/batch-process")
async def batch_process(request: BatchProcessRequest):
    """Process multiple images/versions"""
    processed_versions = []

    for image_id in request.imageIds:
        image = storage.get_image(image_id)
        if not image:
            continue

        for version in image.versions:
            try:
                # Process image using actual crop dimensions (no forced resize)
                processed_path = image_processor.crop_image(
                    image_id,
                    version.id,
                    version.cropData.dict(),
                    version.scale,
                    version.pan.dict() if version.pan else None,
                    None,  # target_width - use actual crop dimensions
                    None,  # target_height - use actual crop dimensions
                    preserve_exif=True
                )

                # Update version
                storage.update_version_processed(image_id, version.id, processed_path)

                processed_versions.append({
                    "imageId": image_id,
                    "versionId": version.id,
                    "path": processed_path
                })

            except Exception as e:
                continue

    return {
        "message": f"Processed {len(processed_versions)} versions",
        "versions": processed_versions
    }


@router.get("/images/{image_id}/versions/{version_id}/download")
async def download_version(image_id: str, version_id: str):
    """Download a processed version"""
    processed_path = image_processor.get_processed_path(image_id, version_id)

    if not processed_path:
        # Try to process on-demand
        image = storage.get_image(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        version = storage.get_version(image_id, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Process image
        processed_path = image_processor.crop_image(
            image_id,
            version_id,
            version.cropData.dict(),
            version.scale,
            version.pan.dict() if version.pan else None,
            preserve_exif=True
        )

        storage.update_version_processed(image_id, version_id, processed_path)

    return FileResponse(
        processed_path,
        media_type="image/jpeg",
        filename=f"{image_id}_{version_id}.jpg"
    )


@router.post("/images/batch-download")
async def batch_download(request: BatchDownloadRequest):
    """Download multiple versions as ZIP"""
    version_ids = []
    for version_id_str in request.versionIds:
        # Parse "imageId:versionId" format
        parts = version_id_str.split(":")
        if len(parts) == 2:
            version_ids.append((parts[0], parts[1]))
        else:
            version_ids.append((version_id_str, version_id_str))

    # Create ZIP file
    zip_path = image_processor.create_batch_zip(version_ids)

    if not zip_path:
        raise HTTPException(status_code=400, detail="Failed to create ZIP file")

    # Clean up old ZIPs
    image_processor.cleanup_old_zips()

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="cropped_images.zip"
    )


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image and all its versions"""
    image = storage.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete from storage
    storage.delete_image(image_id)

    # Delete files
    image_processor.delete_image(image_id)

    return {"message": "Image deleted"}


@router.delete("/images")
async def delete_all_images():
    """Delete all images and their versions"""
    # Get all images before clearing storage
    all_images = storage.get_all_images()

    # Clear storage
    storage.clear_all()

    # Delete all files
    for image in all_images:
        try:
            image_processor.delete_image(image.id)
        except Exception as e:
            logger.error(f"Error deleting files for image {image.id}: {e}")

    return {"message": f"Deleted {len(all_images)} images"}
