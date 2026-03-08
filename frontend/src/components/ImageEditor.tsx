'use client';

import { useState, useEffect, useRef } from 'react';
import { useImageVersions } from '../hooks/useImageVersions';
import { useImageList } from '../hooks/useImageList';
import { useCropState } from '../hooks/useCropState';
import { apiClient } from '../lib/api';
import { Preset } from '../lib/types';
import { cn } from '../lib/utils';

interface ImageEditorProps {
  imageId: string;
  onVersionSelect?: (version: any) => void;
}

export function ImageEditor({ imageId, onVersionSelect }: ImageEditorProps) {
  const { selectedVersionId, getSelectedVersion } = useImageVersions();
  const { crop, setCrop, resetCrop } = useCropState();
  const [selectedPreset, setSelectedPreset] = useState<Preset | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeHandle, setResizeHandle] = useState<string | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const selectedVersion = getSelectedVersion();

  const { getSelectedImage } = useImageList();
  const selectedImage = getSelectedImage();

  // Load versions when image changes
  useEffect(() => {
    if (imageId) {
      useImageVersions.getState().loadVersions(imageId);
    }
  }, [imageId]);

  // Load version crop data when version changes
  useEffect(() => {
    if (selectedVersion) {
      setCrop(selectedVersion.cropData);
      useCropState.getState().setScale(selectedVersion.scale);
      useCropState.getState().setPan(selectedVersion.pan);
    }
  }, [selectedVersionId]);

  // Find preset based on version name
  const presets: Preset[] = [
    { id: "square", name: "Square (1:1)", aspectRatio: { width: 1, height: 1 }, category: "social" },
    { id: "landscape-4-3", name: "Landscape (4:3)", aspectRatio: { width: 4, height: 3 }, category: "standard" },
    { id: "widescreen-16-9", name: "Widescreen (16:9)", aspectRatio: { width: 16, height: 9 }, category: "video" },
    { id: "portrait-9-16", name: "Portrait (9:16)", aspectRatio: { width: 9, height: 16 }, category: "social" },
    { id: "instagram-feed", name: "Instagram Feed (4:5)", aspectRatio: { width: 4, height: 5 }, category: "social" },
    { id: "freeform", name: "Freeform", aspectRatio: null, category: "custom" }
  ];
  const matchingPreset = presets.find((p) => p.name === selectedVersion?.name);
  useEffect(() => {
    setSelectedPreset(matchingPreset || null);
  }, [selectedVersionId]);

  const handleMouseDown = (e: React.MouseEvent, action: string, handle?: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (action === 'drag') {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    } else if (action === 'resize' && handle) {
      setIsResizing(true);
      setResizeHandle(handle);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!imageId) return;

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const imageWidth = rect.width;
    const imageHeight = rect.height;

    if (isDragging) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;

      const newCrop = {
        ...crop,
        x: Math.max(0, Math.min(100 - crop.width, crop.x + (dx / imageWidth) * 100)),
        y: Math.max(0, Math.min(100 - crop.height, crop.y + (dy / imageHeight) * 100)),
      };

      setCrop(newCrop);
      setDragStart({ x: e.clientX, y: e.clientY });
    } else if (isResizing && resizeHandle) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;

      let newCrop = { ...crop };

      switch (resizeHandle) {
        case 'nw':
          newCrop.x = Math.max(0, crop.x + (dx / imageWidth) * 100);
          newCrop.y = Math.max(0, crop.y + (dy / imageHeight) * 100);
          newCrop.width = Math.max(1, crop.width - (dx / imageWidth) * 100);
          newCrop.height = Math.max(1, crop.height - (dy / imageHeight) * 100);
          break;
        case 'ne':
          newCrop.y = Math.max(0, crop.y + (dy / imageHeight) * 100);
          newCrop.width = Math.max(1, crop.width + (dx / imageWidth) * 100);
          newCrop.height = Math.max(1, crop.height - (dy / imageHeight) * 100);
          break;
        case 'sw':
          newCrop.x = Math.max(0, crop.x + (dx / imageWidth) * 100);
          // newCrop.y = Math.max(0, crop.y + (dy / imageHeight) * 100);
          newCrop.width = Math.max(1, crop.width - (dx / imageWidth) * 100);
          newCrop.height = Math.max(1, crop.height + (dy / imageHeight) * 100);
          break;
        case 'se':
          // newCrop.x = Math.max(0, crop.x + (dx / imageWidth) * 100);
          // newCrop.y = Math.max(0, crop.y + (dy / imageHeight) * 100);
          newCrop.width = Math.max(1, crop.width + (dx / imageWidth) * 100);
          newCrop.height = Math.max(1, crop.height + (dy / imageHeight) * 100);
          break;
      }

      setCrop(newCrop);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
    setResizeHandle(null);
  };

  if (!imageId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium mb-2">No image selected</p>
          <p className="text-sm">Select an image from the sidebar to start editing</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Dimensions Display */}
      <div className="mt-3 flex items-center justify-between text-sm text-gray-600">
        <div>
          Original: {selectedImage?.dimensions?.width || 'No image selected'} × {selectedImage?.dimensions?.height || 'No image selected'}px
        </div>
        <div>
          Crop: {selectedImage && crop.width
            ? `${Math.round((crop.width / 100) * (selectedImage.dimensions.width || 0))} × ${Math.round((crop.height / 100) * (selectedImage.dimensions.height || 0))}px`
            : 'No image selected'}
        </div>
      </div>

      {/* Canvas Area */}
      <div
        ref={canvasRef}
        className="flex-1 flex items-center justify-center bg-gray-900 rounded-lg overflow-hidden relative"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div className="relative" style={{ maxWidth: '100%', maxHeight: '100%' }}>
          {/* Original Image */}
          <img
            ref={imageRef}
            src={apiClient.getOriginalUrl(selectedImage ? selectedImage.originalPath : '')}
            alt={selectedImage ? selectedImage.filename : ''}
            className="max-w-full max-h-[calc(100vh-200px)] object-contain"
            draggable={false}
          />

          {/* Crop Box */}
          <div
            className={cn(
              'absolute border-2 border-white cursor-move',
              isDragging && 'cursor-grabbing'
            )}
            style={{
              left: `${crop.x}%`,
              top: `${crop.y}%`,
              width: `${crop.width}%`,
              height: `${crop.height}%`,
              boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.5)',
            }}
            onMouseDown={(e) => handleMouseDown(e, 'drag')}
          >
            {/* Resize Handles */}
            <div
              className="absolute -top-1.5 -left-1.5 w-3 h-3 bg-white border border-gray-300 cursor-nwse-resize"
              onMouseDown={(e) => handleMouseDown(e, 'resize', 'nw')}
            />
            <div
              className="absolute -top-1.5 -right-1.5 w-3 h-3 bg-white border border-gray-300 cursor-nesw-resize"
              onMouseDown={(e) => handleMouseDown(e, 'resize', 'ne')}
            />
            <div
              className="absolute -bottom-1.5 -left-1.5 w-3 h-3 bg-white border border-gray-300 cursor-nesw-resize"
              onMouseDown={(e) => handleMouseDown(e, 'resize', 'sw')}
            />
            <div
              className="absolute -bottom-1.5 -right-1.5 w-3 h-3 bg-white border border-gray-300 cursor-nwse-resize"
              onMouseDown={(e) => handleMouseDown(e, 'resize', 'se')}
            />

            {/* Grid Lines (Rule of Thirds) */}
            <div className="absolute top-0 bottom-0 left-1/3 w-px bg-white/30 pointer-events-none" />
            <div className="absolute top-0 bottom-0 left-2/3 w-px bg-white/30 pointer-events-none" />
            <div className="absolute top-1/3 bottom-0 left-0 right-0 w-px h-px bg-white/30 pointer-events-none" />
            <div className="absolute left-0 right-0 top-1/3 h-px bg-white/30 pointer-events-none" />
            <div className="absolute left-0 right-0 top-2/3 h-px bg-white/30 pointer-events-none" />
          </div>

          {/* Info Overlay */}
          <div className="absolute bottom-4 left-4 right-4 flex justify-between" style={{display: (isDragging || isResizing) ? 'none' : ''}}>
            <div className="bg-black/70 backdrop-blur-sm text-white px-3 py-1.5 rounded text-sm">
              {selectedImage?.filename || 'No image selected'}
            </div>
            <div className="bg-black/70 backdrop-blur-sm text-white px-3 py-1.5 rounded text-sm">
              {selectedVersion?.name || 'No version selected'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
