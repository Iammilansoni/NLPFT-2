'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Database, Server, X, Wifi, WifiOff } from 'lucide-react';

interface ServiceCheck {
  status: string;
  message: string;
  error: string | null;
  critical: boolean;
  impact: string | null;
}

interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  checks: {
    database: ServiceCheck;
    redis: ServiceCheck;
  };
  metrics: {
    uptime_seconds: number;
    uptime_formatted: string;
    total_requests: number;
  };
  summary: {
    services_total: number;
    services_healthy: number;
    services_critical_down: number;
    operational: boolean;
  };
}

export default function ServiceStatusBanner() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/health`);
      const data: HealthResponse = await response.json();
      setHealth(data);
      setIsLoading(false);
      
      // Auto-dismiss if all services are healthy
      if (data.status === 'healthy') {
        setTimeout(() => setDismissed(true), 3000);
      }
    } catch (error) {
      console.error('Failed to check backend health:', error);
      // Backend unreachable - create error state
      setHealth({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: 'unknown',
        environment: 'unknown',
        checks: {
          database: {
            status: 'unhealthy',
            message: 'Cannot connect to backend',
            error: 'Backend server unreachable',
            critical: true,
            impact: 'All features unavailable'
          },
          redis: {
            status: 'unhealthy',
            message: 'Cannot connect to backend',
            error: 'Backend server unreachable',
            critical: false,
            impact: null
          }
        },
        metrics: {
          uptime_seconds: 0,
          uptime_formatted: '0h 0m 0s',
          total_requests: 0
        },
        summary: {
          services_total: 2,
          services_healthy: 0,
          services_critical_down: 1,
          operational: false
        }
      });
      setIsLoading(false);
    }
  };

  if (isLoading || dismissed) return null;
  if (!health) return null;

  // Don't show banner if system is fully healthy
  if (health.status === 'healthy') return null;

  const isUnhealthy = health.status === 'unhealthy';
  const isDegraded = health.status === 'degraded';
  const dbDown = health.checks.database.status !== 'healthy';
  const redisDown = health.checks.redis.status !== 'healthy';

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 backdrop-blur-lg border-b shadow-2xl transition-all duration-300 ${
      isUnhealthy
        ? 'bg-gradient-to-r from-red-500/95 via-red-600/95 to-red-700/95 border-red-400/30' 
        : 'bg-gradient-to-r from-amber-500/95 via-amber-600/95 to-orange-600/95 border-amber-400/30'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-3">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className={`p-2 rounded-lg mt-0.5 ${
              isUnhealthy ? 'bg-red-700/50' : 'bg-amber-700/50'
            }`}>
              {isUnhealthy ? (
                <WifiOff className="w-6 h-6 text-white" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-white" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="font-bold text-base text-white mb-1 flex items-center gap-2">
                    <span className="inline-block w-2 h-2 bg-white rounded-full animate-pulse"></span>
                    {isUnhealthy ? 'Critical Services Offline' : 'Limited Service Availability'}
                  </h3>
                  <p className="text-white/90 text-sm">
                    {isUnhealthy
                      ? `${health.summary.services_critical_down} critical service${health.summary.services_critical_down > 1 ? 's' : ''} unavailable. Application functionality is limited.`
                      : `${health.summary.services_total - health.summary.services_healthy} optional service${(health.summary.services_total - health.summary.services_healthy) > 1 ? 's' : ''} unavailable. Core features remain operational.`}
                  </p>
                </div>
                <button
                  onClick={() => setDismissed(true)}
                  className="flex-shrink-0 p-2 hover:bg-white/20 rounded-lg transition-all duration-200 text-white/80 hover:text-white"
                  aria-label="Dismiss notification"
                  title="Dismiss"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Service Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                {/* PostgreSQL Card */}
                <div className={`rounded-lg p-3 backdrop-blur-sm border transition-all duration-200 ${
                  dbDown
                    ? 'bg-white/10 border-white/20' 
                    : 'bg-white/15 border-white/30'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-md ${
                      dbDown ? 'bg-white/10' : 'bg-emerald-500/20'
                    }`}>
                      <Database className={`w-5 h-5 ${
                        dbDown ? 'text-white' : 'text-emerald-300'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-white text-sm">PostgreSQL</h4>
                        {health.checks.database.critical && (
                          <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-red-500/30 text-red-100">
                            Critical
                          </span>
                        )}
                        {dbDown ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-white/20 text-white">
                            <AlertCircle className="w-3 h-3" />
                            Offline
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/30 text-emerald-100">
                            <CheckCircle2 className="w-3 h-3" />
                            Online
                          </span>
                        )}
                      </div>
                      <p className="text-white/80 text-xs leading-relaxed">
                        {health.checks.database.message}
                      </p>
                      {health.checks.database.impact && (
                        <p className="text-white/60 text-xs mt-1.5 leading-relaxed">
                          💡 {health.checks.database.impact}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Redis Card */}
                <div className={`rounded-lg p-3 backdrop-blur-sm border transition-all duration-200 ${
                  redisDown
                    ? 'bg-white/10 border-white/20' 
                    : 'bg-white/15 border-white/30'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-md ${
                      redisDown ? 'bg-white/10' : 'bg-emerald-500/20'
                    }`}>
                      <Server className={`w-5 h-5 ${
                        redisDown ? 'text-white' : 'text-emerald-300'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-white text-sm">Redis Cache</h4>
                        {!health.checks.redis.critical && (
                          <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-500/30 text-blue-100">
                            Optional
                          </span>
                        )}
                        {redisDown ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-white/20 text-white">
                            <AlertCircle className="w-3 h-3" />
                            Offline
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/30 text-emerald-100">
                            <CheckCircle2 className="w-3 h-3" />
                            Online
                          </span>
                        )}
                      </div>
                      <p className="text-white/80 text-xs leading-relaxed">
                        {health.checks.redis.message}
                      </p>
                      {health.checks.redis.impact && (
                        <p className="text-white/60 text-xs mt-1.5 leading-relaxed">
                          💡 {health.checks.redis.impact}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* System Status Info */}
              {(isUnhealthy || isDegraded) && (
                <div className="rounded-lg p-3 bg-white/15 border border-white/30 backdrop-blur-sm">
                  <div className="flex items-start gap-2">
                    <Wifi className="w-4 h-4 text-white mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-semibold text-sm">
                          {isUnhealthy ? '🚀 Action Required' : 'ℹ️ System Information'}
                        </p>
                        <span className="text-white/70 text-xs">
                          {health.metrics.uptime_formatted} uptime
                        </span>
                      </div>
                      {isUnhealthy ? (
                        <p className="text-white/90 text-xs leading-relaxed">
                          Critical services are offline. Please ensure PostgreSQL is running and accessible. 
                          <span className="text-white/70">Redis is optional for enhanced features.</span>
                        </p>
                      ) : (
                        <p className="text-white/90 text-xs leading-relaxed">
                          Application is operational with {health.summary.services_healthy} of {health.summary.services_total} services online. 
                          Optional services can be started for enhanced functionality.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
