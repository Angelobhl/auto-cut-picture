'use client';

import { useImageList } from '../hooks/useImageList';
import { apiClient } from '../lib/api';
import { Trash2, Image as ImageIcon } from 'lucide-react';
import { cn } from '../lib/utils';

export function ImageList() {
  const { images, selectedImageId, setSelectedImageId, removeImage, loading } = useImageList();

  const handleDeleteImage = async (imageId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this image and all its versions?')) {
      await removeImage(imageId);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Images ({images.length})</h3>

      <div className="flex-1 overflow-y-auto space-y-2">
        {loading ? (
          <div className="text-center text-gray-500 text-sm py-4">Loading images...</div>
        ) : images.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-4">
            No images uploaded yet
          </div>
        ) : (
          images.map((image) => (
            <div
              key={image.id}
              onClick={() => {
                if (image.id) {
                  setSelectedImageId(image.id);
                }
              }}
              className={cn(
                'group relative p-2 rounded-md border transition-all cursor-pointer',
                selectedImageId === image.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-16 h-16 bg-gray-100 rounded overflow-hidden">
                  {apiClient.getThumbnailUrl(image.id) ? (
                    <img
                      src={apiClient.getThumbnailUrl(image.id)}
                      alt={image.filename}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <ImageIcon className="w-6 h-6" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {image.filename}
                  </div>
                  <div className="text-xs text-gray-500">
                    {image.dimensions.width} × {image.dimensions.height}
                  </div>
                  <div className="text-xs text-gray-500">
                    {image.versions.length} version{image.versions.length !== 1 ? 's' : ''}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteImage(image.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                  title="Delete image"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
