"use client";

import { useTheme } from "next-themes";
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
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
        dotColor: "bg-blue-500",
        borderColor: "border-blue-500/30",
        bgColor: "bg-blue-500/10",
        textColor: "text-blue-600 dark:text-blue-400",
        animate: true
      };
    }

    if (error || !isOnline) {
      return {
        icon: WifiOff,
        text: "Offline",
        dotColor: "bg-red-500",
        borderColor: "border-red-500/30",
        bgColor: "bg-red-500/10",
        textColor: "text-red-600 dark:text-red-400",
        animate: false
      };
    }

    return {
      icon: Wifi,
      text: "Online",
      dotColor: "bg-green-500",
      borderColor: "border-green-500/30",
      bgColor: "bg-green-500/10",
      textColor: "text-green-600 dark:text-green-400",
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
