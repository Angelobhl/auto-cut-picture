"""
SQLAlchemy ORM models for the image cropping application.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime

from .database import Base


class ImageModel(AsyncAttrs, Base):
    """
    SQLAlchemy model for images table.

    Maps to the Pydantic Image model:
    - id: UUID string
    - filename: original file name
    - originalPath: storage path of original image
    - dimensions: width and height (stored as separate columns)
    - versions: list of ImageVersion objects
    """
    __tablename__ = "images"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to versions
    versions = relationship(
        "ImageVersionModel",
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="ImageVersionModel.created_at"
    )

    def __repr__(self):
        return f"<ImageModel(id={self.id}, filename={self.filename})>"


class ImageVersionModel(AsyncAttrs, Base):
    """
    SQLAlchemy model for image_versions table.

    Maps to the Pydantic ImageVersion model:
    - id: UUID string
    - imageId: foreign key to images table
    - name: version name
    - aspectRatio: stored as aspect_width and aspect_height
    - cropData: stored as crop_x, crop_y, crop_width, crop_height
    - scale: zoom scale
    - pan: stored as pan_x, pan_y
    - processed: boolean flag
    - processedPath: path to processed file
    """
    __tablename__ = "image_versions"

    id = Column(String(36), primary_key=True)
    image_id = Column(String(36), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    aspect_width = Column(Integer, nullable=True)
    aspect_height = Column(Integer, nullable=True)
    crop_x = Column(Float, nullable=False)
    crop_y = Column(Float, nullable=False)
    crop_width = Column(Float, nullable=False)
    crop_height = Column(Float, nullable=False)
    scale = Column(Float, default=1.0)
    pan_x = Column(Float, default=0)
    pan_y = Column(Float, default=0)
    processed = Column(Boolean, default=False)
    processed_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to image
    image = relationship("ImageModel", back_populates="versions")

    def __repr__(self):
        return f"<ImageVersionModel(id={self.id}, name={self.name}, image_id={self.image_id})>"