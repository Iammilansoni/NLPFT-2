import { useState, useEffect, useRef, useCallback } from 'react';

export type LogCategory = 'info' | 'warning' | 'error' | 'success';
export type LogSeverity = 'normal' | 'high' | 'critical';

export interface LogEntry {
    timestamp: string;
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
    message: string;
    logger: string;
    module: string;
    line: number;
    is_system?: boolean;
    // New fields for user-friendly display
    humanMessage?: string;
    category?: LogCategory;
    severity?: LogSeverity;
    isExpanded?: boolean;
}

const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');

export function useSystemLogs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [filter, setFilter] = useState<LogCategory | 'all'>('all');
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Filter logs by category
    const filteredLogs = filter === 'all'
        ? logs
        : logs.filter(log => log.category === filter);

    // Toggle expanded state for a log entry
    const toggleExpanded = useCallback((index: number) => {
        setLogs(prev => prev.map((log, i) =>
            i === index ? { ...log, isExpanded: !log.isExpanded } : log
        ));
    }, []);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        // Get token from localStorage
        const token = typeof window !== 'undefined' ? localStorage.getItem('nlpforge_access_token') : null;

        if (!token) {
            console.log('[Logs] No token found, skipping system logs connection');
            return;
        }

        try {
            const ws = new WebSocket(`${WS_BASE_URL}/ws/system-logs?token=${token}`);

            ws.onopen = () => {
                setIsConnected(true);
                console.log('[Logs] System Logs Connected');
                // Add connection log entry
                setLogs((prev) => [{
                    timestamp: new Date().toISOString(),
                    level: 'INFO' as const,
                    message: 'Connected to system logs',
                    humanMessage: 'Connected to activity logs',
                    category: 'success' as LogCategory,
                    severity: 'normal' as LogSeverity,
                    logger: 'frontend',
                    module: 'websocket',
                    line: 0,
                    is_system: true
                }, ...prev].slice(0, 1000));
            };

            ws.onclose = (event) => {
                setIsConnected(false);
                console.log('[Logs] System Logs Disconnected', event.code);
                wsRef.current = null;

                // Clear any existing reconnect timeout
                if (reconnectTimeoutRef.current) {
                    clearTimeout(reconnectTimeoutRef.current);
                }

                // Reconnect after 3 seconds (but not if closed intentionally with code 4001)
                if (event.code !== 4001) {
                    reconnectTimeoutRef.current = setTimeout(connect, 3000);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onmessage = (event) => {
                if (isPaused) return;
                try {
                    const log: LogEntry = JSON.parse(event.data);
                    setLogs((prev) => [log, ...prev].slice(0, 1000)); // Keep last 1000 logs, newest first
                } catch (e) {
                    console.error('Failed to parse log message:', e);
                }
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }, [isPaused]);

    useEffect(() => {
        connect();
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            wsRef.current?.close();
        };
    }, [connect]);

    const clearLogs = () => setLogs([]);
    const togglePause = () => setIsPaused(!isPaused);

    return {
        logs,
        filteredLogs,
        isConnected,
        isPaused,
        filter,
        setFilter,
        clearLogs,
        togglePause,
        toggleExpanded,
    };
}
