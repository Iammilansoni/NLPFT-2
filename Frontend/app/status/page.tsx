'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Database, RefreshCw, Server, XCircle } from 'lucide-react';

interface ServiceStatus {
  postgresql: {
    connected: boolean;
    status: string;
    error?: string;
    message: string;
  };
  redis: {
    connected: boolean;
    status: string;
    error?: string;
    message: string;
  };
}

interface HealthResponse {
  status: string;
  services: ServiceStatus;
  timestamp: string;
  uptime_seconds: number;
  total_requests: number;
}

export default function StatusPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const checkHealth = async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/health`);
      const data = await response.json();
      // Transform backend response to match frontend structure
      const transformedData = {
        status: data.status,
        services: {
          postgresql: {
            connected: data.checks?.database?.status === 'healthy',
            status: data.checks?.database?.status || 'unknown',
            error: data.checks?.database?.error || null,
            message: data.checks?.database?.message || (data.checks?.database?.status === 'healthy' ? 'Database operational' : 'Database unavailable')
          },
          redis: {
            connected: data.checks?.redis?.status === 'healthy',
            status: data.checks?.redis?.status || 'unknown',
            error: data.checks?.redis?.error || null,
            message: data.checks?.redis?.message || (data.checks?.redis?.status === 'healthy' ? 'Redis operational' : 'Limited functionality')
          }
        },
        timestamp: data.timestamp,
        uptime_seconds: data.uptime_seconds || 0,
        total_requests: data.total_requests || 0
      };
      setHealth(transformedData);
      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to check backend health:', error);
      setHealth({
        status: 'error',
        services: {
          postgresql: {
            connected: false,
            status: 'disconnected',
            error: 'Backend unreachable',
            message: 'Cannot connect to backend server'
          },
          redis: {
            connected: false,
            status: 'disconnected',
            error: 'Backend unreachable',
            message: 'Cannot connect to backend server'
          }
        },
        timestamp: new Date().toISOString(),
        uptime_seconds: 0,
        total_requests: 0
      });
      setLastChecked(new Date());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    if (autoRefresh) {
      const interval = setInterval(checkHealth, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const allOperational = health?.services.postgresql.connected && health?.services.redis.connected;
  const criticalDown = health && !health.services.postgresql.connected;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-200 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-3">
                <span className={`inline-block w-3 h-3 rounded-full ${
                  allOperational ? 'bg-green-500 animate-pulse' : criticalDown ? 'bg-red-500 animate-pulse' : 'bg-yellow-500 animate-pulse'
                }`}></span>
                System Status
              </h1>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Real-time monitoring of backend services and infrastructure
              </p>
            </div>
          </div>
        </div>

        {/* Overall Status Hero */}
        <div className="bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className={`p-4 rounded-xl ${
                allOperational ? 'bg-green-500/20' : criticalDown ? 'bg-red-500/20' : 'bg-yellow-500/20'
              }`}>
                {allOperational ? (
                  <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                ) : criticalDown ? (
                  <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                ) : (
                  <AlertCircle className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                )}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
                  {allOperational ? 'All Systems Operational' : criticalDown ? 'Service Disruption' : 'Partial Outage'}
                </h2>
                <p className="text-slate-600 dark:text-slate-400">
                  {allOperational 
                    ? 'All services are running normally' 
                    : criticalDown 
                      ? 'Critical services are currently unavailable' 
                      : 'Some non-critical services are experiencing issues'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 rounded-lg border transition-all ${
                  autoRefresh 
                    ? 'bg-blue-500 text-white border-blue-600' 
                    : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600'
                }`}
              >
                {autoRefresh ? '⏸ Pause' : '▶ Resume'}
              </button>
              <button
                onClick={checkHealth}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all shadow-lg hover:shadow-xl"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {health && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <div className={`text-3xl font-bold mb-2 ${
                  allOperational ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {allOperational ? '✓' : '✗'} {allOperational ? 'Operational' : 'Degraded'}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 font-medium">System Status</div>
              </div>
              <div className="text-center p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {formatUptime(health.uptime_seconds)}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 font-medium">Server Uptime</div>
              </div>
              <div className="text-center p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                  {health.total_requests.toLocaleString()}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 font-medium">Total Requests</div>
              </div>
            </div>
          )}

          {lastChecked && (
            <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
              <span>Last checked: {lastChecked.toLocaleTimeString()}</span>
              {autoRefresh && <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> Auto-refresh: 10s</span>}
            </div>
          )}
        </div>

        {/* Service Details */}
        <div className="space-y-4">
          {/* PostgreSQL */}
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${
                health?.services.postgresql.connected 
                  ? 'bg-green-100 dark:bg-green-900' 
                  : 'bg-red-100 dark:bg-red-900'
              }`}>
                <Database className={`w-6 h-6 ${
                  health?.services.postgresql.connected 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    PostgreSQL Database
                  </h3>
                  {health?.services.postgresql.connected ? (
                    <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  )}
                </div>
                <p className="text-slate-600 dark:text-slate-400 mb-2">
                  {health?.services.postgresql.message}
                </p>
                {health?.services.postgresql.error && (
                  <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-red-700 dark:text-red-300">
                        <div className="font-medium mb-1">Error Details:</div>
                        <div className="font-mono text-xs">{health.services.postgresql.error}</div>
                      </div>
                    </div>
                  </div>
                )}
                {!health?.services.postgresql.connected && (
                  <div className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                    <strong>Impact:</strong> Authentication, templates, and data persistence unavailable
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Redis */}
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${
                health?.services.redis.connected 
                  ? 'bg-green-100 dark:bg-green-900' 
                  : 'bg-yellow-100 dark:bg-yellow-900'
              }`}>
                <Server className={`w-6 h-6 ${
                  health?.services.redis.connected 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-yellow-600 dark:text-yellow-400'
                }`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Redis Cache
                  </h3>
                  {health?.services.redis.connected ? (
                    <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                  )}
                </div>
                <p className="text-slate-600 dark:text-slate-400 mb-2">
                  {health?.services.redis.message}
                </p>
                {health?.services.redis.error && (
                  <div className="mt-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-800">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-yellow-700 dark:text-yellow-300">
                        <div className="font-medium mb-1">Error Details:</div>
                        <div className="font-mono text-xs">{health.services.redis.error}</div>
                      </div>
                    </div>
                  </div>
                )}
                {!health?.services.redis.connected && (
                  <div className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                    <strong>Impact:</strong> Vector search and embedding features disabled (optional service)
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
