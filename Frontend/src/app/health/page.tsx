"use client";

import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { HealthStatus } from '@/lib/types';
import { useIsClient } from '@/lib/use-client-only';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Database, 
  Cpu, 
  Clock, 
  Server, 
  Zap, 
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Pause,
  Play
} from 'lucide-react';

export default function HealthPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(5000); // 5 seconds
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const isClient = useIsClient();

  const { 
    data: health, 
    isLoading, 
    error, 
    refetch,
    isRefetching 
  } = useQuery<HealthStatus>({
    queryKey: ['health-detailed'],
    queryFn: api.getHealth,
    refetchInterval: autoRefresh ? refreshInterval : false,
    refetchIntervalInBackground: true,
  });

  useEffect(() => {
    if (health) {
      setLastRefresh(new Date());
    }
  }, [health]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-500/10 text-green-700 dark:text-green-400">Healthy</Badge>;
      case 'degraded':
        return <Badge className="bg-yellow-500/10 text-yellow-700 dark:text-yellow-400">Degraded</Badge>;
      case 'unhealthy':
        return <Badge className="bg-red-500/10 text-red-700 dark:text-red-400">Unhealthy</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-destructive mb-4">
            <Server className="h-12 w-12 mx-auto mb-2" />
            <h2 className="text-xl font-semibold">Service Unavailable</h2>
          </div>
          <p className="text-muted-foreground mb-4">
            Unable to connect to the NLP service health endpoint.
          </p>
          <Button onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">System Health Monitor</h1>
          <p className="text-muted-foreground">
            Real-time monitoring of NLPForge service health and performance
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
              id="auto-refresh"
            />
            <label htmlFor="auto-refresh" className="text-sm">
              Auto-refresh
            </label>
          </div>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            {isRefetching ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className={`border-l-4 ${
          health?.status === 'healthy' ? 'border-l-green-500' :
          health?.status === 'degraded' ? 'border-l-yellow-500' :
          health?.status === 'unhealthy' ? 'border-l-red-500' : 'border-l-gray-500'
        }`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {getStatusIcon(health?.status || 'unknown')}
              Overall Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(health?.status || 'unknown')}
              <p className="text-xs text-muted-foreground">
                Last check: {isClient ? api.formatTime(lastRefresh) : '--:--:--'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Uptime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {health?.checks?.application?.uptime_seconds 
                  ? formatUptime(health.checks.application.uptime_seconds)
                  : 'Unknown'}
              </div>
              <p className="text-xs text-muted-foreground">
                Since startup
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              Version
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {health?.version || 'Unknown'}
              </div>
              <p className="text-xs text-muted-foreground">
                Application version
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Response Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {health?.checks?.health_check?.duration_ms?.toFixed(1) || '0'}ms
              </div>
              <p className="text-xs text-muted-foreground">
                Health check duration
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Component Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Database Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Database Health
            </CardTitle>
            <CardDescription>MongoDB connection and performance metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              {getStatusBadge(health?.checks?.database?.status || 'unknown')}
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Response Time</span>
                <span className="font-mono">
                  {health?.checks?.database?.response_time_ms?.toFixed(2) || '0'}ms
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span>Connection Pool</span>
                <span className="font-mono capitalize">
                  {health?.checks?.database?.connection_pool || 'Unknown'}
                </span>
              </div>
            </div>

            {health?.checks?.database?.response_time_ms && (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">Response Time Indicator</div>
                <Progress 
                  value={Math.min((health.checks.database.response_time_ms / 100) * 100, 100)} 
                  className="h-2"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* System Resources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              System Resources
            </CardTitle>
            <CardDescription>CPU and memory usage statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* CPU Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">CPU Usage</span>
                <div className="flex items-center gap-2">
                  {getStatusBadge(health?.checks?.system?.cpu?.status || 'unknown')}
                  <span className="font-mono text-sm">
                    {health?.checks?.system?.cpu?.usage_percent?.toFixed(1) || '0'}%
                  </span>
                </div>
              </div>
              {health?.checks?.system?.cpu?.usage_percent && (
                <Progress 
                  value={health.checks.system.cpu.usage_percent} 
                  className="h-2"
                />
              )}
            </div>

            {/* Memory Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Memory Usage</span>
                <div className="flex items-center gap-2">
                  {getStatusBadge(health?.checks?.system?.memory?.status || 'unknown')}
                  <span className="font-mono text-sm">
                    {health?.checks?.system?.memory?.usage_percent?.toFixed(1) || '0'}%
                  </span>
                </div>
              </div>
              {health?.checks?.system?.memory?.usage_percent && (
                <Progress 
                  value={health.checks.system.memory.usage_percent} 
                  className="h-2"
                />
              )}
              {health?.checks?.system?.memory && (
                <div className="text-xs text-muted-foreground">
                  {health.checks.system.memory.available_mb}MB available of {health.checks.system.memory.total_mb}MB total
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Rule Engine Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Rule Engine
            </CardTitle>
            <CardDescription>NLP processing engine performance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              {getStatusBadge(health?.checks?.rule_engine?.status || 'unknown')}
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-1">
                <div className="text-muted-foreground">Total Parses</div>
                <div className="font-mono text-lg">
                  {health?.checks?.rule_engine?.total_parses || 0}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Success Rate</div>
                <div className="font-mono text-lg">
                  {health?.checks?.rule_engine?.total_parses ? (
                    ((health.checks.rule_engine.successful_parses || 0) / health.checks.rule_engine.total_parses * 100).toFixed(1)
                  ) : '0'}%
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Response Time</div>
                <div className="font-mono text-lg">
                  {health?.checks?.rule_engine?.response_time_ms?.toFixed(1) || '0'}ms
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Active Patterns</div>
                <div className="font-mono text-lg">
                  {health?.checks?.rule_engine?.active_patterns || 0}
                </div>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center justify-between text-sm">
                <span>Test Parse Status</span>
                <span className={`font-mono ${health?.checks?.rule_engine?.test_parse_successful ? 'text-green-600' : 'text-red-600'}`}>
                  {health?.checks?.rule_engine?.test_parse_successful ? 'Success' : 'Failed'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Application Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Application Details
            </CardTitle>
            <CardDescription>Runtime and configuration information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-3 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-muted-foreground">Process ID</span>
                <span className="font-mono">{health?.checks?.system?.process_id || 'Unknown'}</span>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-muted-foreground">Application Status</span>
                <Badge variant="outline">
                  {health?.checks?.application?.status || 'Unknown'}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-muted-foreground">Startup Time</span>
                <span className="font-mono">
                  {isClient && health?.timestamp ? api.formatDateTime(health.timestamp) : '--'}
                </span>
              </div>
              
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">Auto Refresh</span>
                <div className="flex items-center gap-2">
                  {autoRefresh ? <Play className="h-3 w-3 text-green-500" /> : <Pause className="h-3 w-3 text-gray-500" />}
                  <span className="text-xs">
                    {autoRefresh ? `Every ${refreshInterval/1000}s` : 'Disabled'}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Loading State Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading health status...</p>
          </div>
        </div>
      )}
    </div>
  );
}