from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CropData(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Pan(BaseModel):
    x: float
    y: float


class ImageDimensions(BaseModel):
    width: int
    height: int


class AspectRatio(BaseModel):
    width: int
    height: int


class ImageVersion(BaseModel):
    id: str
    imageId: str
    name: str
    aspectRatio: Optional[AspectRatio] = None
    cropData: CropData
    scale: float = 1.0
    pan: Pan
    processed: bool = False
    processedPath: Optional[str] = None


class Image(BaseModel):
    id: str
    filename: str
    originalPath: str
    dimensions: ImageDimensions
    versions: List[ImageVersion] = []


class VersionCreateRequest(BaseModel):
    name: str
    cropData: Optional[CropData] = None
    aspectRatio: Optional[AspectRatio] = None


class CropUpdateRequest(BaseModel):
    cropData: CropData
    scale: Optional[float] = 1.0
    pan: Optional[Pan] = None
    aspectRatio: Optional[AspectRatio] = None


class BatchProcessRequest(BaseModel):
    imageIds: List[str]


class BatchDownloadRequest(BaseModel):
    versionIds: List[str]


class AnalyzeRequest(BaseModel):
    aspectRatios: Optional[List[AspectRatio]] = None


class AnalysisResult(BaseModel):
    versionId: str
    name: str
    cropData: CropData
    aspectRatio: Optional[AspectRatio] = None


class AnalyzeResponse(BaseModel):
    imageId: str
    results: List[AnalysisResult]
