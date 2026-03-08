import { create } from 'zustand';
import { CropData, Pan, ImageDimensions } from '../lib/types';

interface CropState {
  crop: CropData;
  scale: number;
  pan: Pan;
  setCrop: (crop: CropData) => void;
  setScale: (scale: number) => void;
  setPan: (pan: Pan) => void;
  resetCrop: (dimensions: ImageDimensions, aspectRatio?: { width: number; height: number } | null) => void;
  updateCropFromPixels: (
    pixels: { x: number; y: number; width: number; height: number },
    dimensions: ImageDimensions
  ) => void;
}

export const useCropState = create<CropState>((set) => ({
  crop: { x: 0, y: 0, width: 100, height: 100 },
  scale: 1,
  pan: { x: 0, y: 0 },

  setCrop: (crop) => set({ crop }),
  setScale: (scale) => set({ scale }),
  setPan: (pan) => set({ pan }),

  resetCrop: (dimensions, aspectRatio) => {
    if (aspectRatio) {
      const targetRatio = aspectRatio.width / aspectRatio.height;
      const imageRatio = dimensions.width / dimensions.height;

      let cropWidth, cropHeight, cropX, cropY;

      if (imageRatio > targetRatio) {
        // Image is wider - crop sides
        cropHeight = 100;
        cropWidth = cropHeight * targetRatio / imageRatio;
        cropX = (100 - cropWidth) / 2;
        cropY = 0;
      } else {
        // Image is taller - crop top/bottom
        cropWidth = 100;
        cropHeight = cropWidth * imageRatio / targetRatio;
        cropX = 0;
        cropY = (100 - cropHeight) / 2;
      }

      set({
        crop: { x: cropX, y: cropY, width: cropWidth, height: cropHeight },
        scale: 1,
        pan: { x: 0, y: 0 },
      });
    } else {
      // Freeform - use full image
      set({
        crop: { x: 0, y: 0, width: 100, height: 100 },
        scale: 1,
        pan: { x: 0, y: 0 },
      });
    }
  },

  updateCropFromPixels: (pixels, dimensions) => {
    const crop = {
      x: (pixels.x / dimensions.width) * 100,
      y: (pixels.y / dimensions.height) * 100,
      width: (pixels.width / dimensions.width) * 100,
      height: (pixels.height / dimensions.height) * 100,
    };
    set({ crop });
  },
}));
