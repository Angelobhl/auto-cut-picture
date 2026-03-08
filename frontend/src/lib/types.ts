export interface Preset {
  id: string;
  name: string;
  aspectRatio: { width: number; height: number } | null;
  category: string;
}

export interface CropData {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Pan {
  x: number;
  y: number;
}

export interface ImageVersion {
  id: string;
  imageId: string;
  name: string;
  aspectRatio: { width: number; height: number } | null;
  cropData: CropData;
  scale: number;
  pan: Pan;
  processed: boolean;
  processedPath: string | null;
}

export interface ImageDimensions {
  width: number;
  height: number;
}

export interface Image {
  id: string;
  filename: string;
  originalPath: string;
  dimensions: ImageDimensions;
  versions: ImageVersion[];
}

export interface UploadResponse {
  images: Image[];
}

export interface VersionCreateRequest {
  name: string;
  cropData?: CropData;
  aspectRatio?: { width: number; height: number };
}

export interface CropUpdateRequest {
  cropData: CropData;
  scale?: number;
  pan?: Pan;
}

export interface BatchProcessRequest {
  imageIds: string[];
}

export interface BatchDownloadRequest {
  versionIds: string[];
}
