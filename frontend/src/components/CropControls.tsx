'use client';

import { useCropState } from '../hooks/useCropState';
import { useImageList } from '../hooks/useImageList';
import { useImageVersions } from '../hooks/useImageVersions';
import { Preset } from '../lib/types';
import { useState, useEffect } from 'react';

interface CropControlsProps {
  selectedPreset: Preset | null;
  onPresetSelect: (preset: Preset) => void;
}

export function CropControls({ selectedPreset, onPresetSelect }: CropControlsProps) {
  const { crop, scale, pan, setCrop, setScale, setPan, resetCrop } = useCropState();
  const { getSelectedImage } = useImageList();
  const { selectedVersionId, syncWithCropState, updateVersionAspectRatio } = useImageVersions();
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  // Sync crop changes to backend with debounce
  useEffect(() => {
    // Skip sync if this is a programmatic load from version data
    if (useCropState.getState().isLoadingFromVersion) {
      return;
    }

    if (debounceTimer) clearTimeout(debounceTimer);

    const timer = setTimeout(async () => {
      const selectedImage = getSelectedImage();
      if (selectedImage && selectedVersionId) {
        await syncWithCropState(selectedImage.id, selectedVersionId);
      }
    }, 500);

    setDebounceTimer(timer);

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [crop, scale, pan]);

  const handleCropChange = (field: keyof typeof crop, value: number) => {
    setCrop({ ...crop, [field]: value });
  };

  const handlePresetApply = () => {
    const selectedImage = getSelectedImage();
    if (selectedImage && selectedPreset) {
      resetCrop(selectedImage.dimensions, selectedPreset.aspectRatio);
    }
  };

  useEffect(() => {
    // Skip if this is a version switch - the crop should be loaded from version data, not reset
    if (useCropState.getState().isLoadingFromVersion) {
      return;
    }

    const selectedImage = getSelectedImage();
    if (selectedImage && selectedPreset) {
      resetCrop(selectedImage.dimensions, selectedPreset.aspectRatio);
      // Sync aspectRatio to the currently selected version
      if (selectedVersionId) {
        updateVersionAspectRatio(selectedVersionId, selectedPreset.aspectRatio);
      }
    }
  }, [selectedPreset?.id]);

  return (
    <div className="space-y-6">
      {/* Scale Control */}
      <div style={{display: 'none'}}>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Scale: {scale.toFixed(2)}x
        </label>
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.1"
          value={scale}
          onChange={(e) => setScale(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Crop Coordinates (Percentage) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          裁剪位置 (%)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">X</label>
            <input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={crop.x.toFixed(1)}
              onChange={(e) => handleCropChange('x', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Y</label>
            <input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={crop.y.toFixed(1)}
              onChange={(e) => handleCropChange('y', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          裁剪尺寸 (%)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">宽度</label>
            <input
              type="number"
              min="1"
              max="100"
              step="0.1"
              value={crop.width.toFixed(1)}
              onChange={(e) => handleCropChange('width', parseFloat(e.target.value) || 100)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">高度</label>
            <input
              type="number"
              min="1"
              max="100"
              step="0.1"
              value={crop.height.toFixed(1)}
              onChange={(e) => handleCropChange('height', parseFloat(e.target.value) || 100)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>
      </div>

      {/* Pan Controls */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          平移偏移 (%)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Pan X</label>
            <input
              type="number"
              min="-50"
              max="50"
              step="0.1"
              value={pan.x.toFixed(1)}
              onChange={(e) => setPan({ ...pan, x: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Pan Y</label>
            <input
              type="number"
              min="-50"
              max="50"
              step="0.1"
              value={pan.y.toFixed(1)}
              onChange={(e) => setPan({ ...pan, y: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>
      </div>

      {/* Reset Button */}
      <button
        style={{display: 'none'}}
        onClick={handlePresetApply}
        disabled={!selectedPreset}
        className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        应用预设到裁剪框
      </button>
    </div>
  );
}
