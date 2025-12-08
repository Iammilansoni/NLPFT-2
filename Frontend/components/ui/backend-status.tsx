"use client";

import { useTheme } from "next-themes";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

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
        bgGradient: "from-blue-500/20 via-blue-500/10 to-transparent",
        borderColor: "border-blue-500/30",
        textColor: "text-blue-600 dark:text-blue-400",
        animate: true
      };
    }

    if (error || !isOnline) {
      return {
        icon: WifiOff,
        text: "Offline",
        dotColor: "bg-red-500",
        bgGradient: "from-red-500/20 via-red-500/10 to-transparent",
        borderColor: "border-red-500/30",
        textColor: "text-red-600 dark:text-red-400",
        animate: false
      };
    }

    return {
      icon: Wifi,
      text: "Online",
      dotColor: "bg-emerald-500",
      bgGradient: "from-emerald-500/20 via-emerald-500/10 to-transparent",
      borderColor: "border-emerald-500/30",
      textColor: "text-emerald-600 dark:text-emerald-400",
      animate: false
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  if (variant === 'minimal') {
    return (
      <div className={cn("relative", className)} title={`Backend: ${config.text}`}>
        <span className={cn(
          "flex h-2.5 w-2.5 rounded-full",
          config.dotColor
        )}>
          {isOnline && (
            <span className={cn(
              "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
              config.dotColor
            )} />
          )}
        </span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "relative inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
        "border backdrop-blur-sm transition-all duration-300",
        config.borderColor,
        `bg-gradient-to-r ${config.bgGradient}`,
        className
      )}
    >
      {/* Animated Status Dot */}
      <span className="relative flex h-2 w-2">
        <span className={cn(
          "relative inline-flex rounded-full h-2 w-2",
          config.dotColor
        )} />
        {(isOnline || isLoading) && (
          <span className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75",
            isLoading ? "animate-ping" : "animate-pulse",
            config.dotColor
          )} />
        )}
      </span>

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
        <span className="text-muted-foreground text-[10px] ml-1">
          {latency}ms
        </span>
      )}
    </motion.div>
  );
}
