import { create } from 'zustand';
import { Image } from '../lib/types';
import { apiClient } from '../lib/api';

interface ImageListState {
  images: Image[];
  selectedImageId: string;
  loading: boolean;
  error: string | null;
  setImages: (images: Image[]) => void;
  setSelectedImageId: (id: string) => void;
  loadImages: () => Promise<void>;
  addImages: (newImages: Image[]) => void;
  removeImage: (id: string) => Promise<void>;
  deleteAllImages: () => Promise<void>;
  updateImage: (updatedImage: Image) => void;
  getSelectedImage: () => Image | undefined;
}

export const useImageList = create<ImageListState>((set, get) => ({
  images: [],
  selectedImageId: '',
  loading: false,
  error: null,

  setImages: (images) => set({ images }),
  setSelectedImageId: (id) => set({ selectedImageId: id }),

  loadImages: async () => {
    set({ loading: true, error: null });
    try {
      const images = await apiClient.getImages();
      // Deduplicate images by ID
      const uniqueImages = Array.from(
        new Map(images.map(img => [img.id, img])).values()
      );
      set({ images: uniqueImages, loading: false });
    } catch (error) {
      set({ error: 'Failed to load images', loading: false });
    }
  },

  addImages: (newImages) => {
    set((state) => ({
      images: [...state.images, ...newImages],
      selectedImageId: newImages.length > 0 ? newImages[0].id : state.selectedImageId,
    }));
  },

  removeImage: async (id) => {
    try {
      await apiClient.deleteImage(id);
      set((state) => {
        const filtered = state.images.filter((img) => img.id !== id);
        return {
          images: filtered,
          selectedImageId:
            state.selectedImageId === id && filtered.length > 0
              ? filtered[0].id
              : state.selectedImageId === id
              ? ''
              : state.selectedImageId,
        };
      });
    } catch (error) {
      set({ error: 'Failed to delete image' });
    }
  },

  deleteAllImages: async () => {
    try {
      await apiClient.deleteAllImages();
      set({ images: [], selectedImageId: '' });
    } catch (error) {
      set({ error: 'Failed to delete all images' });
    }
  },

  updateImage: (updatedImage) => {
    set((state) => ({
      images: state.images.map((img) =>
        img.id === updatedImage.id ? updatedImage : img
      ),
    }));
  },

  getSelectedImage: () => {
    const state = get();
    return state.images.find((img) => img.id === state.selectedImageId);
  },
}));
