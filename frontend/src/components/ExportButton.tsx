'use client';

import { useImageList } from '../hooks/useImageList';
import { useImageVersions } from '../hooks/useImageVersions';
import { apiClient } from '../lib/api';
import { Download, Sparkles } from 'lucide-react';
import { useState } from 'react';

interface ExportButtonProps {
  onBatchProcess?: () => void;
}

export function ExportButton({ onBatchProcess }: ExportButtonProps) {
  const { images } = useImageList();
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  const handleBatchProcess = async () => {
    setProcessing(true);
    try {
      // Collect all version IDs
      const versionIds: string[] = [];
      images.forEach((image) => {
        image.versions.forEach((version) => {
          versionIds.push(`${image.id}:${version.id}`);
        });
      });

      // Process all images
      const imageIds = images.map((img) => img.id);
      await apiClient.batchProcess({ imageIds });

      onBatchProcess?.();
    } catch (error) {
      console.error('Batch process failed:', error);
      alert('Failed to process images');
    } finally {
      setProcessing(false);
    }
  };

  const handleBatchDownload = async () => {
    setLoading(true);
    try {
      // Collect all version IDs
      const versionIds: string[] = [];
      images.forEach((image) => {
        image.versions.forEach((version) => {
          versionIds.push(`${image.id}:${version.id}`);
        });
      });

      // Download as ZIP
      const blob = await apiClient.batchDownload({ versionIds });

      // Trigger download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cropped_images.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Batch download failed:', error);
      alert('Failed to download images');
    } finally {
      setLoading(false);
    }
  };

  const totalVersions = images.reduce((sum, img) => sum + img.versions.length, 0);
  const processedVersions = images.reduce(
    (sum, img) => sum + img.versions.filter((v) => v.processed).length,
    0
  );

  return (
    <div className="space-y-3">
      <button
        onClick={handleBatchProcess}
        disabled={images.length === 0 || processing}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg"
      >
        <Sparkles className="w-5 h-5" />
        {processing ? 'Processing...' : 'Process All Versions'}
      </button>

      <button
        onClick={handleBatchDownload}
        disabled={totalVersions === 0 || loading}
        className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all"
      >
        <Download className="w-5 h-5" />
        {loading ? 'Downloading...' : 'Download All'}
      </button>

      <div className="text-center text-sm text-gray-600">
        {processedVersions} / {totalVersions} versions processed
      </div>
    </div>
  );
}
