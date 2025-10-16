import { Activity, Database, Cpu, Zap, Clock, FileText, TrendingUp, Shield } from 'lucide-react';
import { useTheme } from "next-themes";

interface PlaceholderMetricsProps {
  mode?: 'loading' | 'offline';
}

export function PlaceholderMetrics({ mode = 'loading' }: PlaceholderMetricsProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  
  const offlineStats = [
    { label: 'Platform Uptime', value: 'Offline', description: 'Backend unavailable', icon: Clock, tone: 'blue' },
    { label: 'Database Health', value: 'OFFLINE', description: 'Connection failed', icon: Database, tone: 'red' },
    { label: 'CPU Load', value: 'N/A', description: 'Monitoring disabled', icon: Cpu, tone: 'gray' },
    { label: 'Rule Success Rate', value: 'N/A', description: 'Service unavailable', icon: Zap, tone: 'gray' },
  ];

  
  const loadingItems = [
    { label: 'Uptime', value: '—', icon: Activity },
    { label: 'DB Resp. Time', value: '—', icon: Database },
    { label: 'CPU Load', value: '—', icon: Cpu },
    { label: 'Rule Success', value: '—', icon: Zap },
  ];

  if (mode === 'offline') {
    return (
      <div className="space-y-6">
        <div className={`rounded-2xl p-6 border transition-all duration-300 ${
          isDark 
            ? 'bg-gradient-to-r from-red-500/20 to-orange-500/20 border-red-500/30 shadow-lg shadow-red-500/10'
            : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-200/50 shadow-md'
        }`}>
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${
              isDark 
                ? 'bg-red-500/30 border border-red-400/30'
                : 'bg-red-500 shadow-md'
            }`}>
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`text-lg font-semibold ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                Backend Services Offline
              </h3>
              <p className={`text-sm ${isDark ? 'text-red-400/80' : 'text-red-600/80'}`}>
                Displaying cached metrics. Start the backend to view live data.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {offlineStats.map((stat, index) => (
            <div
              key={stat.label}
              className={`group relative overflow-hidden rounded-2xl p-6 transition-all duration-500 border ${
                stat.tone === 'red'
                  ? isDark
                    ? 'bg-gradient-to-br from-red-500/20 to-red-600/20 border-red-500/30 shadow-lg shadow-red-500/10'
                    : 'bg-gradient-to-br from-red-50 to-red-100/50 border-red-200/50 shadow-md'
                  : stat.tone === 'blue'
                  ? isDark
                    ? 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border-blue-500/30 shadow-lg shadow-blue-500/10'
                    : 'bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200/50 shadow-md'
                  : isDark
                  ? 'bg-gradient-to-br from-slate-500/20 to-slate-600/20 border-slate-500/30 shadow-lg shadow-slate-500/10'
                  : 'bg-gradient-to-br from-slate-50 to-slate-100/50 border-slate-200/50 shadow-md'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className={`text-sm font-semibold ${
                    stat.tone === 'red'
                      ? isDark ? 'text-red-300' : 'text-red-700'
                      : stat.tone === 'blue'
                      ? isDark ? 'text-blue-300' : 'text-blue-700'
                      : isDark ? 'text-slate-300' : 'text-slate-700'
                  }`}>
                    {stat.label}
                  </h3>
                  <div className={`rounded-xl p-2.5 ${
                    stat.tone === 'red'
                      ? isDark
                        ? 'bg-gradient-to-br from-red-500/40 to-red-600/40'
                        : 'bg-gradient-to-br from-red-500 to-red-600'
                      : stat.tone === 'blue'
                      ? isDark
                        ? 'bg-gradient-to-br from-blue-500/40 to-blue-600/40'
                        : 'bg-gradient-to-br from-blue-500 to-blue-600'
                      : isDark
                      ? 'bg-gradient-to-br from-slate-500/40 to-slate-600/40'
                      : 'bg-gradient-to-br from-slate-500 to-slate-600'
                  }`}>
                    <stat.icon className="h-5 w-5 text-white" />
                  </div>
                </div>
                <p className={`text-2xl font-bold ${
                  stat.tone === 'red'
                    ? isDark ? 'text-red-100' : 'text-red-900'
                    : stat.tone === 'blue'
                    ? isDark ? 'text-blue-100' : 'text-blue-900'
                    : isDark ? 'text-slate-100' : 'text-slate-900'
                }`}>
                  {stat.value}
                </p>
                <p className={`text-sm ${
                  stat.tone === 'red'
                    ? isDark ? 'text-red-400/80' : 'text-red-600/80'
                    : stat.tone === 'blue'
                    ? isDark ? 'text-blue-400/80' : 'text-blue-600/80'
                    : isDark ? 'text-slate-400/80' : 'text-slate-600/80'
                }`}>
                  {stat.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className={`rounded-xl p-4 border transition-all duration-300 ${
          isDark 
            ? 'bg-slate-800/40 border-slate-700/50 text-slate-300'
            : 'bg-slate-100/60 border-slate-200/50 text-slate-600'
        }`}>
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5" />
            <div>
              <p className="text-sm font-medium">Offline Mode Active</p>
              <p className="text-xs opacity-80">
                Last successful connection: Never • Cached entries: 0 • 
                <span className="ml-1 font-medium">Start backend services to restore live monitoring</span>
              </p>
            </div>
          </div>
        </div>

        <div className={`rounded-xl p-6 border transition-all duration-300 ${
          isDark 
            ? 'bg-gradient-to-br from-slate-800/60 to-slate-900/40 border-slate-700/50 shadow-lg shadow-black/20'
            : 'bg-gradient-to-br from-white/90 to-slate-50/80 border-slate-200/50 shadow-md'
        }`}>
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className={`h-5 w-5 ${isDark ? 'text-slate-300' : 'text-slate-600'}`} />
            <h3 className={`text-lg font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
              Historical Performance Summary
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg ${
              isDark ? 'bg-slate-700/30' : 'bg-slate-100/60'
            }`}>
              <p className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                Avg. Uptime (30d)
              </p>
              <p className={`text-xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                N/A
              </p>
              <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                No historical data
              </p>
            </div>
            <div className={`p-4 rounded-lg ${
              isDark ? 'bg-slate-700/30' : 'bg-slate-100/60'
            }`}>
              <p className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                Peak Performance
              </p>
              <p className={`text-xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                N/A
              </p>
              <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Service offline
              </p>
            </div>
            <div className={`p-4 rounded-lg ${
              isDark ? 'bg-slate-700/30' : 'bg-slate-100/60'
            }`}>
              <p className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                Total Requests
              </p>
              <p className={`text-xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                0
              </p>
              <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Backend required
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4" aria-hidden="true">
      {loadingItems.map(i => (
        <div key={i.label} className="rounded-xl border border-border/60 bg-white/70 p-4 shadow-sm dark:bg-slate-900/60 animate-pulse">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary dark:text-slate-400">
            <i.icon className="h-3.5 w-3.5 opacity-70" /> {i.label}
          </div>
          <div className="mt-2 h-6 w-16 rounded bg-accent-100/70 dark:bg-accent/30" />
        </div>
      ))}
    </div>
  );
}
