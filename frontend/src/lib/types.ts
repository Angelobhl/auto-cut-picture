export interface AspectRatio {
  width: number;
  height: number;
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

export interface ImageDimensions {
  width: number;
  height: number;
}

export interface Preset {
  id: string;
  name: string;
  aspectRatio: AspectRatio | null;
  category: string;
}

export interface ImageVersion {
  id: string;
  imageId: string;
  name: string;
  aspectRatio: AspectRatio | null;
  cropData: CropData;
  scale: number;
  pan: Pan;
  processed: boolean;
  processedPath: string | null;
}

export interface Image {
  id: string;
  filename: string;
  originalPath: string;
  dimensions: ImageDimensions;
  versions: ImageVersion[];
}

export interface VersionCreateRequest {
  name: string;
  cropData: CropData | null;
  aspectRatio: AspectRatio | null;
}

export interface CropUpdateRequest {
  cropData: CropData;
  scale?: number;
  pan: Pan | null;
  aspectRatio?: AspectRatio | null;
}

export interface BatchProcessRequest {
  imageIds: string[];
}

export interface BatchDownloadRequest {
  versionIds: string[];
}

export interface AnalyzeRequest {
  aspectRatios: AspectRatio[] | null;
}

export interface AnalysisResult {
  versionId: string;
  name: string;
  cropData: CropData;
}

export interface AnalyzeResponse {
  imageId: string;
  results: AnalysisResult[];
}
