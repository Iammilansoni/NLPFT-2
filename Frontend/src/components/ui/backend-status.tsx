"use client";

import { useTheme } from "next-themes";
import { Wifi, WifiOff, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";

interface BackendStatusProps {
  className?: string;
  showText?: boolean;
}

export function BackendStatus({ className = "", showText = true }: BackendStatusProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const [isOnline, setIsOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' + '/api/v1/health', {
          method: 'GET',
          signal: AbortSignal.timeout(5000),
        });
        setIsOnline(response.ok);
        setError(false);
      } catch (err) {
        setIsOnline(false);
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusInfo = () => {
    if (isLoading) {
      return {
        icon: AlertCircle,
        text: "Checking...",
        color: isDark ? "text-amber-300" : "text-amber-600",
        bgColor: isDark ? "bg-amber-500/20" : "bg-amber-50",
        borderColor: isDark ? "border-amber-500/30" : "border-amber-200",
      };
    }

    if (error || !isOnline) {
      return {
        icon: WifiOff,
        text: "Backend Offline",
        color: isDark ? "text-red-300" : "text-red-600",
        bgColor: isDark ? "bg-red-500/20" : "bg-red-50",
        borderColor: isDark ? "border-red-500/30" : "border-red-200",
      };
    }

    return {
      icon: Wifi,
      text: "Backend Online",
      color: isDark ? "text-emerald-300" : "text-emerald-600",
      bgColor: isDark ? "bg-emerald-500/20" : "bg-emerald-50",
      borderColor: isDark ? "border-emerald-500/30" : "border-emerald-200",
    };
  };

  const status = getStatusInfo();
  const Icon = status.icon;

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-300 ${status.color} ${status.bgColor} ${status.borderColor} ${className}`}
      title={`Backend Status: ${status.text}`}
    >
      <Icon className="h-3 w-3" />
      {showText && <span>{status.text}</span>}
    </div>
  );
}
