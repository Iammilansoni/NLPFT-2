"use client";

import { useEffect, useRef, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { api } from "@/lib/api";
import { HealthStatus } from "@/lib/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/design/MetricCard";
import { EmptyState } from "@/components/design/EmptyState";
import { LoadingOverlay } from "@/components/design/LoadingOverlay";
import {
  Activity,
  Database,
  Cpu,
  MemoryStick,
  Clock,
  Server,
  Zap,
  FileText,
  TrendingUp,
  Shield,
  Gauge,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { PlaceholderMetrics } from "@/components/design/PlaceholderMetrics";





type HighlightTone = "blue" | "emerald" | "violet" | "amber";

interface HighlightData {
  title: string;
  value: string | number;
  description: string;
  icon: LucideIcon;
  tone: HighlightTone;
}

export default function DashboardPage() {
  const { theme, resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const {
    data: health,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<HealthStatus>({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 30000,
    staleTime: 15000,
    retry: 1,
  });

  const previousStatusRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    const prev = previousStatusRef.current;
    const current = health?.status;
    if (prev && current && prev !== current) {
      const el = document.getElementById("dashboard-announcer");
      if (el) {
        el.textContent = `System status changed: ${current}`;
      }
    }
    previousStatusRef.current = current;
  }, [health?.status]);

  const loadStateSection = () => {
    if (isLoading) {
      return (
        <div className="mt-4">
          <LoadingOverlay
            isLoading
            variant="inline"
            size="md"
            title="Loading Operational Metrics"
            description="Fetching live health and performance data..."
            icon={Server}
            spinner="pulse"
            className="min-h-[36vh]"
          />
        </div>
      );
    }
    if (error) {
      return (
        <div className="mt-6 animate-fade-in">
          <EmptyState
            icon={Server}
            title="Service Unavailable"
            description="Unable to connect to the enterprise NLP service. Start the backend and retry."
            action={{ label: "Retry", onClick: () => refetch() }}
            size="lg"
          />
        </div>
      );
    }
    return null;
  };

  const getStatusBadge = (status: string) => {
    const getStatusIcon = () => {
      switch (status) {
        case "healthy":
          return <Shield className="h-3 w-3" />;
        case "degraded":
          return <Activity className="h-3 w-3" />;
        case "unhealthy":
          return <Server className="h-3 w-3" />;
        default:
          return <Clock className="h-3 w-3" />;
      }
    };

    const getStatusStyles = () => {
      const baseStyles = "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-300 border";

      switch (status) {
        case "healthy":
          return `${baseStyles} ${isDark
            ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-300 shadow-lg shadow-emerald-500/10'
            : 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-sm'
            }`;
        case "degraded":
          return `${baseStyles} ${isDark
            ? 'bg-amber-500/20 border-amber-500/30 text-amber-300 shadow-lg shadow-amber-500/10'
            : 'bg-amber-50 border-amber-200 text-amber-700 shadow-sm'
            }`;
        case "unhealthy":
          return `${baseStyles} ${isDark
            ? 'bg-red-500/20 border-red-500/30 text-red-300 shadow-lg shadow-red-500/10'
            : 'bg-red-50 border-red-200 text-red-700 shadow-sm'
            }`;
        default:
          return `${baseStyles} ${isDark
            ? 'bg-slate-500/20 border-slate-500/30 text-slate-300 shadow-lg shadow-slate-500/10'
            : 'bg-slate-50 border-slate-200 text-slate-700 shadow-sm'
            }`;
      }
    };

    return (
      <span className={getStatusStyles()}>
        {getStatusIcon()}
        <span className="capitalize">{status}</span>
      </span>
    );
  };

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const totalParses = health?.checks?.rule_engine?.total_parses ?? 0;
  const successRate =
    totalParses > 0 && health?.checks?.rule_engine?.successful_parses != null
      ? Math.round((health.checks.rule_engine.successful_parses / totalParses) * 100)
      : null;

  const highlightTiles: HighlightData[] = useMemo(
    () => [
      {
        title: "Platform Uptime",
        value: health?.checks?.application?.uptime_seconds
          ? formatUptime(health.checks.application.uptime_seconds)
          : "—",
        description: health?.checks?.application?.version
          ? `Application v${health.checks.application.version}`
          : "Runtime status unavailable",
        icon: Clock,
        tone: "blue",
      },
      {
        title: "Database Health",
        value: (health?.checks?.database?.status || "unknown").toUpperCase(),
        description: `${health?.checks?.database?.response_time_ms?.toFixed(1) ?? "0"} ms response time`,
        icon: Database,
        tone: "emerald",
      },
      {
        title: "CPU Load",
        value: `${health?.checks?.system?.cpu?.usage_percent?.toFixed(1) ?? "0"}%`,
        description: `Process ID ${health?.checks?.system?.process_id ?? "—"}`,
        icon: Cpu,
        tone: "violet",
      },
      {
        title: "Rule Success Rate",
        value: successRate !== null ? `${successRate}%` : "—",
        description: `${health?.checks?.rule_engine?.successful_parses ?? 0} successful of ${totalParses} parses`,
        icon: Zap,
        tone: "amber",
      },
    ],
    [health, successRate, totalParses]
  );

  return (
    <main
      className="relative min-h-screen overflow-hidden theme-transition"
      style={{
        background: isDark
          ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #1e293b 75%, #0f172a 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%, #f8fafc 100%)'
      }}
      aria-labelledby="dashboard-title"
    >
      <div id="dashboard-announcer" aria-live="polite" className="sr-only" />

      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div
          className={`absolute inset-0 transition-opacity duration-500 ${isDark ? 'opacity-8' : 'opacity-3'
            }`}
          style={{
            backgroundImage: isDark
              ? `linear-gradient(to right, rgba(59,130,246,0.08) 1px, transparent 1px),linear-gradient(to bottom, rgba(59,130,246,0.08) 1px, transparent 1px)`
              : `linear-gradient(to right, rgba(99,102,241,0.04) 1px, transparent 1px),linear-gradient(to bottom, rgba(99,102,241,0.04) 1px, transparent 1px)`,
            backgroundSize: "4rem 4rem",
          }}
        />

        <div className={`absolute -top-40 -left-40 h-96 w-96 rounded-full blur-3xl transition-all duration-700 ${isDark
          ? 'bg-gradient-to-br from-blue-500/20 to-indigo-500/20 animate-pulse'
          : 'bg-gradient-to-br from-blue-500/8 to-indigo-500/8'
          }`} />
        <div className={`absolute top-1/3 -right-20 h-[32rem] w-[32rem] rounded-full blur-3xl transition-all duration-700 ${isDark
          ? 'bg-gradient-to-bl from-violet-500/25 to-purple-500/25 animate-pulse'
          : 'bg-gradient-to-bl from-violet-500/6 to-purple-500/6'
          }`} style={{ animationDelay: '1s' }} />
        <div className={`absolute bottom-0 left-1/4 h-80 w-80 rounded-full blur-3xl transition-all duration-700 ${isDark
          ? 'bg-gradient-to-tr from-cyan-500/20 to-blue-500/20 animate-pulse'
          : 'bg-gradient-to-tr from-cyan-500/6 to-blue-500/6'
          }`} style={{ animationDelay: '2s' }} />

        {isDark && (
          <>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-gradient-to-r from-blue-500/5 to-purple-500/5 blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }} />
            <div className="absolute top-20 right-1/4 h-64 w-64 rounded-full bg-gradient-to-br from-emerald-500/15 to-teal-500/15 blur-2xl animate-pulse" style={{ animationDelay: '1.5s' }} />
          </>
        )}
      </div>

      <div className="relative mx-auto max-w-7xl space-y-8 px-4 py-12 sm:px-6 lg:px-8">
        <section className="space-y-6" aria-labelledby="dashboard-title">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-2xl transition-all duration-300 ${isDark
                  ? 'bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                  : 'bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200/50 shadow-md'
                  }`}>
                  <Gauge className={`h-8 w-8 ${isDark ? 'text-blue-300' : 'text-blue-600'}`} />
                </div>
                <div>
                  <h1
                    id="dashboard-title"
                    className={`text-4xl font-bold tracking-tight transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                      }`}
                  >
                    Operational Metrics
                  </h1>
                  <p className={`text-lg transition-colors duration-300 ${isDark ? 'text-slate-300' : 'text-slate-600'
                    }`}>
                    Live health signals and performance indicators from core subsystems
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <div className={`group relative overflow-hidden rounded-2xl px-5 py-3 transition-all duration-300 hover:scale-105 ${isDark
                ? 'bg-gradient-to-r from-slate-900/60 to-slate-800/60 border border-slate-700/50 backdrop-blur-xl shadow-lg shadow-black/20'
                : 'bg-gradient-to-r from-white/80 to-slate-50/80 border border-slate-200/60 backdrop-blur-sm shadow-md'
                }`}>
                <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${isDark
                  ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10'
                  : 'bg-gradient-to-r from-blue-50/50 to-indigo-50/50'
                  }`} />

                <div className="relative flex items-center gap-3">
                  <div className={`flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-700'
                    }`}>
                    <Gauge className="h-4 w-4" />
                    <span className="text-sm font-medium">System Status</span>
                  </div>
                  <div className="h-4 w-px bg-gradient-to-b from-transparent via-slate-300 dark:via-slate-600 to-transparent" />
                  {getStatusBadge(health?.status || "unknown")}
                </div>
              </div>

              <button
                type="button"
                onClick={() => refetch()}
                disabled={isFetching}
                className={`group relative overflow-hidden rounded-2xl px-5 py-3 text-sm font-medium transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 ${isDark
                  ? 'bg-gradient-to-r from-indigo-600/80 to-blue-600/80 border border-indigo-500/50 text-white hover:from-indigo-500/90 hover:to-blue-500/90 focus:ring-indigo-400 focus:ring-offset-slate-950 shadow-lg shadow-indigo-500/20 backdrop-blur-xl'
                  : 'bg-gradient-to-r from-indigo-500 to-blue-500 border border-indigo-400/30 text-white hover:from-indigo-600 hover:to-blue-600 focus:ring-indigo-500 focus:ring-offset-white shadow-md hover:shadow-lg'
                  }`}
                aria-label="Refresh metrics"
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 transform -skew-x-12 group-hover:animate-pulse" />

                <div className="relative flex items-center gap-2">
                  {isFetching ? (
                    <>
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden>
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" />
                        <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                      </svg>
                      <span>Refreshing...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="h-4 w-4 transition-transform duration-300 group-hover:rotate-180" aria-hidden />
                      <span>Refresh Data</span>
                    </>
                  )}
                </div>
              </button>

              <div className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-300 ${isDark
                ? 'bg-slate-800/40 border border-slate-700/50 text-slate-300'
                : 'bg-slate-100/60 border border-slate-200/50 text-slate-600'
                }`}>
                <div className={`h-2 w-2 rounded-full transition-all duration-300 ${health?.status === 'healthy'
                  ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse'
                  : health?.status === 'degraded'
                    ? 'bg-amber-500 shadow-lg shadow-amber-500/50'
                    : 'bg-red-500 shadow-lg shadow-red-500/50'
                  }`} />
                <span className="text-xs font-medium">
                  {health?.status === 'healthy' ? 'Connected' : 'Issues Detected'}
                </span>
              </div>
            </div>
          </div>

          {health?.timestamp && (
            <div className={`flex items-center gap-3 text-sm transition-all duration-300 ${isDark ? 'text-slate-400' : 'text-slate-500'
              }`}>
              <div className="flex items-center gap-2">
                <div className={`p-1.5 rounded-lg transition-all duration-300 ${isDark
                  ? 'bg-slate-800/50 border border-slate-700/50'
                  : 'bg-slate-100/80 border border-slate-200/50'
                  }`}>
                  <Clock className="h-3 w-3" />
                </div>
                <span className="font-medium">Last updated:</span>
              </div>
              <time className={`font-mono px-3 py-1.5 rounded-lg transition-all duration-300 border ${isDark
                ? 'bg-slate-800/60 border-slate-700/50 text-slate-200 shadow-lg shadow-black/10'
                : 'bg-white/80 border-slate-200/60 text-slate-700 shadow-sm'
                }`} dateTime={health.timestamp}>
                {api.formatDateTime(health.timestamp)}
              </time>

              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs ${isDark
                ? 'bg-blue-500/20 border border-blue-500/30 text-blue-300'
                : 'bg-blue-50 border border-blue-200 text-blue-700'
                }`}>
                <div className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
                <span>Auto-refresh: 30s</span>
              </div>
            </div>
          )}
        </section>

        {loadStateSection()}

        {isLoading && <PlaceholderMetrics mode="loading" />}
        {error && <PlaceholderMetrics mode="offline" />}

        {!isLoading && !error && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4" role="list" aria-label="Key health highlights">
            {highlightTiles.map((tile, index) => (
              <article
                role="listitem"
                key={String(tile.title)}
                aria-labelledby={`tile-${tile.title}`}
                className="animate-fade-in"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <HighlightTile {...(tile as HighlightData)} isDark={isDark} />
              </article>
            ))}
          </div>
        )}

        {!isLoading && !error && (
          <Card className={`group overflow-hidden transition-all duration-500 hover:scale-[1.02] ${isDark
            ? 'border-slate-700/30 bg-gradient-to-br from-slate-900/60 to-slate-800/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
            : 'border-slate-200/40 bg-gradient-to-br from-white/90 to-slate-50/80 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
            }`} role="region" aria-labelledby="system-health-title">

            <CardHeader className={`relative border-b transition-all duration-300 ${isDark
              ? 'border-slate-700/40 bg-gradient-to-r from-slate-800/50 to-slate-900/50'
              : 'border-slate-200/40 bg-gradient-to-r from-slate-50/60 to-blue-50/30'
              }`}>
              <div className={`absolute inset-0 opacity-30 ${isDark ? 'opacity-20' : 'opacity-10'
                }`} style={{
                  backgroundImage: `radial-gradient(circle at 1px 1px, ${isDark ? 'rgba(59,130,246,0.3)' : 'rgba(99,102,241,0.2)'} 1px, transparent 0)`,
                  backgroundSize: '20px 20px'
                }} />

              <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle className={`flex items-center gap-4 text-2xl font-bold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                  }`} id="system-health-title">
                  <div className={`relative rounded-2xl p-3 transition-all duration-300 group-hover:scale-110 ${isDark
                    ? 'bg-gradient-to-br from-blue-500/40 to-indigo-600/40 shadow-lg shadow-blue-500/30 border border-blue-400/30'
                    : 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30'
                    }`}>
                    <Shield className="h-7 w-7 text-white" aria-hidden />
                    {isDark && (
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-400/20 to-indigo-500/20 animate-pulse" />
                    )}
                  </div>
                  <div>
                    <span>System Health Overview</span>
                    <div className={`text-sm font-normal mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'
                      }`}>
                      Live monitoring dashboard
                    </div>
                  </div>
                </CardTitle>

                <div className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${isDark
                  ? 'bg-slate-800/60 border border-slate-700/50'
                  : 'bg-white/80 border border-slate-200/60'
                  }`}>
                  <div className={`h-2 w-2 rounded-full ${health?.status === 'healthy'
                    ? 'bg-emerald-500 animate-pulse shadow-lg shadow-emerald-500/50'
                    : 'bg-amber-500 animate-pulse shadow-lg shadow-amber-500/50'
                    }`} />
                  <span className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'
                    }`}>
                    {health?.status === 'healthy' ? 'All Systems Operational' : 'Monitoring Issues'}
                  </span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-8">
              <div className="grid grid-cols-1 gap-8 md:grid-cols-3">

                <div className={`group/card relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-2 hover:scale-105 ${isDark
                  ? 'bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 shadow-xl shadow-blue-500/20 hover:shadow-2xl hover:shadow-blue-500/30'
                  : 'bg-gradient-to-br from-blue-50/80 to-indigo-50/60 border border-blue-200/50 shadow-lg hover:shadow-xl'
                  }`}>
                  <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 ${isDark
                    ? 'bg-gradient-to-br from-blue-500/10 to-indigo-600/10'
                    : 'bg-gradient-to-br from-blue-100/50 to-indigo-100/30'
                    }`} />

                  <div className={`absolute -inset-1 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 blur-xl ${isDark ? 'bg-gradient-to-br from-blue-500/30 to-indigo-600/30' : ''
                    }`} />

                  <div className="relative space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-blue-300' : 'text-blue-700'
                        }`}>Application Version</h3>
                      <div className={`rounded-xl p-2.5 transition-all duration-300 group-hover/card:scale-110 group-hover/card:rotate-12 ${isDark
                        ? 'bg-gradient-to-br from-blue-500/40 to-indigo-600/40 shadow-lg shadow-blue-500/20'
                        : 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md'
                        }`}>
                        <FileText className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <p className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-blue-100' : 'text-blue-900'
                      }`}>
                      {health?.version ?? "Unknown"}
                    </p>
                    <p className={`text-sm transition-colors duration-300 ${isDark ? 'text-blue-400/80' : 'text-blue-600/80'
                      }`}>
                      Current release build
                    </p>
                  </div>
                </div>

                <div className={`group/card relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-2 hover:scale-105 ${isDark
                  ? 'bg-gradient-to-br from-emerald-500/20 to-teal-600/20 border border-emerald-500/30 shadow-xl shadow-emerald-500/20 hover:shadow-2xl hover:shadow-emerald-500/30'
                  : 'bg-gradient-to-br from-emerald-50/80 to-teal-50/60 border border-emerald-200/50 shadow-lg hover:shadow-xl'
                  }`}>
                  <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 ${isDark
                    ? 'bg-gradient-to-br from-emerald-500/10 to-teal-600/10'
                    : 'bg-gradient-to-br from-emerald-100/50 to-teal-100/30'
                    }`} />

                  <div className={`absolute -inset-1 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 blur-xl ${isDark ? 'bg-gradient-to-br from-emerald-500/30 to-teal-600/30' : ''
                    }`} />

                  <div className="relative space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-emerald-300' : 'text-emerald-700'
                        }`}>System Uptime</h3>
                      <div className={`rounded-xl p-2.5 transition-all duration-300 group-hover/card:scale-110 group-hover/card:rotate-12 ${isDark
                        ? 'bg-gradient-to-br from-emerald-500/40 to-teal-600/40 shadow-lg shadow-emerald-500/20'
                        : 'bg-gradient-to-br from-emerald-500 to-teal-600 shadow-md'
                        }`}>
                        <Clock className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <p className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-emerald-100' : 'text-emerald-900'
                      }`}>
                      {health?.checks?.application?.uptime_seconds ? formatUptime(health.checks.application.uptime_seconds) : "Unknown"}
                    </p>
                    <p className={`text-sm transition-colors duration-300 ${isDark ? 'text-emerald-400/80' : 'text-emerald-600/80'
                      }`}>
                      Continuous operation time
                    </p>
                  </div>
                </div>

                <div className={`group/card relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-2 hover:scale-105 ${isDark
                  ? 'bg-gradient-to-br from-violet-500/20 to-purple-600/20 border border-violet-500/30 shadow-xl shadow-violet-500/20 hover:shadow-2xl hover:shadow-violet-500/30'
                  : 'bg-gradient-to-br from-violet-50/80 to-purple-50/60 border border-violet-200/50 shadow-lg hover:shadow-xl'
                  }`}>
                  <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 ${isDark
                    ? 'bg-gradient-to-br from-violet-500/10 to-purple-600/10'
                    : 'bg-gradient-to-br from-violet-100/50 to-purple-100/30'
                    }`} />

                  <div className={`absolute -inset-1 rounded-2xl opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 blur-xl ${isDark ? 'bg-gradient-to-br from-violet-500/30 to-purple-600/30' : ''
                    }`} />

                  <div className="relative space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-violet-300' : 'text-violet-700'
                        }`}>Process ID</h3>
                      <div className={`rounded-xl p-2.5 transition-all duration-300 group-hover/card:scale-110 group-hover/card:rotate-12 ${isDark
                        ? 'bg-gradient-to-br from-violet-500/40 to-purple-600/40 shadow-lg shadow-violet-500/20'
                        : 'bg-gradient-to-br from-violet-500 to-purple-600 shadow-md'
                        }`}>
                        <Server className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <p className={`text-3xl font-bold font-mono transition-colors duration-300 ${isDark ? 'text-violet-100' : 'text-violet-900'
                      }`}>
                      {health?.checks?.system?.process_id?.toString() ?? "Unknown"}
                    </p>
                    <p className={`text-sm transition-colors duration-300 ${isDark ? 'text-violet-400/80' : 'text-violet-600/80'
                      }`}>
                      System process identifier
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !error && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-4" role="region" aria-label="Top-level metrics">

            <div className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-3 hover:scale-105 ${isDark
              ? 'bg-gradient-to-br from-slate-900/80 to-slate-800/60 border border-slate-700/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
              : 'bg-gradient-to-br from-white/90 to-slate-50/80 border border-slate-200/40 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
              }`}>
              <div className={`absolute top-4 right-4 h-3 w-3 rounded-full ${health?.checks?.database?.status === "healthy"
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse'
                : health?.checks?.database?.status === "degraded"
                  ? 'bg-amber-500 shadow-lg shadow-amber-500/50'
                  : 'bg-red-500 shadow-lg shadow-red-500/50'
                }`} />

              {isDark && (
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
              )}

              <div className="relative space-y-4">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 ${isDark
                    ? 'bg-gradient-to-br from-blue-500/30 to-indigo-600/30 shadow-lg shadow-blue-500/20'
                    : 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md'
                    }`}>
                    <Database className="h-6 w-6 text-white" />
                  </div>
                  <div className={`text-right ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    <div className="text-xs font-medium uppercase tracking-wide">Database</div>
                    <div className="text-xs opacity-75">Response Time</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    {health?.checks?.database?.response_time_ms?.toFixed(1) ?? "0"} ms
                  </div>

                  <div className={`h-2 rounded-full overflow-hidden ${isDark ? 'bg-slate-700/50' : 'bg-slate-200/60'
                    }`}>
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${(health?.checks?.database?.response_time_ms ?? 0) < 100
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                        : (health?.checks?.database?.response_time_ms ?? 0) < 500
                          ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                          : 'bg-gradient-to-r from-red-500 to-red-400'
                        }`}
                      style={{
                        width: `${Math.min(100, ((health?.checks?.database?.response_time_ms ?? 0) / 1000) * 100)}%`
                      }}
                    />
                  </div>

                  <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Status: {health?.checks?.database?.status || 'Unknown'}
                  </div>
                </div>
              </div>
            </div>

            <div className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-3 hover:scale-105 ${isDark
              ? 'bg-gradient-to-br from-slate-900/80 to-slate-800/60 border border-slate-700/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
              : 'bg-gradient-to-br from-white/90 to-slate-50/80 border border-slate-200/40 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
              }`}>
              <div className={`absolute top-4 right-4 h-3 w-3 rounded-full ${(health?.checks?.system?.cpu?.usage_percent ?? 0) < 70
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse'
                : (health?.checks?.system?.cpu?.usage_percent ?? 0) < 85
                  ? 'bg-amber-500 shadow-lg shadow-amber-500/50'
                  : 'bg-red-500 shadow-lg shadow-red-500/50'
                }`} />

              {isDark && (
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-orange-500/20 to-red-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
              )}

              <div className="relative space-y-4">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 ${isDark
                    ? 'bg-gradient-to-br from-orange-500/30 to-red-600/30 shadow-lg shadow-orange-500/20'
                    : 'bg-gradient-to-br from-orange-500 to-red-600 shadow-md'
                    }`}>
                    <Cpu className="h-6 w-6 text-white" />
                  </div>
                  <div className={`text-right ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    <div className="text-xs font-medium uppercase tracking-wide">CPU Usage</div>
                    <div className="text-xs opacity-75">Current Load</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    {health?.checks?.system?.cpu?.usage_percent?.toFixed(1) ?? "0"}%
                  </div>

                  <div className={`h-2 rounded-full overflow-hidden ${isDark ? 'bg-slate-700/50' : 'bg-slate-200/60'
                    }`}>
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${(health?.checks?.system?.cpu?.usage_percent ?? 0) < 70
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                        : (health?.checks?.system?.cpu?.usage_percent ?? 0) < 85
                          ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                          : 'bg-gradient-to-r from-red-500 to-red-400'
                        }`}
                      style={{
                        width: `${Math.min(100, health?.checks?.system?.cpu?.usage_percent ?? 0)}%`
                      }}
                    />
                  </div>

                  <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Process ID: {health?.checks?.system?.process_id ?? "Unknown"}
                  </div>
                </div>
              </div>
            </div>

            <div className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-3 hover:scale-105 ${isDark
              ? 'bg-gradient-to-br from-slate-900/80 to-slate-800/60 border border-slate-700/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
              : 'bg-gradient-to-br from-white/90 to-slate-50/80 border border-slate-200/40 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
              }`}>
              <div className={`absolute top-4 right-4 h-3 w-3 rounded-full ${(health?.checks?.system?.memory?.usage_percent ?? 0) < 70
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse'
                : (health?.checks?.system?.memory?.usage_percent ?? 0) < 85
                  ? 'bg-amber-500 shadow-lg shadow-amber-500/50'
                  : 'bg-red-500 shadow-lg shadow-red-500/50'
                }`} />

              {isDark && (
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
              )}

              <div className="relative space-y-4">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 ${isDark
                    ? 'bg-gradient-to-br from-purple-500/30 to-pink-600/30 shadow-lg shadow-purple-500/20'
                    : 'bg-gradient-to-br from-purple-500 to-pink-600 shadow-md'
                    }`}>
                    <MemoryStick className="h-6 w-6 text-white" />
                  </div>
                  <div className={`text-right ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    <div className="text-xs font-medium uppercase tracking-wide">Memory</div>
                    <div className="text-xs opacity-75">Usage</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    {health?.checks?.system?.memory?.usage_percent?.toFixed(1) ?? "0"}%
                  </div>

                  <div className={`h-2 rounded-full overflow-hidden ${isDark ? 'bg-slate-700/50' : 'bg-slate-200/60'
                    }`}>
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${(health?.checks?.system?.memory?.usage_percent ?? 0) < 70
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                        : (health?.checks?.system?.memory?.usage_percent ?? 0) < 85
                          ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                          : 'bg-gradient-to-r from-red-500 to-red-400'
                        }`}
                      style={{
                        width: `${Math.min(100, health?.checks?.system?.memory?.usage_percent ?? 0)}%`
                      }}
                    />
                  </div>

                  <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Available: {health?.checks?.system?.memory?.available_mb ?? 0} MB
                  </div>
                </div>
              </div>
            </div>

            <div className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-500 hover:-translate-y-3 hover:scale-105 ${isDark
              ? 'bg-gradient-to-br from-slate-900/80 to-slate-800/60 border border-slate-700/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
              : 'bg-gradient-to-br from-white/90 to-slate-50/80 border border-slate-200/40 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
              }`}>
              <div className={`absolute top-4 right-4 h-3 w-3 rounded-full ${health?.checks?.rule_engine?.status === "healthy"
                ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse'
                : health?.checks?.rule_engine?.status === "degraded"
                  ? 'bg-amber-500 shadow-lg shadow-amber-500/50'
                  : 'bg-red-500 shadow-lg shadow-red-500/50'
                }`} />

              {isDark && (
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
              )}

              <div className="relative space-y-4">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 ${isDark
                    ? 'bg-gradient-to-br from-indigo-500/30 to-purple-600/30 shadow-lg shadow-indigo-500/20'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md'
                    }`}>
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                  <div className={`text-right ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    <div className="text-xs font-medium uppercase tracking-wide">Rule Engine</div>
                    <div className="text-xs opacity-75">Total Parses</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`text-3xl font-bold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    {health?.checks?.rule_engine?.total_parses ?? 0}
                  </div>

                  {health?.checks?.rule_engine?.successful_parses && health?.checks?.rule_engine?.total_parses && (
                    <>
                      <div className={`h-2 rounded-full overflow-hidden ${isDark ? 'bg-slate-700/50' : 'bg-slate-200/60'
                        }`}>
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-1000"
                          style={{
                            width: `${Math.round((health.checks.rule_engine.successful_parses / health.checks.rule_engine.total_parses) * 100)}%`
                          }}
                        />
                      </div>

                      <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                        Success Rate: {Math.round((health.checks.rule_engine.successful_parses / health.checks.rule_engine.total_parses) * 100)}%
                      </div>
                    </>
                  )}

                  {(!health?.checks?.rule_engine?.successful_parses || !health?.checks?.rule_engine?.total_parses) && (
                    <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                      Status: {health?.checks?.rule_engine?.status || 'Unknown'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {!isLoading && !error && (
          <Card className={`overflow-hidden transition-all duration-500 glass-morphism dashboard-card ${isDark
            ? 'border-slate-700/50 bg-slate-900/30 shadow-2xl shadow-black/20'
            : 'border-slate-200/50 bg-white/70 shadow-xl'
            }`} role="region" aria-labelledby="quick-actions-title">
            <CardHeader className={`border-b transition-all duration-300 ${isDark
              ? 'border-slate-700/50 bg-gradient-to-r from-indigo-900/20 to-purple-900/20'
              : 'border-slate-200/50 bg-gradient-to-r from-indigo-50/50 to-purple-50/50'
              }`}>
              <CardTitle className={`flex items-center gap-3 text-xl transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                }`} id="quick-actions-title">
                <div className={`rounded-lg p-2 shadow-md transition-all duration-300 ${isDark
                  ? 'bg-gradient-to-br from-indigo-500/30 to-purple-600/30 shadow-indigo-500/20'
                  : 'bg-gradient-to-br from-indigo-500 to-purple-600'
                  }`}>
                  <TrendingUp className="h-5 w-5 text-white" aria-hidden />
                </div>
                Quick Actions
              </CardTitle>
              <CardDescription className={`text-base transition-colors duration-300 ${isDark ? 'text-slate-300' : 'text-slate-600'
                }`}>
                Access the control surfaces your team uses most
              </CardDescription>
            </CardHeader>

            <CardContent className="p-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <QuickActionLink href="/convert" title="AI Converter" subtitle="Transform text" icon={Zap} isDark={isDark} />
                <QuickActionLink href="/dictionary" title="Dictionary" subtitle="Manage lexicon" icon={FileText} isDark={isDark} />
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !error && (
          <Card className={`overflow-hidden transition-all duration-500 glass-morphism dashboard-card ${isDark
            ? 'border-slate-700/50 bg-slate-900/30 shadow-2xl shadow-black/20'
            : 'border-slate-200/50 bg-white/70 shadow-xl'
            }`} role="region" aria-labelledby="analytics-title">
            <CardHeader className={`border-b transition-all duration-300 ${isDark
              ? 'border-slate-700/50 bg-gradient-to-r from-purple-900/20 to-pink-900/20'
              : 'border-slate-200/50 bg-gradient-to-r from-purple-50/50 to-pink-50/50'
              }`}>
              <CardTitle className={`flex items-center gap-3 text-xl transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                }`} id="analytics-title">
                <div className={`rounded-lg p-2 shadow-md transition-all duration-300 ${isDark
                  ? 'bg-gradient-to-br from-purple-500/30 to-pink-600/30 shadow-purple-500/20'
                  : 'bg-gradient-to-br from-purple-500 to-pink-600'
                  }`}>
                  <Activity className="h-5 w-5 text-white" aria-hidden />
                </div>
                Advanced Analytics
              </CardTitle>
            </CardHeader>

            <CardContent className="p-6">
              <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                <div className="space-y-4">
                  <h3 className={`flex items-center gap-2 text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    <div className={`h-2 w-2 rounded-full transition-all duration-300 ${isDark
                      ? 'bg-gradient-to-r from-indigo-400 to-purple-400 shadow-lg shadow-indigo-400/50'
                      : 'bg-gradient-to-r from-indigo-500 to-purple-500'
                      }`} />
                    Rule Engine Performance
                  </h3>
                  <div className="space-y-3">
                    <KeyValueRow label="Successful Parses" value={String(health?.checks?.rule_engine?.successful_parses ?? 0)} valueColor="emerald" isDark={isDark} />
                    <KeyValueRow label="Failed Parses" value={String(health?.checks?.rule_engine?.failed_parses ?? 0)} valueColor="rose" isDark={isDark} />
                    <KeyValueRow label="Active Patterns" value={String(health?.checks?.rule_engine?.active_patterns ?? 0)} valueColor="blue" isDark={isDark} />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className={`flex items-center gap-2 text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
                    }`}>
                    <div className={`h-2 w-2 rounded-full transition-all duration-300 ${isDark
                      ? 'bg-gradient-to-r from-blue-400 to-cyan-400 shadow-lg shadow-blue-400/50'
                      : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                      }`} />
                    System Diagnostics
                  </h3>
                  <div className="space-y-3">
                    <KeyValueRow label="Check Duration" value={`${health?.checks?.health_check?.duration_ms?.toFixed(1) ?? "0"} ms`} valueColor="indigo" isDark={isDark} />
                    <KeyValueRow label="Database Pool" value={String(health?.checks?.database?.connection_pool ?? "Unknown")} valueColor="violet" isDark={isDark} />
                    <KeyValueRow label="Test Parse" value={health?.checks?.rule_engine?.test_parse_successful ? "Success" : "Failed"} valueColor={health?.checks?.rule_engine?.test_parse_successful ? "blue" : "rose"} isDark={isDark} />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}





function InfoPanel({ label, value, color }: { label: string; value: string; color: string }) {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 dark:bg-gradient-to-br dark:from-blue-950/30 dark:to-blue-900/20 dark:border-blue-800",
    indigo: "bg-indigo-50 border-indigo-200 dark:bg-gradient-to-br dark:from-indigo-950/30 dark:to-indigo-900/20 dark:border-indigo-800",
    cyan: "bg-cyan-50 border-cyan-200 dark:bg-gradient-to-br dark:from-cyan-950/30 dark:to-cyan-900/20 dark:border-cyan-800",
  };

  const textColors = {
    blue: "text-blue-900 dark:text-blue-300",
    indigo: "text-indigo-900 dark:text-indigo-300",
    cyan: "text-cyan-900 dark:text-cyan-300",
  };

  const labelColors = {
    blue: "text-blue-700 dark:text-blue-400",
    indigo: "text-indigo-700 dark:text-indigo-400",
    cyan: "text-cyan-700 dark:text-cyan-400",
  };

  return (
    <div className={`rounded-xl border p-4 shadow-sm ${colorClasses[color as keyof typeof colorClasses]}`}>
      <p className={`text-sm font-medium ${labelColors[color as keyof typeof labelColors]}`}>{label}</p>
      <p className={`mt-1 text-2xl font-bold ${textColors[color as keyof typeof textColors]}`}>{value}</p>
    </div>
  );
}

function QuickActionLink({ href, title, subtitle, icon: Icon, isDark }: { href: string; title: string; subtitle: string; icon: LucideIcon; isDark: boolean }) {
  return (
    <Link
      href={href}
      className={`group block rounded-xl p-5 transition-all duration-300 hover:-translate-y-2 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 glass-morphism ${isDark
        ? 'border-slate-700/50 bg-slate-800/40 hover:bg-slate-700/60 hover:border-indigo-500/50 focus:ring-indigo-400 focus:ring-offset-slate-950 hover:shadow-2xl hover:shadow-indigo-500/20'
        : 'border-slate-200/50 bg-white/60 hover:bg-white/80 hover:border-indigo-300/50 focus:ring-indigo-500 focus:ring-offset-white hover:shadow-xl'
        }`}
      aria-label={title}
    >
      <div className="flex items-center gap-4">
        <div className={`rounded-lg p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 ${isDark
          ? 'bg-gradient-to-br from-indigo-500/30 to-blue-500/30 shadow-lg shadow-indigo-500/20'
          : 'bg-gradient-to-br from-indigo-100 to-blue-100'
          }`}>
          <Icon className={`h-6 w-6 transition-colors duration-300 ${isDark ? 'text-indigo-300' : 'text-indigo-600'
            }`} aria-hidden />
        </div>
        <div>
          <div className={`font-semibold transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
            }`}>{title}</div>
          <div className={`text-sm transition-colors duration-300 ${isDark ? 'text-slate-300' : 'text-slate-600'
            }`}>{subtitle}</div>
        </div>
      </div>
    </Link>
  );
}

function KeyValueRow({ label, value, valueColor = "blue", isDark }: { label: string; value: string; valueColor?: string; isDark?: boolean }) {
  const colorMap = {
    emerald: isDark ? "text-emerald-400" : "text-emerald-600",
    rose: isDark ? "text-rose-400" : "text-rose-600",
    violet: isDark ? "text-violet-400" : "text-violet-600",
    blue: isDark ? "text-blue-400" : "text-blue-600",
    indigo: isDark ? "text-indigo-400" : "text-indigo-600",
  };

  return (
    <div className={`flex items-center justify-between rounded-lg px-4 py-3 transition-all duration-300 glass-light ${isDark
      ? 'border-slate-700/50 bg-slate-800/40 hover:bg-slate-700/60'
      : 'border-slate-200/50 bg-slate-50/80 hover:bg-slate-100/80'
      }`}>
      <span className={`text-sm font-medium transition-colors duration-300 ${isDark ? 'text-slate-200' : 'text-slate-700'
        }`}>{label}</span>
      <span className={`font-mono text-lg font-bold transition-colors duration-300 ${colorMap[valueColor as keyof typeof colorMap]}`}>{value}</span>
    </div>
  );
}


const highlightToneStyles: Record<HighlightTone, {
  gradient: string;
  icon: string;
  border: string;
  glow: string;
}> = {
  blue: {
    gradient: "from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30",
    icon: "from-blue-500 to-indigo-600",
    border: "border-blue-200 dark:border-blue-800",
    glow: "from-blue-400/20 to-indigo-400/20 dark:from-blue-500/10 dark:to-indigo-500/10",
  },
  emerald: {
    gradient: "from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30",
    icon: "from-emerald-500 to-teal-600",
    border: "border-emerald-200 dark:border-emerald-800",
    glow: "from-emerald-400/20 to-teal-400/20 dark:from-emerald-500/10 dark:to-teal-500/10",
  },
  violet: {
    gradient: "from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30",
    icon: "from-violet-500 to-purple-600",
    border: "border-violet-200 dark:border-violet-800",
    glow: "from-violet-400/20 to-purple-400/20 dark:from-violet-500/10 dark:to-purple-500/10",
  },
  amber: {
    gradient: "from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30",
    icon: "from-amber-500 to-orange-600",
    border: "border-amber-200 dark:border-amber-800",
    glow: "from-amber-400/20 to-orange-400/20 dark:from-amber-500/10 dark:to-orange-500/10",
  },
};

function HighlightTile({ title, value, description, icon: Icon, tone, isDark }: HighlightData & { isDark: boolean }) {
  const styles = highlightToneStyles[tone];

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border p-6 transition-all duration-500 hover:-translate-y-2 hover:scale-105 glass-morphism ${isDark
        ? `${styles.gradient} ${styles.border} shadow-2xl shadow-black/20 hover:shadow-3xl hover:shadow-black/30`
        : `${styles.gradient} ${styles.border} shadow-lg hover:shadow-2xl`
        }`}
      role="group"
      aria-labelledby={`tile-${title}`}
    >
      <div className={`pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full blur-2xl transition-all duration-500 ${isDark
        ? `${styles.glow} opacity-30 group-hover:opacity-60`
        : `${styles.glow} opacity-40 group-hover:opacity-70`
        }`} aria-hidden />

      {isDark && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" aria-hidden />
      )}

      <div className="relative space-y-4">
        <div className="flex items-center justify-between">
          <h3 id={`tile-${title}`} className={`text-sm font-semibold transition-colors duration-300 ${isDark ? 'text-slate-200' : 'text-slate-700'
            }`}>
            {title}
          </h3>
          <div className={`rounded-lg p-2 shadow-md transition-all duration-300 group-hover:scale-110 ${isDark
            ? `bg-gradient-to-br ${styles.icon} shadow-lg shadow-black/20`
            : `bg-gradient-to-br ${styles.icon}`
            }`} aria-hidden>
            <Icon className="h-5 w-5 text-white transition-transform duration-300 group-hover:rotate-12" aria-hidden />
          </div>
        </div>

        <div className={`text-3xl font-bold tracking-tight transition-colors duration-300 ${isDark ? 'text-white' : 'text-slate-900'
          }`}>
          {value}
        </div>

        <p className={`text-sm transition-colors duration-300 ${isDark ? 'text-slate-300' : 'text-slate-600'
          }`}>{description}</p>

        {isDark && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" aria-hidden />
        )}
      </div>
    </div>
  );
}
