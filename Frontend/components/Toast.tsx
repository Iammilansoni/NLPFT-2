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
            ? 'bg-success/10 dark:bg-success/20 border border-success/25 dark:border-success'
            : 'bg-destructive/10 dark:bg-destructive/20 border border-destructive/25 dark:border-destructive'
        }`}
        role="alert"
        aria-live="polite"
      >
        {type === 'success' ? (
          <CheckCircle className="w-5 h-5 text-success dark:text-success flex-shrink-0 mt-0.5" />
        ) : (
          <XCircle className="w-5 h-5 text-destructive dark:text-destructive flex-shrink-0 mt-0.5" />
        )}

        <div className="flex-1">
          <p
            className={`text-sm font-medium ${
              type === 'success'
                ? 'text-success dark:text-success-foreground'
                : 'text-destructive dark:text-destructive-foreground'
            }`}
          >
            {message}
          </p>
        </div>

        <button
          onClick={onClose}
          className={`flex-shrink-0 rounded-md p-1 hover:bg-opacity-20 transition-colors ${
            type === 'success'
              ? 'hover:bg-success/25 dark:hover:bg-success'
              : 'hover:bg-destructive/25 dark:hover:bg-destructive'
          }`}
          aria-label="Dismiss notification"
        >
          <X
            className={`w-4 h-4 ${
              type === 'success'
                ? 'text-success dark:text-success'
                : 'text-destructive dark:text-destructive'
            }`}
          />
        </button>
      </div>
    </motion.div>
  );
};

export default Toast;
