/**
 * ModelCard Component
 * Displays a single model with metadata and selection state
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Zap, Info, Check } from 'lucide-react';
import { Model } from '@/lib/api';

export interface ModelCardProps {
  model: Model;
  selected: boolean;
  onSelect: (modelId: string) => void;
  onShowInfo: (model: Model) => void;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  model,
  selected,
  onSelect,
  onShowInfo,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <button
        onClick={() => onSelect(model.id)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onSelect(model.id);
          }
        }}
        className={`
          relative w-full p-4 rounded-lg border-2 transition-all
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          text-left
          ${
            selected
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          }
        `}
        aria-pressed={selected}
        aria-label={`Select ${model.name}`}
        role="radio"
      >
        {/* Selection Indicator */}
        {selected && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute top-3 right-3 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center"
          >
            <Check className="w-4 h-4 text-white" />
          </motion.div>
        )}

        {/* Model Name */}
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white pr-8">
            {model.name}
          </h3>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          {model.cpuFriendly && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
              <Cpu className="w-3 h-3 mr-1" />
              CPU Friendly
            </span>
          )}

          {!model.cpuFriendly && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
              <Zap className="w-3 h-3 mr-1" />
              GPU Recommended
            </span>
          )}

          {model.dimension && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
              {model.dimension}D
            </span>
          )}

          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">
            {model.contextTokens.toLocaleString()} tokens
          </span>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {model.shortDescription}
        </p>

        {/* More Info Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onShowInfo(model);
          }}
          className="inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 focus:outline-none focus:underline"
          aria-label={`More information about ${model.name}`}
        >
          <Info className="w-4 h-4 mr-1" />
          More info
        </button>
      </button>
    </motion.div>
  );
};

export default ModelCard;
