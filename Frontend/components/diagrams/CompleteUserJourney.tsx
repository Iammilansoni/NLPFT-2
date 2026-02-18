'use client';

import { useRef, useMemo } from 'react';
import { motion, useInView, type Variants } from 'framer-motion';
import {
  LogIn,
  FileText,
  Settings,
  Database,
  Cpu,
  Search,
  CheckCircle,
  Zap,
  Bot,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CompleteUserJourney — Theme-aligned Animated Flow Diagram
 *
 * Follows the "Enterprise Calm" design system:
 *  - bg-card / border-2 border-border cards with hover:border-primary/50
 *  - bg-primary/10 icon backgrounds, text-primary accents
 *  - bg-gradient-to-b from-background via-primary/5 to-background section bg
 *  - Thin animated connectors with travelling particle (PipelineAnimation-style)
 *  - Staggered whileInView entrance, single subtle blob (no floating orbs)
 *  - Snake layout: Row 1 L→R, vertical drop connector, Row 2 R→L
 *  - Mobile: compact vertical timeline
 */

interface NodeDef {
  id: string;
  step: number;
  title: string;
  subtitle: string;
  Icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  iconBg: string;
  particleColor: string;
}

const NODES: NodeDef[] = [
  { id: 'auth',      step: 1,  title: 'Sign In',     subtitle: 'Login or Register',        Icon: LogIn,       iconColor: 'text-emerald-500', iconBg: 'bg-emerald-500/10', particleColor: '#10b981' },
  { id: 'templates', step: 2,  title: 'Templates',   subtitle: 'Define API spec once',     Icon: FileText,    iconColor: 'text-blue-500',    iconBg: 'bg-blue-500/10',    particleColor: '#3b82f6' },
  { id: 'configure', step: 3,  title: 'Configure',   subtitle: 'LLM & Embeddings',         Icon: Settings,    iconColor: 'text-orange-500',  iconBg: 'bg-orange-500/10',  particleColor: '#f97316' },
  { id: 'generate',  step: 4,  title: 'AI Generate', subtitle: 'Thousands of test cases',  Icon: Bot,         iconColor: 'text-violet-500',  iconBg: 'bg-violet-500/10',  particleColor: '#8b5cf6' },
  { id: 'embed',     step: 5,  title: 'Embed',       subtitle: 'Vector indexing',          Icon: Cpu,         iconColor: 'text-cyan-500',    iconBg: 'bg-cyan-500/10',    particleColor: '#06b6d4' },
  { id: 'vectordb',  step: 6,  title: 'Vector DB',   subtitle: 'Redis KNN search',         Icon: Database,    iconColor: 'text-rose-500',    iconBg: 'bg-rose-500/10',    particleColor: '#f43f5e' },
  { id: 'rerank',    step: 7,  title: 'Re-Rank',     subtitle: 'FlashRank cross-encoder',  Icon: Zap,         iconColor: 'text-purple-500',  iconBg: 'bg-purple-500/10',  particleColor: '#a855f7' },
  { id: 'query',     step: 8,  title: 'Query',       subtitle: 'Semantic search',          Icon: Search,      iconColor: 'text-pink-500',    iconBg: 'bg-pink-500/10',    particleColor: '#ec4899' },
  { id: 'insights',  step: 9,  title: 'Insights',    subtitle: 'Test insights & logs',     Icon: CheckCircle, iconColor: 'text-lime-500',    iconBg: 'bg-lime-500/10',    particleColor: '#84cc16' },
  { id: 'dashboard', step: 10, title: 'Dashboard',   subtitle: 'Real-time results',        Icon: BarChart3,   iconColor: 'text-primary',     iconBg: 'bg-primary/10',     particleColor: '#3b82f6' },
];

// ─── Connectors ───────────────────────────────────────────────────────────────

function HorizontalConnector({ delay, color, reverse = false }: { delay: number; color: string; reverse?: boolean }) {
  return (
    <div className="relative flex items-center w-6 md:w-10 lg:w-14 flex-shrink-0 mx-0.5" style={{ height: 16 }}>
      <div className="absolute inset-y-0 w-full flex items-center"><div className="w-full h-px bg-border" /></div>
      <motion.div
        className="absolute top-1/2 -translate-y-1/2 h-px"
        style={{ [reverse ? 'right' : 'left']: 0, backgroundColor: color, opacity: 0.7 }}
        initial={{ width: 0 }}
        animate={{ width: '100%' }}
        transition={{ duration: 0.45, delay, ease: 'easeOut' }}
      />
      <motion.div
        className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full z-10"
        style={{ backgroundColor: color, boxShadow: `0 0 6px 2px ${color}70` }}
        animate={reverse
          ? { right: ['-4px', 'calc(100% + 4px)'], opacity: [0, 1, 1, 0] }
          : { left: ['-4px', 'calc(100% + 4px)'], opacity: [0, 1, 1, 0] }}
        transition={{ duration: 1.5, delay: delay + 0.3, repeat: Infinity, repeatDelay: 1.2, ease: 'easeInOut' }}
      />
      <div
        className="absolute top-1/2 -translate-y-1/2 w-0 h-0"
        style={{
          [reverse ? 'left' : 'right']: 0,
          borderTop: '3px solid transparent',
          borderBottom: '3px solid transparent',
          ...(reverse ? { borderRight: `5px solid ${color}90` } : { borderLeft: `5px solid ${color}90` }),
        }}
      />
    </div>
  );
}

function VerticalConnector({ delay, fromColor, toColor }: { delay: number; fromColor: string; toColor: string }) {
  return (
    <div className="relative flex justify-center w-full" style={{ height: 40 }}>
      <div className="absolute left-1/2 -translate-x-1/2 inset-y-0 w-px bg-border" />
      <motion.div
        className="absolute left-1/2 -translate-x-1/2 top-0 w-px origin-top"
        style={{ background: `linear-gradient(180deg, ${fromColor}90, ${toColor}50)` }}
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ duration: 0.45, delay, ease: 'easeOut' }}
      />
      <motion.div
        className="absolute left-1/2 -translate-x-1/2 w-2 h-2 rounded-full z-10"
        style={{ backgroundColor: fromColor, boxShadow: `0 0 6px 2px ${fromColor}70` }}
        animate={{ top: ['-4px', 'calc(100% + 4px)'], opacity: [0, 1, 1, 0] }}
        transition={{ duration: 1.0, delay: delay + 0.25, repeat: Infinity, repeatDelay: 1.5, ease: 'easeInOut' }}
      />
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0"
        style={{ borderLeft: '3px solid transparent', borderRight: '3px solid transparent', borderTop: `5px solid ${toColor}90` }}
      />
    </div>
  );
}

// ─── Node Card ────────────────────────────────────────────────────────────────

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 18, scale: 0.93 },
  visible: (i: number) => ({
    opacity: 1, y: 0, scale: 1,
    transition: { duration: 0.5, delay: i * 0.08, type: 'spring', stiffness: 200, damping: 20 },
  }),
};

function NodeCard({ node, index }: { node: NodeDef; index: number }) {
  const { Icon } = node;
  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover={{ scale: 1.05, y: -3 }}
      className="group relative flex flex-col items-center"
    >
      <motion.div
        className="absolute -top-2 -right-1.5 z-20 w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-bold shadow"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 320, delay: index * 0.08 + 0.2 }}
      >
        {node.step}
      </motion.div>

      <div
        className={cn(
          'relative flex flex-col items-center justify-center gap-2.5 p-3 md:p-4',
          'w-[104px] h-[112px] sm:w-[110px] sm:h-[118px] md:w-[124px] md:h-[132px]',
          'rounded-xl border-2 border-border bg-card',
          'hover:border-primary/50 hover:shadow-md',
          'transition-all duration-300 overflow-hidden cursor-default',
        )}
      >
        {/* Hover gradient overlay — mirrors FeatureHighlights */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-primary/10 via-transparent to-accent/10 pointer-events-none" />

        <div className={cn('w-10 h-10 md:w-11 md:h-11 rounded-lg flex items-center justify-center', node.iconBg)}>
          <Icon className={cn('w-5 h-5 md:w-6 md:h-6', node.iconColor)} />
        </div>

        <div className="relative z-10 text-center">
          <p className="text-[11px] md:text-xs font-semibold text-foreground leading-tight">{node.title}</p>
          <p className="text-[9px] md:text-[10px] text-muted-foreground leading-tight mt-0.5">{node.subtitle}</p>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Legend ───────────────────────────────────────────────────────────────────

const LEGEND_GROUPS = [
  { label: 'Auth & Setup',     color: '#10b981' },
  { label: 'AI Generation',    color: '#8b5cf6' },
  { label: 'Vector Pipeline',  color: '#06b6d4' },
  { label: 'Search & Ranking', color: '#ec4899' },
  { label: 'Insights',         color: '#3b82f6' },
];

function Legend() {
  return (
    <motion.div
      className="flex flex-wrap justify-center gap-x-6 gap-y-2 mt-10 pt-6 border-t border-border"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, delay: 1.0 }}
    >
      {LEGEND_GROUPS.map((g) => (
        <span key={g.label} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: g.color }} />
          {g.label}
        </span>
      ))}
    </motion.div>
  );
}

// ─── Mobile Timeline ──────────────────────────────────────────────────────────

function MobileTimelineNode({ node, index, isLast }: { node: NodeDef; index: number; isLast: boolean }) {
  const { Icon } = node;
  return (
    <motion.div
      className="flex gap-3"
      initial={{ opacity: 0, x: -14 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.07 }}
    >
      <div className="flex flex-col items-center flex-shrink-0">
        <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center border border-border', node.iconBg)}>
          <Icon className={cn('w-4 h-4', node.iconColor)} />
        </div>
        {!isLast && (
          <div className="relative w-px flex-1 min-h-[24px] bg-border my-1">
            <motion.div
              className="absolute left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: node.particleColor }}
              animate={{ top: ['0%', '100%'], opacity: [0, 1, 1, 0] }}
              transition={{ duration: 0.9, delay: index * 0.07 + 0.35, repeat: Infinity, repeatDelay: 1.8, ease: 'linear' }}
            />
          </div>
        )}
      </div>

      <div className="flex-1 pb-4 pt-0.5">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[9px] font-bold flex-shrink-0">
            {node.step}
          </span>
          <p className="text-sm font-semibold text-foreground">{node.title}</p>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 ml-5">{node.subtitle}</p>
      </div>
    </motion.div>
  );
}

// ─── Main Export ──────────────────────────────────────────────────────────────

export function CompleteUserJourney() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-60px' });
  const row2Reversed = useMemo(() => [...NODES.slice(5, 10)].reverse(), []);

  return (
    <section
      ref={ref}
      className="relative py-20 md:py-32 border-t"
      aria-label="Complete User Journey Diagram"
    >
      {/* Section background — identical to FeatureHighlights */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />
        <motion.div
          aria-hidden
          animate={{ scale: [1, 1.15, 1], opacity: [0.08, 0.18, 0.08] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-accent/20 rounded-full blur-3xl"
        />
      </div>

      <div className="container mx-auto px-6 md:px-12 max-w-[1280px]">
        {isInView && (
          <>
            {/* ══ Desktop snake (≥ md) ══ */}
            <div className="hidden md:block">
              {/* Row 1 — steps 1–5, L→R */}
              <div className="flex items-center justify-center">
                {NODES.slice(0, 5).map((node, i) => (
                  <div key={node.id} className="flex items-center">
                    <NodeCard node={node} index={i} />
                    {i < 4 && <HorizontalConnector delay={i * 0.08 + 0.15} color={node.particleColor} />}
                  </div>
                ))}
              </div>

              {/* Vertical turn — right-aligned to last card in row 1 */}
              <div className="flex" style={{ justifyContent: 'flex-end', paddingRight: 'calc(50% - 362px)' }}>
                <div style={{ width: 124 }}>
                  <VerticalConnector delay={0.55} fromColor={NODES[4].particleColor} toColor={NODES[5].particleColor} />
                </div>
              </div>

              {/* Row 2 — steps 10→6, flow R→L */}
              <div className="flex items-center justify-center">
                {row2Reversed.map((node, i) => (
                  <div key={node.id} className="flex items-center">
                    <NodeCard node={node} index={node.step - 1} />
                    {i < 4 && (
                      <HorizontalConnector
                        delay={(node.step - 1) * 0.08 + 0.15}
                        color={row2Reversed[i + 1]?.particleColor ?? node.particleColor}
                        reverse
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* ══ Tablet two-row (sm) ══ */}
            <div className="hidden sm:flex md:hidden flex-col items-center">
              <div className="flex items-center justify-center flex-wrap">
                {NODES.slice(0, 5).map((node, i) => (
                  <div key={node.id} className="flex items-center">
                    <NodeCard node={node} index={i} />
                    {i < 4 && <HorizontalConnector delay={i * 0.08 + 0.15} color={node.particleColor} />}
                  </div>
                ))}
              </div>
              <div className="self-end pr-2" style={{ width: 110 }}>
                <VerticalConnector delay={0.55} fromColor={NODES[4].particleColor} toColor={NODES[5].particleColor} />
              </div>
              <div className="flex items-center justify-center flex-wrap">
                {row2Reversed.map((node, i) => (
                  <div key={node.id} className="flex items-center">
                    <NodeCard node={node} index={node.step - 1} />
                    {i < 4 && (
                      <HorizontalConnector
                        delay={(node.step - 1) * 0.08 + 0.15}
                        color={row2Reversed[i + 1]?.particleColor ?? node.particleColor}
                        reverse
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* ══ Mobile vertical timeline ══ */}
            <div className="sm:hidden max-w-xs mx-auto">
              {NODES.map((node, i) => (
                <MobileTimelineNode
                  key={node.id}
                  node={node}
                  index={i}
                  isLast={i === NODES.length - 1}
                />
              ))}
            </div>

            <Legend />
          </>
        )}
      </div>
    </section>
  );
}

export default CompleteUserJourney;
