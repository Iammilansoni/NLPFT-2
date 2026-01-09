"use client";

import { useState, useEffect } from 'react';
import { getApiBase } from '@/lib/runtime-config';
import { useIsClient } from '@/lib/use-client-only';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import {
  Activity,
  Database,
  Cpu,
  Server,
  Zap,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  WifiOff,
  MemoryStick,
  Gauge,
  Timer,
  Hash,
  TrendingUp
} from 'lucide-react';

export default function HealthPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(5000);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [isRefetching, setIsRefetching] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<any>(null);
  const isClient = useIsClient();

  const fetchHealth = async () => {
    try {
      setIsRefetching(true);
      const RAW_API_BASE = getApiBase();
      const apiUrl = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : '';
      const response = await fetch(`${apiUrl}/api/v1/health`);
      if (!response.ok) {
        throw new Error('Failed to fetch health');
      }
      const data = await response.json();
      setHealth(data);
      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setIsRefetching(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    if (!autoRefresh) return;
    const interval = setInterval(fetchHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours < 24) return `${hours}h ${minutes}m`;
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'healthy':
        return { label: 'Healthy', icon: CheckCircle2, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30' };
      case 'degraded':
        return { label: 'Degraded', icon: AlertTriangle, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' };
      case 'unhealthy':
        return { label: 'Unhealthy', icon: XCircle, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30' };
      default:
        return { label: 'Unknown', icon: AlertTriangle, color: 'text-muted-foreground', bg: 'bg-muted' };
    }
  };

  // Error State
  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="mx-auto w-16 h-16 mb-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <WifiOff className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Service Unavailable</h2>
          <p className="text-muted-foreground mb-6 text-sm">
            Unable to connect to the health endpoint. Check if the backend is running.
          </p>
          <Button onClick={() => fetchHealth()} size="sm" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  // Loading State
  if (!health && !error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto w-12 h-12 mb-4 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
          <p className="text-sm text-muted-foreground">Loading health status...</p>
        </div>
      </div>
    );
  }

  const overallStatus = getStatusConfig(health?.status || 'unknown');
  const OverallIcon = overallStatus.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">System Health</h1>
          <p className="text-sm text-muted-foreground">
            Real-time monitoring of NLPForge services
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted border border-border">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
              id="auto-refresh"
              className="scale-90"
            />
            <label htmlFor="auto-refresh" className="text-xs font-medium cursor-pointer">
              Auto-refresh
            </label>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchHealth()}
            disabled={isRefetching}
            className="gap-2"
          >
            <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Status Card */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={cn("h-12 w-12 rounded-lg flex items-center justify-center", overallStatus.bg)}>
              <OverallIcon className={cn("h-6 w-6", overallStatus.color)} />
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-0.5">Overall Status</div>
              <div className="text-xl font-semibold">{overallStatus.label}</div>
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm">
            <div>
              <div className="text-xs text-muted-foreground mb-0.5">Uptime</div>
              <div className="font-mono font-medium">
                {health?.checks?.application?.uptime_seconds
                  ? formatUptime(health.checks.application.uptime_seconds)
                  : '--'}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-0.5">Version</div>
              <div className="font-mono font-medium">
                {health?.version || '--'}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-0.5">Last Check</div>
              <div className="font-mono font-medium">
                {isClient ? lastRefresh.toLocaleTimeString() : '--:--:--'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ServiceCard
          title="Backend API"
          description="FastAPI Server"
          status={health?.status || 'unknown'}
          icon={<Server className="h-5 w-5" />}
          metrics={[
            { label: 'Response', value: `${health?.checks?.health_check?.duration_ms?.toFixed(1) || '0'}ms` },
            { label: 'PID', value: health?.checks?.system?.process_id || '--' }
          ]}
        />
        <ServiceCard
          title="PostgreSQL"
          description="Primary Database"
          status={health?.checks?.database?.status || 'unknown'}
          icon={<Database className="h-5 w-5" />}
          metrics={[
            { label: 'Latency', value: `${health?.checks?.database?.response_time_ms?.toFixed(1) || '0'}ms` },
            { label: 'Pool', value: health?.checks?.database?.connection_pool || '--' }
          ]}
        />
        <ServiceCard
          title="Redis"
          description="Vector Store & Cache"
          status={health?.checks?.redis?.status || 'unknown'}
          icon={<Zap className="h-5 w-5" />}
          metrics={[
            { label: 'Latency', value: `${health?.checks?.redis?.response_time_ms?.toFixed(1) || '0'}ms` },
            { label: 'Memory', value: health?.checks?.redis?.used_memory || '--' }
          ]}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* System Resources */}
        <div className="rounded-lg border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center">
                <Cpu className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-medium">System Resources</h3>
                <p className="text-xs text-muted-foreground">CPU and memory utilization</p>
              </div>
            </div>
          </div>
          <div className="p-4 space-y-4">
            <ResourceMeter
              label="CPU Usage"
              value={health?.checks?.system?.cpu?.usage_percent || 0}
              icon={<Gauge className="h-4 w-4" />}
            />
            <ResourceMeter
              label="Memory Usage"
              value={health?.checks?.system?.memory?.usage_percent || 0}
              icon={<MemoryStick className="h-4 w-4" />}
              subtitle={health?.checks?.system?.memory ?
                `${health.checks.system.memory.available_mb}MB free of ${health.checks.system.memory.total_mb}MB` :
                undefined
              }
            />
          </div>
        </div>

        {/* Rule Engine */}
        <div className="rounded-lg border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center">
                <Activity className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-medium">NLP Rule Engine</h3>
                <p className="text-xs text-muted-foreground">Processing engine performance</p>
              </div>
            </div>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-3">
              <MetricTile
                label="Total Parses"
                value={health?.checks?.rule_engine?.total_parses || 0}
                icon={<Hash className="h-3.5 w-3.5" />}
              />
              <MetricTile
                label="Success Rate"
                value={health?.checks?.rule_engine?.total_parses ?
                  `${((health.checks.rule_engine.successful_parses || 0) / health.checks.rule_engine.total_parses * 100).toFixed(1)}%` :
                  '0%'
                }
                icon={<TrendingUp className="h-3.5 w-3.5" />}
              />
              <MetricTile
                label="Response Time"
                value={`${health?.checks?.rule_engine?.response_time_ms?.toFixed(1) || '0'}ms`}
                icon={<Timer className="h-3.5 w-3.5" />}
              />
              <MetricTile
                label="Active Patterns"
                value={health?.checks?.rule_engine?.active_patterns || 0}
                icon={<Zap className="h-3.5 w-3.5" />}
              />
            </div>

            <div className="mt-3 pt-3 border-t flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Test Parse Status</span>
              <span className={cn(
                "font-medium flex items-center gap-1.5",
                health?.checks?.rule_engine?.test_parse_successful ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              )}>
                {health?.checks?.rule_engine?.test_parse_successful ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Passing
                  </>
                ) : (
                  <>
                    <XCircle className="h-3.5 w-3.5" />
                    Failed
                  </>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Service Card Component - Enterprise Calm
function ServiceCard({
  title,
  description,
  status,
  icon,
  metrics,
}: {
  title: string;
  description: string;
  status: string;
  icon: React.ReactNode;
  metrics: { label: string; value: string | number }[];
}) {
  const isHealthy = status === 'healthy';
  const isUnknown = status === 'unknown';

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between mb-3">
        <div className={cn(
          "h-10 w-10 rounded-lg flex items-center justify-center",
          isHealthy ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
            isUnknown ? 'bg-muted text-muted-foreground' :
              'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
        )}>
          {icon}
        </div>

        <div className={cn(
          "flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
          isHealthy && 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
          isUnknown && 'bg-muted text-muted-foreground',
          !isHealthy && !isUnknown && 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
        )}>
          <span className={cn(
            "h-1.5 w-1.5 rounded-full",
            isHealthy && 'bg-green-500',
            isUnknown && 'bg-muted-foreground',
            !isHealthy && !isUnknown && 'bg-red-500'
          )} />
          {isHealthy ? 'Online' : isUnknown ? 'Checking' : 'Offline'}
        </div>
      </div>

      <h4 className="font-medium text-sm mb-0.5">{title}</h4>
      <p className="text-xs text-muted-foreground mb-3">{description}</p>

      <div className="grid grid-cols-2 gap-3 pt-3 border-t">
        {metrics.map((metric, i) => (
          <div key={i}>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{metric.label}</div>
            <div className="text-sm font-mono font-medium">{metric.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Resource Meter Component - Enterprise Calm
function ResourceMeter({
  label,
  value,
  icon,
  subtitle
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  subtitle?: string;
}) {
  const getColor = () => {
    if (value < 50) return 'bg-green-500';
    if (value < 80) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{icon}</span>
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className="text-sm font-mono font-medium tabular-nums">
          {value.toFixed(1)}%
        </span>
      </div>

      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-300", getColor())}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>

      {subtitle && (
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      )}
    </div>
  );
}

// Metric Tile Component - Enterprise Calm
function MetricTile({
  label,
  value,
  icon
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}) {
  return (
    <div className="p-3 rounded-md bg-muted/50">
      <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-base font-semibold font-mono tabular-nums">{value}</div>
    </div>
  );
}