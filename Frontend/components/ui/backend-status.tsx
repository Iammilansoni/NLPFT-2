"use client";

import { useTheme } from "next-themes";
import { getApiBase } from '@/lib/runtime-config';
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface BackendStatusProps {
  className?: string;
  showText?: boolean;
  variant?: 'default' | 'minimal' | 'detailed';
}

export function BackendStatus({ className = "", showText = true, variant = 'default' }: BackendStatusProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const [isOnline, setIsOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      const startTime = performance.now();
      try {
        setIsLoading(true);
        const RAW_API_BASE = getApiBase();
        const apiUrl = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : '';
        const response = await fetch(`${apiUrl}/api/v1/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000),
        });
        const endTime = performance.now();
        setLatency(Math.round(endTime - startTime));
        setIsOnline(response.ok);
        setError(false);
      } catch (err) {
        setIsOnline(false);
        setError(true);
        setLatency(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusConfig = () => {
    if (isLoading) {
      return {
        icon: Loader2,
        text: "Connecting...",
        dotColor: "bg-info",
        borderColor: "border-info/30",
        bgColor: "bg-info/10",
        textColor: "text-info dark:text-info",
        animate: true
      };
    }

    if (error || !isOnline) {
      return {
        icon: WifiOff,
        text: "Offline",
        dotColor: "bg-destructive",
        borderColor: "border-destructive/30",
        bgColor: "bg-destructive/10",
        textColor: "text-destructive dark:text-destructive",
        animate: false
      };
    }

    return {
      icon: Wifi,
      text: "Online",
      dotColor: "bg-success",
      borderColor: "border-success/30",
      bgColor: "bg-success/10",
      textColor: "text-success dark:text-success",
      animate: false
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  if (variant === 'minimal') {
    return (
      <div className={cn("relative", className)} title={`Backend: ${config.text}`}>
        <span className={cn(
          "flex h-2 w-2 rounded-full",
          config.dotColor
        )} />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium",
        "border",
        config.borderColor,
        config.bgColor,
        className
      )}
    >
      {/* Status Dot */}
      <span className={cn(
        "inline-flex rounded-full h-1.5 w-1.5",
        config.dotColor
      )} />

      {/* Icon */}
      <Icon className={cn(
        "h-3 w-3",
        config.textColor,
        config.animate && "animate-spin"
      )} />

      {/* Text */}
      {showText && (
        <span className={cn("font-medium", config.textColor)}>
          {config.text}
        </span>
      )}

      {/* Latency (for detailed variant) */}
      {variant === 'detailed' && isOnline && latency !== null && (
        <span className="text-muted-foreground text-[10px] tabular-nums">
          {latency}ms
        </span>
      )}
    </div>
  );
}
