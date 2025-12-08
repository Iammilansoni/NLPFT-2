/**
 * ModelInfoModal Component
 * Detailed model information modal
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { X, Cpu, Zap, Database, Clock } from 'lucide-react';
import { Model } from '@/lib/api';

export interface ModelInfoModalProps {
  model: Model;
  onClose: () => void;
}

export const ModelInfoModal: React.FC<ModelInfoModalProps> = ({
  model,
  onClose,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
        role="dialog"
        aria-labelledby="modal-title"
        aria-describedby="modal-description"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2
                id="modal-title"
                className="text-2xl font-bold text-gray-900 dark:text-white"
              >
                {model.name}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {model.type === 'embedding' ? 'Embedding Model' : 'LLM Model'}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div id="modal-description" className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Description
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {model.shortDescription}
            </p>
          </div>

          {/* Specifications */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Specifications
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {model.dimension && (
                <div className="flex items-start gap-3">
                  <Database className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Vector Dimension
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {model.dimension}D
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3">
                <Clock className="w-5 h-5 text-purple-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Context Length
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {model.contextTokens.toLocaleString()} tokens
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                {model.cpuFriendly ? (
                  <Cpu className="w-5 h-5 text-green-500 mt-0.5" />
                ) : (
                  <Zap className="w-5 h-5 text-yellow-500 mt-0.5" />
                )}
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Performance
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {model.cpuFriendly ? 'CPU Optimized' : 'GPU Recommended'}
                  </p>
                </div>
              </div>

              {model.tokenLimit && (
                <div className="flex items-start gap-3">
                  <Database className="w-5 h-5 text-indigo-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Token Limit
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {model.tokenLimit.toLocaleString()} tokens
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Notes */}
          {model.notes && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Technical Notes
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">
                {model.notes}
              </p>
            </div>
          )}

          {/* CPU Warning */}
          {!model.cpuFriendly && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex gap-3">
                <Zap className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                    GPU Recommended
                  </p>
                  <p className="text-sm text-yellow-700 dark:text-yellow-400 mt-1">
                    This model is not optimized for CPU-only infrastructure and may
                    have slower performance. Consider using a GPU or selecting a
                    CPU-friendly alternative.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Use Cases */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Recommended Use Cases
            </h3>
            <ul className="space-y-2">
              {model.type === 'embedding' && (
                <>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>
                      Semantic search across{' '}
                      {model.dimension && model.dimension < 512 ? '10k-100k' : '100k+'}{' '}
                      documents
                    </span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>
                      Intent detection and query classification
                    </span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>
                      {model.cpuFriendly
                        ? 'Production deployments on standard CPU instances'
                        : 'High-accuracy applications with GPU acceleration'}
                    </span>
                  </li>
                </>
              )}
              {model.type === 'llm' && (
                <>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>Dataset generation and augmentation</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>Structured CSV data generation</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>
                      Generating{' '}
                      {model.contextTokens > 10000
                        ? 'large-scale datasets (1000+ rows)'
                        : 'standard datasets (100-500 rows)'}
                    </span>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-6">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Close
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ModelInfoModal;
