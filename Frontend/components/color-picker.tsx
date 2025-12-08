'use client';

/**
 * Color Picker Component - Select primary theme color
 */

import { Palette } from 'lucide-react';
import { useTheme } from '@/components/theme-provider';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

const colors = [
  { name: 'Blue', value: 'blue', hex: '#3b82f6' },
  { name: 'Purple', value: 'purple', hex: '#a855f7' },
  { name: 'Green', value: 'green', hex: '#10b981' },
  { name: 'Orange', value: 'orange', hex: '#f97316' },
  { name: 'Pink', value: 'pink', hex: '#ec4899' },
  { name: 'Red', value: 'red', hex: '#ef4444' },
] as const;

export function ColorPicker() {
  const { themeColor, setThemeColor } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-10 h-10 rounded-lg border border-border bg-card hover:bg-accent transition-colors flex items-center justify-center"
        aria-label="Choose theme color"
      >
        <Palette className="w-5 h-5" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 p-3 bg-card border border-border rounded-lg shadow-lg z-50 min-w-[200px]"
            >
              <div className="text-sm font-medium mb-3">Theme Color</div>
              <div className="grid grid-cols-3 gap-2">
                {colors.map((color) => (
                  <button
                    key={color.value}
                    onClick={() => {
                      setThemeColor(color.value);
                      setIsOpen(false);
                    }}
                    className="group relative flex flex-col items-center gap-1.5 p-2 rounded hover:bg-accent transition-colors"
                    aria-label={`Set theme color to ${color.name}`}
                  >
                    <div
                      className="w-8 h-8 rounded-full border-2 transition-all"
                      style={{
                        backgroundColor: color.hex,
                        borderColor: themeColor === color.value ? color.hex : 'transparent',
                        boxShadow: themeColor === color.value ? `0 0 0 3px hsl(var(--background)), 0 0 0 5px ${color.hex}` : 'none',
                      }}
                    />
                    <span className="text-xs">{color.name}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
