import {
  Image,
  ImageVersion,
  VersionCreateRequest,
  CropUpdateRequest,
  BatchProcessRequest,
  BatchDownloadRequest,
  AnalyzeRequest,
  AnalyzeResponse,
  CropData,
  Pan,
  ImageDimensions,
  AspectRatio,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async uploadImages(files: File[]): Promise<Image[]> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/api/images/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload images');
    }

    return response.json();
  }

  async getImages(): Promise<Image[]> {
    return this.request<Image[]>('/api/images');
  }

  async getImage(id: string): Promise<Image> {
    return this.request<Image>(`/api/images/${id}`);
  }

  async getVersions(imageId: string): Promise<ImageVersion[]> {
    return this.request<ImageVersion[]>(`/api/images/${imageId}/versions`);
  }

  async createVersion(imageId: string, request: VersionCreateRequest): Promise<ImageVersion> {
    return this.request<ImageVersion>(`/api/images/${imageId}/versions`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async updateCrop(
    imageId: string,
    versionId: string,
    request: CropUpdateRequest
  ): Promise<ImageVersion> {
    return this.request<ImageVersion>(
      `/api/images/${imageId}/versions/${versionId}/crop`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  async deleteVersion(imageId: string, versionId: string): Promise<void> {
    return this.request<void>(`/api/images/${imageId}/versions/${versionId}`, {
      method: 'DELETE',
    });
  }

  async analyzeImage(imageId: string, request: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>(`/api/images/${imageId}/analyze`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async batchProcess(request: BatchProcessRequest): Promise<{ message: string; versions: any[] }> {
    return this.request<{ message: string; versions: any[] }>('/api/images/batch-process', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async downloadVersion(imageId: string, versionId: string): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/api/images/${imageId}/versions/${versionId}/download`
    );
    if (!response.ok) {
      throw new Error('Failed to download version');
    }
    return response.blob();
  }

  async batchDownload(request: BatchDownloadRequest): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/images/batch-download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error('Failed to download batch');
    }
    return response.blob();
  }

  async deleteImage(imageId: string): Promise<void> {
    return this.request<void>(`/api/images/${imageId}`, {
      method: 'DELETE',
    });
  }

  async deleteAllImages(): Promise<void> {
    return this.request<void>('/api/images', {
      method: 'DELETE',
    });
  }

  getThumbnailUrl(imageId: string): string {
    return `${this.baseUrl}/thumbnails/${imageId}_thumb.jpg`;
  }

  getProcessedUrl(imageId: string, versionId: string): string {
    return `${this.baseUrl}/processed/${imageId}_${versionId}_cropped.jpg`;
  }

  getOriginalUrl(imagePath: string): string {
    // Extract filename from path and construct URL
    const filename = imagePath.split('/').pop();
    return `${this.baseUrl}/uploads/${filename}`;
  }
}

export const apiClient = new ApiClient();
