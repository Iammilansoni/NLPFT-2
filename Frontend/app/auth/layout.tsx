/**
 * Auth Layout
 * Enterprise-grade auth layout with subtle background motif
 * Matches landing page visual style
 */

import React from 'react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen relative bg-background">
      {/* Magenta Orb Grid Background - Light Mode */}
      <div
        className="fixed inset-0 dark:hidden pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(100,116,139,0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(100,116,139,0.08) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(236,72,153,0.1) 0%, rgba(168,85,247,0.04) 40%, transparent 70%)
          `,
          backgroundSize: "40px 40px, 40px 40px, 100% 100%",
          backgroundColor: "white",
        }}
        aria-hidden="true"
      />

      {/* Magenta Orb Grid Background - Dark Mode */}
      <div
        className="fixed inset-0 hidden dark:block pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(148,163,184,0.06) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(148,163,184,0.06) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(236,72,153,0.08) 0%, rgba(168,85,247,0.03) 40%, transparent 70%)
          `,
          backgroundSize: "40px 40px, 40px 40px, 100% 100%",
          backgroundColor: "hsl(222, 25%, 6%)",
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
