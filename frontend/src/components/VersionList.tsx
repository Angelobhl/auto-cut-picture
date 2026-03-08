'use client';

import { useImageVersions } from '../hooks/useImageVersions';
import { Preset } from '../lib/types';
import { Plus, Trash2, CheckCircle, Circle } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../lib/utils';

interface VersionListProps {
  imageId: string;
  onVersionSelect?: (version: any) => void;
}

export function VersionList({ imageId, onVersionSelect }: VersionListProps) {
  const { versions, selectedVersionId, setSelectedVersionId, createVersion, deleteVersion, loading } = useImageVersions();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newVersionName, setNewVersionName] = useState('');

  const handleCreateVersion = async () => {
    if (!imageId) {
      console.warn('Cannot create version: no image selected');
      return;
    }
    if (!newVersionName.trim()) return;

    await createVersion(imageId, { name: newVersionName });
    setNewVersionName('');
    setShowCreateDialog(false);
  };

  const handleDeleteVersion = async (versionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!imageId) {
      console.warn('Cannot delete version: no image selected');
      return;
    }
    if (confirm('Are you sure you want to delete this version?')) {
      await deleteVersion(imageId, versionId);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Versions</h3>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
          title="Create new version"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {showCreateDialog && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md border border-gray-200">
          <input
            type="text"
            placeholder="Version name (e.g., 1:1 Square)"
            value={newVersionName}
            onChange={(e) => setNewVersionName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreateVersion()}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2"
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreateVersion}
              className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm"
            >
              Create
            </button>
            <button
              onClick={() => {
                setShowCreateDialog(false);
                setNewVersionName('');
              }}
              className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-md text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-2">
        {loading ? (
          <div className="text-center text-gray-500 text-sm py-4">Loading versions...</div>
        ) : versions.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-4">No versions yet</div>
        ) : (
          versions.map((version) => (
            <div
              key={version.id}
              onClick={() => {
                if (version.id) {
                  setSelectedVersionId(version.id);
                  onVersionSelect?.(version);
                }
              }}
              className={cn(
                'group relative p-3 rounded-md border transition-all cursor-pointer',
                selectedVersionId === version.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {version.processed ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <Circle className="w-4 h-4 text-gray-400" />
                  )}
                  <div>
                    <div className="text-sm font-medium text-gray-900">{version.name}</div>
                    {version.aspectRatio && (
                      <div className="text-xs text-gray-500">
                        {version.aspectRatio.width}:{version.aspectRatio.height}
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteVersion(version.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                  title="Delete version"
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
