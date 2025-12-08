import { useState, useEffect, useRef, useCallback } from 'react';

export interface LogEntry {
    timestamp: string;
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
    message: string;
    logger: string;
    module: string;
    line: number;
}

const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');

export function useSystemLogs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        // Get token from localStorage
        const token = typeof window !== 'undefined' ? localStorage.getItem('nlpforge_access_token') : null;

        if (!token) {
            console.log('❌ No token found, skipping system logs connection');
            return;
        }

        const ws = new WebSocket(`${WS_BASE_URL}/ws/system-logs?token=${token}`);

        ws.onopen = () => {
            setIsConnected(true);
            console.log('✅ System Logs Connected');
        };

        ws.onclose = () => {
            setIsConnected(false);
            console.log('❌ System Logs Disconnected');
            // Reconnect after 3 seconds
            setTimeout(connect, 3000);
        };

        ws.onmessage = (event) => {
            if (isPaused) return;
            try {
                const log = JSON.parse(event.data);
                setLogs((prev) => [log, ...prev].slice(0, 1000)); // Keep last 1000 logs
            } catch (e) {
                console.error('Failed to parse log message:', e);
            }
        };

        wsRef.current = ws;
    }, [isPaused]);

    useEffect(() => {
        connect();
        return () => {
            wsRef.current?.close();
        };
    }, [connect]);

    const clearLogs = () => setLogs([]);
    const togglePause = () => setIsPaused(!isPaused);

    return {
        logs,
        isConnected,
        isPaused,
        clearLogs,
        togglePause,
    };
}
