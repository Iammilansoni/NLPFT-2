/**
 * Toast Component
 * Notification toast for success/error messages
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, X } from 'lucide-react';

export interface ToastProps {
  type: 'success' | 'error';
  message: string;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ type, message, onClose }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.3 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
      className="fixed bottom-24 right-6 z-50"
    >
      <div
        className={`flex items-start gap-3 min-w-[300px] max-w-md px-4 py-3 rounded-lg shadow-lg ${
          type === 'success'
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
        }`}
        role="alert"
        aria-live="polite"
      >
        {type === 'success' ? (
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
        ) : (
          <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
        )}

        <div className="flex-1">
          <p
            className={`text-sm font-medium ${
              type === 'success'
                ? 'text-green-900 dark:text-green-100'
                : 'text-red-900 dark:text-red-100'
            }`}
          >
            {message}
          </p>
        </div>

        <button
          onClick={onClose}
          className={`flex-shrink-0 rounded-md p-1 hover:bg-opacity-20 transition-colors ${
            type === 'success'
              ? 'hover:bg-green-200 dark:hover:bg-green-700'
              : 'hover:bg-red-200 dark:hover:bg-red-700'
          }`}
          aria-label="Dismiss notification"
        >
          <X
            className={`w-4 h-4 ${
              type === 'success'
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          />
        </button>
      </div>
    </motion.div>
  );
};

export default Toast;
