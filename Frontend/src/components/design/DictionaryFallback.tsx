"use client";

import { useTheme } from "next-themes";
import { 
  Library, 
  Database, 
  AlertCircle, 
  FileText, 
  Code, 
  Zap,
  Plus,
  Download,
  Upload,
  Search
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DictionaryFallback() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const offlineStats = [
    { 
      label: 'Total Functions', 
      value: '0', 
      description: 'Backend required',
      icon: Library,
      tone: 'gray' as const
    },
    { 
      label: 'Categories', 
      value: 'N/A', 
      description: 'Service offline',
      icon: Code,
      tone: 'gray' as const
    },
    { 
      label: 'Success Rate', 
      value: 'N/A', 
      description: 'Monitoring disabled',
      icon: Zap,
      tone: 'gray' as const
    },
    { 
      label: 'Last Updated', 
      value: 'Unknown', 
      description: 'Connection failed',
      icon: FileText,
      tone: 'red' as const
    },
  ];

  const disabledActions = [
    { label: 'Create Function', icon: Plus },
    { label: 'Search Functions', icon: Search },
    { label: 'Export Dictionary', icon: Download },
    { label: 'Import Functions', icon: Upload },
  ];

  return (
    <div className="space-y-8">
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
            <Database className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${isDark ? 'text-red-300' : 'text-red-700'}`}>
              Dictionary Service Unavailable
            </h3>
            <p className={`text-sm ${isDark ? 'text-red-400/80' : 'text-red-600/80'}`}>
              Cannot load function dictionary. Start the backend to manage functions.
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
                    : isDark ? 'text-slate-300' : 'text-slate-700'
                }`}>
                  {stat.label}
                </h3>
                <div className={`rounded-xl p-2.5 ${
                  stat.tone === 'red'
                    ? isDark
                      ? 'bg-gradient-to-br from-red-500/40 to-red-600/40'
                      : 'bg-gradient-to-br from-red-500 to-red-600'
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
                  : isDark ? 'text-slate-100' : 'text-slate-900'
              }`}>
                {stat.value}
              </p>
              <p className={`text-sm ${
                stat.tone === 'red'
                  ? isDark ? 'text-red-400/80' : 'text-red-600/80'
                  : isDark ? 'text-slate-400/80' : 'text-slate-600/80'
              }`}>
                {stat.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      <Card className={`overflow-hidden transition-all duration-500 ${
        isDark
          ? 'border-slate-700/30 bg-gradient-to-br from-slate-900/60 to-slate-800/40 shadow-2xl shadow-black/30 backdrop-blur-xl'
          : 'border-slate-200/40 bg-gradient-to-br from-white/90 to-slate-50/80 shadow-xl shadow-slate-900/10 backdrop-blur-sm'
      }`}>
        <CardHeader className={`border-b transition-all duration-300 ${
          isDark
            ? 'border-slate-700/40 bg-gradient-to-r from-slate-800/50 to-slate-900/50'
            : 'border-slate-200/40 bg-gradient-to-r from-slate-50/60 to-blue-50/30'
        }`}>
          <CardTitle className={`flex items-center gap-4 text-xl font-bold ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            <div className={`rounded-xl p-2.5 ${
              isDark
                ? 'bg-gradient-to-br from-amber-500/40 to-orange-600/40 shadow-lg shadow-amber-500/30 border border-amber-400/30'
                : 'bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-amber-500/30'
            }`}>
              <AlertCircle className="h-6 w-6 text-white" />
            </div>
            <div>
              <span>Dictionary Actions Unavailable</span>
              <div className={`text-sm font-normal mt-1 ${
                isDark ? 'text-slate-400' : 'text-slate-600'
              }`}>
                Backend connection required
              </div>
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {disabledActions.map((action, index) => (
              <Button
                key={action.label}
                variant="outline"
                disabled
                className={`flex items-center gap-3 p-4 h-auto justify-start transition-all duration-300 ${
                  isDark
                    ? 'border-slate-600/50 bg-slate-800/30 text-slate-400 hover:bg-slate-800/30'
                    : 'border-slate-300/50 bg-slate-100/30 text-slate-500 hover:bg-slate-100/30'
                }`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <action.icon className="h-5 w-5" />
                <div className="text-left">
                  <div className="font-medium">{action.label}</div>
                  <div className="text-xs opacity-70">Requires backend</div>
                </div>
              </Button>
            ))}
          </div>

          <div className={`mt-6 p-4 rounded-lg border ${
            isDark 
              ? 'bg-slate-800/40 border-slate-700/50 text-slate-300'
              : 'bg-slate-100/60 border-slate-200/50 text-slate-600'
          }`}>
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5" />
              <div>
                <p className="text-sm font-medium">Offline Mode - No Functions Available</p>
                <p className="text-xs opacity-80">
                  Start the backend service to create, edit, and manage function definitions. 
                  All dictionary operations require an active database connection.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className={`overflow-hidden transition-all duration-500 ${
        isDark
          ? 'border-blue-700/30 bg-gradient-to-br from-blue-900/20 to-indigo-800/20 shadow-lg shadow-blue-500/10'
          : 'border-blue-200/40 bg-gradient-to-br from-blue-50/80 to-indigo-50/60 shadow-md'
      }`}>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className={`rounded-xl p-2.5 ${
              isDark
                ? 'bg-gradient-to-br from-blue-500/40 to-indigo-600/40'
                : 'bg-gradient-to-br from-blue-500 to-indigo-600'
            }`}>
              <Library className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`text-lg font-semibold mb-2 ${
                isDark ? 'text-blue-300' : 'text-blue-700'
              }`}>
                How to Restore Dictionary Functionality
              </h3>
              <div className={`space-y-2 text-sm ${
                isDark ? 'text-blue-400/90' : 'text-blue-600/90'
              }`}>
                <p>1. <strong>Start the Backend:</strong> Run the NLPForge API server</p>
                <p>2. <strong>Verify Database:</strong> Ensure MongoDB is running and accessible</p>
                <p>3. <strong>Refresh Page:</strong> The dictionary will automatically load when services are available</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
