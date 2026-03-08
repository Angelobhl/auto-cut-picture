'use client';

import { Preset } from '../lib/types';
import { cn } from '../lib/utils';

interface PresetSelectorProps {
  selectedPreset: Preset | null;
  onPresetSelect: (preset: Preset) => void;
}

// Presets defined directly in component
const PRESETS: Preset[] = [
  { id: "square", name: "Square (1:1)", aspectRatio: { width: 1, height: 1 }, category: "social" },
  { id: "landscape-4-3", name: "Landscape (4:3)", aspectRatio: { width: 4, height: 3 }, category: "standard" },
  { id: "widescreen-16-9", name: "Widescreen (16:9)", aspectRatio: { width: 16, height: 9 }, category: "video" },
  { id: "portrait-9-16", name: "Portrait (9:16)", aspectRatio: { width: 9, height: 16 }, category: "social" },
  { id: "instagram-feed", name: "Instagram Feed (4:5)", aspectRatio: { width: 4, height: 5 }, category: "social" },
  { id: "freeform", name: "Freeform", aspectRatio: null, category: "custom" }
];

export function PresetSelector({ selectedPreset, onPresetSelect }: PresetSelectorProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Aspect Ratio Presets
      </label>
      <div className="grid grid-cols-2 gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => onPresetSelect(preset)}
            className={cn(
              'px-3 py-2 text-sm rounded-md border transition-colors',
              selectedPreset?.id === preset.id
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400 text-gray-700'
            )}
          >
            {preset.name}
          </button>
        ))}
      </div>
    </div>
  );
}
