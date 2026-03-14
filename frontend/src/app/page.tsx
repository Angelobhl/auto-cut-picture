'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useImageList } from '../hooks/useImageList';
import { useImageVersions } from '../hooks/useImageVersions';
import { ImageList } from '../components/ImageList';
import { VersionList } from '../components/VersionList';
import { ImageEditor } from '../components/ImageEditor';
import { CropControls } from '../components/CropControls';
import { PresetSelector, PRESETS } from '../components/PresetSelector';
import { ExportButton } from '../components/ExportButton';
import { Upload, Sparkles, RefreshCw, Trash2 } from 'lucide-react';
import { apiClient } from '../lib/api';
import { Preset } from '../lib/types';

export default function Home() {
  const { images, selectedImageId, deleteAllImages, loadImages, loading, addImages } = useImageList();
  const { selectedVersionId, versions } = useImageVersions();
  const [initialLoading, setInitialLoading] = useState(true);
  const [isUploadMode, setIsUploadMode] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<Preset | null>(null);

  // Load images on mount
  useEffect(() => {
    const init = async () => {
      await loadImages();
      setInitialLoading(false);
    };
    init();
  }, [loadImages]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    try {
      const uploadedImages = await apiClient.uploadImages(acceptedFiles);
      addImages(uploadedImages);
      setIsUploadMode(false);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('上传图片失败');
    }
  }, [addImages]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif'],
    },
    multiple: true,
  });

  const handleAnalyze = async () => {
    // alert('Coming Soon');
    // return ;

    const selectedImage = useImageList.getState().getSelectedImage();
    if (!selectedImage) {
      alert('请先选择一张图片');
      return;
    }

    try {
      await useImageVersions.getState().analyzeImage(selectedImage.id, {
        aspectRatios: [
          { width: 1, height: 1 },
          { width: 16, height: 9 },
          { width: 9, height: 16 },
        ],
      });
      alert('智能分析完成！已创建新版本。');
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('分析图片失败');
    }
  };

  const handleBatchProcess = () => {
    // Refresh image list to show processed versions
    useImageList.getState().loadImages();
  };

  const handleDeleteAllImages = async () => {
    if (confirm('确定要删除所有图片和版本吗？此操作无法撤销。')) {
      await deleteAllImages();
      setIsUploadMode(false); // Will show upload zone since images.length === 0
    }
  };

  // Sync preset selection with selected version
  useEffect(() => {
    const selectedVersion = versions.find((v) => v.id === selectedVersionId);
    if (!selectedVersion) {
      setSelectedPreset(null);
      return;
    }

    // Find matching preset based on aspectRatio
    const matchingPreset = PRESETS.find((preset) => {
      if (!preset.aspectRatio && !selectedVersion.aspectRatio) return true;
      if (!preset.aspectRatio || !selectedVersion.aspectRatio) return false;
      return (
        preset.aspectRatio.width === selectedVersion.aspectRatio.width &&
        preset.aspectRatio.height === selectedVersion.aspectRatio.height
      );
    });

    setSelectedPreset(matchingPreset || null);
  }, [selectedVersionId, versions]);

  // Show loading screen during initial load
  if (initialLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  // Show upload screen if no images or user clicked upload button
  if (images.length === 0 || isUploadMode) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 p-8">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              自动裁图
            </h1>
            <p className="text-gray-600 text-lg">
              精准裁剪与构图
            </p>
          </div>

          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
              transition-all duration-200
              ${isDragActive
                ? 'border-blue-500 bg-blue-50 scale-[1.02]'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-lg text-gray-700">将图片拖放到这里...</p>
            ) : (
              <div>
                <p className="text-lg text-gray-700 mb-2">
                  拖放图片到此处，或点击选择
                </p>
                <p className="text-sm text-gray-500">
                  支持 PNG、JPG、JPEG、WebP、GIF
                </p>
              </div>
            )}
          </div>

          {images.length > 0 && (
            <button
              onClick={() => setIsUploadMode(false)}
              className="mt-6 w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              返回编辑（{images.length} 张图片）
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900">自动裁图</h1>
            <button
              onClick={() => setIsUploadMode(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              上传图片
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDeleteAllImages}
              className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              清空全部
            </button>
            <button
              onClick={handleAnalyze}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              智能分析
            </button>
            <button
              onClick={handleBatchProcess}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              刷新
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Images & Versions */}
        <aside className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Image List */}
            <div className="flex-1 overflow-y-auto p-4 border-b border-gray-200">
              <ImageList />
            </div>

            {/* Version List */}
            <div className="flex-1 overflow-y-auto p-4">
              <VersionList imageId={selectedImageId} />
            </div>
          </div>
        </aside>

        {/* Center - Image Editor */}
        <section className="flex-1 p-6 overflow-hidden">
          <ImageEditor imageId={selectedImageId} />
        </section>

        {/* Right Sidebar - Controls */}
        <aside className="w-80 bg-white border-l border-gray-200 p-6 overflow-y-auto">
          <div className="space-y-8">
            {/* Preset Selector */}
            <div>
              <PresetSelector
                selectedPreset={selectedPreset}
                onPresetSelect={setSelectedPreset}
              />
            </div>

            {/* Crop Controls */}
            <div>
              <CropControls
                selectedPreset={selectedPreset}
                onPresetSelect={setSelectedPreset}
              />
            </div>

            {/* Export */}
            <div className="pt-6 border-t border-gray-200">
              <ExportButton onBatchProcess={handleBatchProcess} />
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}
