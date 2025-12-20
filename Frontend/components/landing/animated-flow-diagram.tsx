'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  LogIn,
  FileText,
  Bot,
  File,
  Cpu,
  Database,
  Shuffle,
  PlayCircle,
  Camera,
  BarChart3,
} from 'lucide-react';

/**
 * Landing Animated Flow Diagram
 *
 * Flow (10 nodes):
 * [Login & Onboarding]
 * [Define Your API Once]
 * [AI Generates Thousands of Test Cases]
 * [Smart CSV + Deep Metadata]
 * [Embeddings (Your Model Choice)]
 * [High-Speed Redis Vector Search]
 * [AI Query Understanding + Re-Ranking]
 * [Automated API Calls + Browser Flow Testing]
 * [Test Insights • Screenshots • Logs]
 * [Clean Dashboard With Real-Time Results]
 */

const nodes = [
  { id: 'n1', label: 'Login\n& Onboarding', icon: LogIn, color: 'from-sky-500 to-indigo-500' },
  { id: 'n2', label: 'Define Your\nAPI Once', icon: FileText, color: 'from-blue-500 to-sky-500' },
  { id: 'n3', label: 'AI Generates\nThousands of Tests', icon: Bot, color: 'from-fuchsia-500 to-rose-500' },
  { id: 'n4', label: 'Smart CSV\n+ Deep Metadata', icon: File, color: 'from-emerald-500 to-teal-500' },
  { id: 'n5', label: 'Embeddings\n(Your Model Choice)', icon: Cpu, color: 'from-lime-500 to-emerald-500' },
  { id: 'n6', label: 'High-Speed\nRedis Vector Search', icon: Database, color: 'from-orange-400 to-red-500' },
  { id: 'n7', label: 'AI Query\nUnderstanding\n+ Re-Ranking', icon: Shuffle, color: 'from-blue-500 to-sky-500' },
  { id: 'n8', label: 'Automated API Calls\n+ Browser Testing', icon: PlayCircle, color: 'from-cyan-500 to-blue-500' },
  { id: 'n9', label: 'Test Insights •\nScreenshots • Logs', icon: Camera, color: 'from-rose-500 to-pink-500' },
  { id: 'n10', label: 'Clean Dashboard\nWith Real-Time Results', icon: BarChart3, color: 'from-emerald-500 to-green-500' },
];

export function AnimatedFlowDiagram() {
  // Calculate positions for a 5x2 grid layout
  // For simplicity use percentage-based columns and two rows
  const colCount = 5;
  const rowCount = 2;

  const getPosition = (index: number) => {
    const col = index % colCount;
    const row = Math.floor(index / colCount);
    const x = 5 + col * (90 / (colCount - 1)); // 5% padding left..right
    const y = row === 0 ? 24 : 76; // top row ~24%, bottom row ~76%
    return { x: `${x}%`, y: `${y}%` };
  };

  return (
    <section
      aria-label="Product flow diagram"
      className="relative w-full max-w-6xl mx-auto p-6 lg:p-12"
      role="region"
    >
      {/* subtle grid background */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(to_right,#00000008_1px,transparent_1px),linear-gradient(to_bottom,#00000008_1px,transparent_1px)] bg-[size:24px_24px] rounded-2xl" />

      {/* SVG connectors */}
      <svg
        className="absolute inset-0 w-full h-full"
        aria-hidden="true"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="g1" x1="0" x2="1">
            <stop offset="0%" stopColor="hsl(var(--primary) / 0.15)" />
            <stop offset="50%" stopColor="hsl(var(--primary) / 0.9)" />
            <stop offset="100%" stopColor="hsl(var(--primary) / 0.15)" />
          </linearGradient>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Draw lines between consecutive nodes */}
        {nodes.map((_, i) => {
          if (i === nodes.length - 1) return null;
          const from = getPosition(i);
          const to = getPosition(i + 1);
          // create gentle curved path
          const midX = `calc(${from.x} + (${to.x} - ${from.x}) / 2)`;
          // using simple quadratic curve via path d
          return (
            <g key={`edge-${i}`}>
              <motion.path
                d={`M ${from.x} ${from.y} Q ${midX} ${(parseFloat(from.y) + parseFloat(to.y)) / 2}% ${to.x} ${to.y}`}
                stroke="url(#g1)"
                strokeWidth={2}
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                // initial draw animation
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.9, delay: 0.15 * i, ease: 'easeInOut' }}
              />

              {/* flowing particle along the path */}
              <motion.circle
                r="4"
                fill="hsl(var(--primary))"
                initial={{ opacity: 0 }}
                animate={{
                  translateX: [0, 1],
                  opacity: [0, 1, 1, 0],
                }}
                transition={{
                  duration: 2.4,
                  delay: 0.2 + i * 0.12,
                  repeat: Infinity,
                  ease: 'linear',
                }}
                // move along path using CSS motion path via SVG <animateMotion> is clip; we emulate
                // For simplicity we place the particle at 'from' coords and animate transform via framer
                style={{
                  transformOrigin: 'center',
                  position: 'absolute',
                }}
                // place initial circle via cx/cy attributes
                cx={from.x}
                cy={from.y}
              />
            </g>
          );
        })}
      </svg>

      {/* Desktop grid of nodes (5 cols x 2 rows) */}
      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-5 gap-6 items-stretch">
        {nodes.map((node, idx) => {
          const pos = getPosition(idx);
          const Icon = node.icon;
          return (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.6, delay: idx * 0.08, type: 'spring', stiffness: 160, damping: 18 }}
              className={`relative flex items-center justify-center min-h-[110px] sm:min-h-[120px]`}
              role="img"
              aria-label={node.label.replace('\n', ' ')}
              tabIndex={0}
            >
              <div className="w-full max-w-xs mx-auto">
                <div
                  className={`rounded-2xl p-4 md:p-5 bg-card border border-border shadow-sm hover:shadow-lg transition-shadow focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary`}
                >
                  <div className="flex items-center justify-center mb-3">
                    <div className={`rounded-lg p-2 md:p-3 bg-gradient-to-br ${node.color} inline-flex`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <p className="text-center text-xs md:text-sm font-semibold leading-snug whitespace-pre-line">
                    {node.label}
                  </p>
                </div>

                {/* small subtle pulse */}
                <motion.span
                  className="absolute right-6 -top-2 w-2 h-2 rounded-full bg-primary"
                  animate={{
                    scale: [1, 1.6, 1],
                    opacity: [1, 0.5, 1],
                  }}
                  transition={{ duration: 2.2, delay: idx * 0.15, repeat: Infinity, ease: 'easeInOut' }}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Mobile linear timeline fallback (visible only on small screens) */}
      <div className="sm:hidden mt-6 space-y-4">
        {nodes.map((n, i) => {
          const Icon = n.icon;
          return (
            <div key={`mobile-${n.id}`} className="flex items-start space-x-3">
              <div className="mt-1">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center shadow">
                  <Icon className="w-4 h-4 text-gray-700" />
                </div>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{n.label.split('\n')[0]}</div>
                <div className="text-xs text-muted-foreground">{n.label.split('\n').slice(1).join(' ')}</div>
                {/* simple animated connector */}
                {i < nodes.length - 1 && (
                  <motion.div
                    className="h-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.08 }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default AnimatedFlowDiagram;
