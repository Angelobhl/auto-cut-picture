import { create } from 'zustand';
import { ImageVersion, VersionCreateRequest, AnalyzeRequest } from '../lib/types';
import { apiClient } from '../lib/api';
import { useCropState } from './useCropState';

interface ImageVersionsState {
  versions: ImageVersion[];
  selectedVersionId: string | null;
  loading: boolean;
  error: string | null;
  setVersions: (imageId: string, versions: ImageVersion[]) => void;
  setSelectedVersionId: (id: string | null) => void;
  loadVersions: (imageId: string) => Promise<void>;
  createVersion: (imageId: string, request: VersionCreateRequest) => Promise<void>;
  updateCrop: (imageId: string, versionId: string, cropData: any, scale?: number, pan?: any) => Promise<void>;
  deleteVersion: (imageId: string, versionId: string) => Promise<void>;
  analyzeImage: (imageId: string, request: AnalyzeRequest) => Promise<void>;
  syncWithCropState: (imageId: string, versionId: string) => Promise<void>;
  getSelectedVersion: () => ImageVersion | undefined;
  getVersionById: (versionId: string) => ImageVersion | undefined;
}

export const useImageVersions = create<ImageVersionsState>((set, get) => ({
  versions: [],
  selectedVersionId: null,
  loading: false,
  error: null,

  setVersions: (imageId, versions) => {
    set({ versions });
    // Select first version if none selected
    const state = get();
    if (versions.length > 0 && !state.selectedVersionId) {
      set({ selectedVersionId: versions[0].id });
    }
  },

  setSelectedVersionId: (id) => set({ selectedVersionId: id }),

  loadVersions: async (imageId) => {
    set({ loading: true, error: null });
    try {
      const versions = await apiClient.getVersions(imageId);
      set({ versions, loading: false });
      // Select first version if none selected
      const state = get();
      if (versions.length > 0 && !state.selectedVersionId) {
        set({ selectedVersionId: versions[0].id });
      }
    } catch (error) {
      set({ error: 'Failed to load versions', loading: false });
    }
  },

  createVersion: async (imageId, request) => {
    set({ loading: true, error: null });
    try {
      const newVersion = await apiClient.createVersion(imageId, request);
      set((state) => ({
        versions: [...state.versions, newVersion],
        selectedVersionId: newVersion.id,
        loading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to create version', loading: false });
    }
  },

  updateCrop: async (imageId, versionId, cropData, scale = 1, pan = { x: 0, y: 0 }) => {
    try {
      const updatedVersion = await apiClient.updateCrop(imageId, versionId, {
        cropData,
        scale,
        pan,
      });
      set((state) => ({
        versions: state.versions.map((v) =>
          v.id === versionId ? updatedVersion : v
        ),
      }));
    } catch (error) {
      set({ error: 'Failed to update crop' });
    }
  },

  deleteVersion: async (imageId, versionId) => {
    try {
      await apiClient.deleteVersion(imageId, versionId);
      set((state) => {
        const filtered = state.versions.filter((v) => v.id !== versionId);
        return {
          versions: filtered,
          selectedVersionId:
            state.selectedVersionId === versionId && filtered.length > 0
              ? filtered[0].id
              : state.selectedVersionId === versionId
              ? null
              : state.selectedVersionId,
        };
      });
    } catch (error) {
      set({ error: 'Failed to delete version' });
    }
  },

  analyzeImage: async (imageId, request) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.analyzeImage(imageId, request);

      // Create versions for each analysis result
      for (const result of response.results) {
        await apiClient.createVersion(imageId, {
          name: result.name,
          cropData: result.cropData,
          aspectRatio: undefined, // Let it be calculated
        });
      }

      // Reload versions
      const versions = await apiClient.getVersions(imageId);
      set({ versions, loading: false });

      // Select first version if none selected
      const state = get();
      if (versions.length > 0 && !state.selectedVersionId) {
        set({ selectedVersionId: versions[0].id });
      }
    } catch (error) {
      set({ error: 'Failed to analyze image', loading: false });
    }
  },

  syncWithCropState: async (imageId, versionId) => {
    const cropState = useCropState.getState();
    try {
      await get().updateCrop(
        imageId,
        versionId,
        cropState.crop,
        cropState.scale,
        cropState.pan
      );
    } catch (error) {
      set({ error: 'Failed to sync crop state' });
    }
  },

  getSelectedVersion: () => {
    const state = get();
    return state.versions.find((v) => v.id === state.selectedVersionId);
  },

  getVersionById: (versionId) => {
    const state = get();
    return state.versions.find((v) => v.id === versionId);
  },
}));
