"use client";

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { HealthStatus } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Database, Cpu, MemoryStick, Clock, Server, Zap, FileText } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: health, isLoading, error } = useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading system status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-destructive mb-4">
            <Server className="h-12 w-12 mx-auto mb-2" />
            <h2 className="text-xl font-semibold">Service Unavailable</h2>
          </div>
          <p className="text-muted-foreground mb-4">
            Unable to connect to the NLP service. Please check if the backend server is running.
          </p>
          <Button onClick={() => window.location.reload()}>Try Again</Button>
        </div>
      </div>
    );
  }

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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">NLPForge Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor your NLP service status and access key features
        </p>
      </div>

      {/* Overall Status */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Status
            </CardTitle>
            {getStatusBadge(health?.status || 'unknown')}
          </div>
          <CardDescription>
            Last updated: {health?.timestamp ? api.formatDateTime(health.timestamp) : 'Unknown'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-medium">Version</p>
              <p className="text-muted-foreground">{health?.version}</p>
            </div>
            <div>
              <p className="font-medium">Uptime</p>
              <p className="text-muted-foreground">
                {health?.checks?.application?.uptime_seconds 
                  ? formatUptime(health.checks.application.uptime_seconds)
                  : 'Unknown'}
              </p>
            </div>
            <div>
              <p className="font-medium">Process ID</p>
              <p className="text-muted-foreground">{health?.checks?.system?.process_id || 'Unknown'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Database Status */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4" />
              Database
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(health?.checks?.database?.status || 'unknown')}
              <div className="text-2xl font-bold">
                {health?.checks?.database?.response_time_ms?.toFixed(1) || '0'}ms
              </div>
              <p className="text-xs text-muted-foreground">Response Time</p>
            </div>
          </CardContent>
        </Card>

        {/* CPU Usage */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(health?.checks?.system?.cpu?.status || 'unknown')}
              <div className="text-2xl font-bold">
                {health?.checks?.system?.cpu?.usage_percent?.toFixed(1) || '0'}%
              </div>
              <p className="text-xs text-muted-foreground">Current Load</p>
            </div>
          </CardContent>
        </Card>

        {/* Memory Usage */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <MemoryStick className="h-4 w-4" />
              Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(health?.checks?.system?.memory?.status || 'unknown')}
              <div className="text-2xl font-bold">
                {health?.checks?.system?.memory?.usage_percent?.toFixed(1) || '0'}%
              </div>
              <p className="text-xs text-muted-foreground">
                {health?.checks?.system?.memory?.available_mb || 0} MB available
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Rule Engine */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Rule Engine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(health?.checks?.rule_engine?.status || 'unknown')}
              <div className="text-2xl font-bold">
                {health?.checks?.rule_engine?.total_parses || 0}
              </div>
              <p className="text-xs text-muted-foreground">Total Parses</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Access key features and tools
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/health">
              <Button variant="outline" className="w-full justify-start">
                <Activity className="h-4 w-4 mr-2" />
                Detailed Health
              </Button>
            </Link>
            <Link href="/convert">
              <Button variant="outline" className="w-full justify-start">
                <Zap className="h-4 w-4 mr-2" />
                Convert Text
              </Button>
            </Link>
            <Link href="/dictionary">
              <Button variant="outline" className="w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                Manage Dictionary
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-muted-foreground">Rule Engine Performance</p>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between">
                    <span>Successful Parses:</span>
                    <span className="font-mono">{health?.checks?.rule_engine?.successful_parses || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failed Parses:</span>
                    <span className="font-mono">{health?.checks?.rule_engine?.failed_parses || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Active Patterns:</span>
                    <span className="font-mono">{health?.checks?.rule_engine?.active_patterns || 0}</span>
                  </div>
                </div>
              </div>
              <div>
                <p className="font-medium text-muted-foreground">Health Check Details</p>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between">
                    <span>Check Duration:</span>
                    <span className="font-mono">{health?.checks?.health_check?.duration_ms?.toFixed(1) || '0'}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Database Pool:</span>
                    <span className="font-mono">{health?.checks?.database?.connection_pool || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Test Parse:</span>
                    <span className={`font-mono ${health?.checks?.rule_engine?.test_parse_successful ? 'text-green-600' : 'text-red-600'}`}>
                      {health?.checks?.rule_engine?.test_parse_successful ? 'Success' : 'Failed'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
