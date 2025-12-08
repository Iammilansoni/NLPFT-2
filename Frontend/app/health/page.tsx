"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useIsClient } from '@/lib/use-client-only';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { 
  Activity, 
  Database, 
  Cpu, 
  Clock, 
  Server, 
  Zap, 
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Wifi,
  WifiOff,
  HardDrive,
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
        return { 
          label: 'Healthy', 
          icon: CheckCircle2, 
          color: 'emerald',
          gradient: 'from-emerald-500 to-teal-600'
        };
      case 'degraded':
        return { 
          label: 'Degraded', 
          icon: AlertTriangle, 
          color: 'amber',
          gradient: 'from-amber-500 to-orange-600'
        };
      case 'unhealthy':
        return { 
          label: 'Unhealthy', 
          icon: XCircle, 
          color: 'red',
          gradient: 'from-red-500 to-rose-600'
        };
      default:
        return { 
          label: 'Unknown', 
          icon: AlertTriangle, 
          color: 'gray',
          gradient: 'from-gray-500 to-slate-600'
        };
    }
  };

  // Error State
  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className="relative mx-auto w-24 h-24 mb-6">
            <div className="absolute inset-0 bg-red-500/20 rounded-full animate-pulse" />
            <div className="absolute inset-2 bg-gradient-to-br from-red-500 to-rose-600 rounded-full flex items-center justify-center">
              <WifiOff className="h-10 w-10 text-white" />
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-2">Service Unavailable</h2>
          <p className="text-muted-foreground mb-6">
            Unable to connect to the NLPForge health endpoint. Please check if the backend service is running.
          </p>
          <Button onClick={() => fetchHealth()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry Connection
          </Button>
        </motion.div>
      </div>
    );
  }

  const overallStatus = getStatusConfig(health?.status || 'unknown');
  const OverallIcon = overallStatus.icon;

  return (
    <div className="space-y-8 relative">
      {/* Ambient Background */}
      <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className={cn(
          "absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-20 blur-3xl",
          health?.status === 'healthy' ? 'bg-emerald-500' : 
          health?.status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'
        )} />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="space-y-2">
          <motion.h1 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold tracking-tight"
          >
            System Health Monitor
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-muted-foreground"
          >
            Real-time monitoring of NLPForge services and infrastructure
          </motion.p>
        </div>
        
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-4"
        >
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-muted/50 border border-border/50">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
              id="auto-refresh"
            />
            <label htmlFor="auto-refresh" className="text-sm font-medium cursor-pointer">
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
        </motion.div>
      </div>

      {/* Overall Status Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className={cn(
          "relative overflow-hidden rounded-2xl p-[1px]",
          "bg-gradient-to-r",
          overallStatus.gradient
        )}
      >
        <div className="relative rounded-[15px] bg-background/95 backdrop-blur-xl p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className={cn(
                "relative h-16 w-16 rounded-2xl flex items-center justify-center",
                "bg-gradient-to-br shadow-lg",
                overallStatus.gradient
              )}>
                <OverallIcon className="h-8 w-8 text-white" />
                {health?.status === 'healthy' && (
                  <div className="absolute inset-0 rounded-2xl bg-white/20 animate-pulse" />
                )}
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Overall System Status</div>
                <div className="text-2xl font-bold">{overallStatus.label}</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6 text-center md:text-right">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Uptime</div>
                <div className="text-lg font-semibold font-mono">
                  {health?.checks?.application?.uptime_seconds 
                    ? formatUptime(health.checks.application.uptime_seconds)
                    : '--'}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Version</div>
                <div className="text-lg font-semibold font-mono">
                  {health?.version || '--'}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Last Check</div>
                <div className="text-lg font-semibold font-mono">
                  {isClient ? lastRefresh.toLocaleTimeString() : '--:--:--'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Service Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ServiceCard
          title="Backend API"
          description="FastAPI Server"
          status={health?.status || 'unknown'}
          icon={<Server className="h-5 w-5" />}
          gradient="from-violet-500 to-purple-600"
          metrics={[
            { label: 'Response', value: `${health?.checks?.health_check?.duration_ms?.toFixed(1) || '0'}ms` },
            { label: 'PID', value: health?.checks?.system?.process_id || '--' }
          ]}
          delay={0.3}
        />
        <ServiceCard
          title="PostgreSQL"
          description="Primary Database"
          status={health?.checks?.database?.status || 'unknown'}
          icon={<Database className="h-5 w-5" />}
          gradient="from-blue-500 to-cyan-600"
          metrics={[
            { label: 'Latency', value: `${health?.checks?.database?.response_time_ms?.toFixed(1) || '0'}ms` },
            { label: 'Pool', value: health?.checks?.database?.connection_pool || '--' }
          ]}
          delay={0.4}
        />
        <ServiceCard
          title="Redis"
          description="Vector Store & Cache"
          status={health?.checks?.redis?.status || 'unknown'}
          icon={<Zap className="h-5 w-5" />}
          gradient="from-rose-500 to-orange-600"
          metrics={[
            { label: 'Latency', value: `${health?.checks?.redis?.response_time_ms?.toFixed(1) || '0'}ms` },
            { label: 'Memory', value: health?.checks?.redis?.used_memory || '--' }
          ]}
          delay={0.5}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Resources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-border/50 bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Cpu className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">System Resources</h3>
                <p className="text-xs text-muted-foreground">CPU and memory utilization</p>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-6">
            <ResourceMeter
              label="CPU Usage"
              value={health?.checks?.system?.cpu?.usage_percent || 0}
              icon={<Gauge className="h-4 w-4" />}
              status={health?.checks?.system?.cpu?.status}
            />
            <ResourceMeter
              label="Memory Usage"
              value={health?.checks?.system?.memory?.usage_percent || 0}
              icon={<MemoryStick className="h-4 w-4" />}
              status={health?.checks?.system?.memory?.status}
              subtitle={health?.checks?.system?.memory ? 
                `${health.checks.system.memory.available_mb}MB free of ${health.checks.system.memory.total_mb}MB` : 
                undefined
              }
            />
          </div>
        </motion.div>

        {/* Rule Engine */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-border/50 bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                <Activity className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">NLP Rule Engine</h3>
                <p className="text-xs text-muted-foreground">Processing engine performance</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <MetricTile
                label="Total Parses"
                value={health?.checks?.rule_engine?.total_parses || 0}
                icon={<Hash className="h-4 w-4" />}
              />
              <MetricTile
                label="Success Rate"
                value={health?.checks?.rule_engine?.total_parses ? 
                  `${((health.checks.rule_engine.successful_parses || 0) / health.checks.rule_engine.total_parses * 100).toFixed(1)}%` : 
                  '0%'
                }
                icon={<TrendingUp className="h-4 w-4" />}
              />
              <MetricTile
                label="Response Time"
                value={`${health?.checks?.rule_engine?.response_time_ms?.toFixed(1) || '0'}ms`}
                icon={<Timer className="h-4 w-4" />}
              />
              <MetricTile
                label="Active Patterns"
                value={health?.checks?.rule_engine?.active_patterns || 0}
                icon={<Zap className="h-4 w-4" />}
              />
            </div>
            
            <div className="mt-4 pt-4 border-t border-border/50">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Test Parse Status</span>
                <span className={cn(
                  "text-sm font-medium flex items-center gap-2",
                  health?.checks?.rule_engine?.test_parse_successful ? 'text-emerald-500' : 'text-red-500'
                )}>
                  {health?.checks?.rule_engine?.test_parse_successful ? (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      Passing
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4" />
                      Failed
                    </>
                  )}
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Loading Overlay */}
      <AnimatePresence>
        {!health && !error && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <div className="text-center">
              <div className="relative mx-auto w-16 h-16 mb-4">
                <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary animate-spin" />
              </div>
              <p className="text-muted-foreground">Loading health status...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Service Card Component
function ServiceCard({
  title,
  description,
  status,
  icon,
  gradient,
  metrics,
  delay
}: {
  title: string;
  description: string;
  status: string;
  icon: React.ReactNode;
  gradient: string;
  metrics: { label: string; value: string | number }[];
  delay: number;
}) {
  const isHealthy = status === 'healthy';
  const isUnknown = status === 'unknown';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={cn(
        "relative rounded-2xl p-[1px] transition-all duration-300",
        "bg-gradient-to-br",
        isHealthy ? gradient : isUnknown ? 'from-gray-500/50 to-slate-600/50' : 'from-red-500/50 to-rose-600/50'
      )}
    >
      <div className="rounded-[15px] bg-background/95 backdrop-blur-sm p-5 h-full">
        <div className="flex items-start justify-between mb-4">
          <div className={cn(
            "h-11 w-11 rounded-xl flex items-center justify-center",
            isHealthy ? `bg-gradient-to-br ${gradient} text-white shadow-lg` : 
            isUnknown ? 'bg-muted text-muted-foreground' :
            'bg-red-500/10 text-red-500'
          )}>
            {icon}
          </div>
          
          <div className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
            isHealthy && 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
            isUnknown && 'bg-gray-500/10 text-gray-600 dark:text-gray-400',
            !isHealthy && !isUnknown && 'bg-red-500/10 text-red-600 dark:text-red-400'
          )}>
            <span className={cn(
              "h-1.5 w-1.5 rounded-full",
              isHealthy && 'bg-emerald-500',
              isUnknown && 'bg-gray-500 animate-pulse',
              !isHealthy && !isUnknown && 'bg-red-500'
            )} />
            {isHealthy ? 'Online' : isUnknown ? 'Checking' : 'Offline'}
          </div>
        </div>
        
        <h4 className="font-semibold mb-0.5">{title}</h4>
        <p className="text-xs text-muted-foreground mb-4">{description}</p>
        
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border/50">
          {metrics.map((metric, i) => (
            <div key={i}>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{metric.label}</div>
              <div className="text-sm font-mono font-medium">{metric.value}</div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// Resource Meter Component
function ResourceMeter({
  label,
  value,
  icon,
  status,
  subtitle
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  status?: string;
  subtitle?: string;
}) {
  const getColor = () => {
    if (value < 50) return 'emerald';
    if (value < 80) return 'amber';
    return 'red';
  };

  const color = getColor();

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{icon}</span>
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className={cn(
          "text-sm font-mono font-semibold",
          color === 'emerald' && 'text-emerald-500',
          color === 'amber' && 'text-amber-500',
          color === 'red' && 'text-red-500'
        )}>
          {value.toFixed(1)}%
        </span>
      </div>
      
      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={cn(
            "absolute inset-y-0 left-0 rounded-full",
            color === 'emerald' && 'bg-gradient-to-r from-emerald-500 to-teal-500',
            color === 'amber' && 'bg-gradient-to-r from-amber-500 to-orange-500',
            color === 'red' && 'bg-gradient-to-r from-red-500 to-rose-500'
          )}
        />
      </div>
      
      {subtitle && (
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      )}
    </div>
  );
}

// Metric Tile Component
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
    <div className="p-3 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-lg font-semibold font-mono">{value}</div>
    </div>
  );
}