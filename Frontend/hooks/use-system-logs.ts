import { useState, useEffect, useRef, useCallback } from 'react';
import { getApiBase, getWsUrl } from '../lib/runtime-config';

export type LogCategory = 'info' | 'warning' | 'error' | 'success';
export type LogSeverity = 'normal' | 'high' | 'critical';
export type ActivityType = 'llm' | 'dataset' | 'template' | 'embedding' | 'auth' | 'system' | 'api';

export interface LogEntry {
    timestamp: string;
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
    message: string;
    logger: string;
    module: string;
    line: number;
    is_system?: boolean;
    // Enhanced fields for user-friendly display
    humanMessage?: string;
    category?: LogCategory;
    severity?: LogSeverity;
    activityType?: ActivityType;
    isExpanded?: boolean;
    isNoise?: boolean; // Hidden from default view
}

const RAW_API_BASE = getApiBase();
const WS_BASE_URL = getWsUrl();

// Patterns to detect activity types from log messages
function detectActivityType(message: string): ActivityType {
    const msg = message.toLowerCase();
    if (msg.includes('huggingface') || msg.includes('gemini') || msg.includes('ollama') ||
        msg.includes('llm') || msg.includes('provider') || msg.includes('🤖')) return 'llm';
    if (msg.includes('dataset') || msg.includes('generation') || msg.includes('batch') ||
        msg.includes('test case')) return 'dataset';
    if (msg.includes('template') || msg.includes('approved') || msg.includes('rejected')) return 'template';
    if (msg.includes('embedding') || msg.includes('vector') || msg.includes('redis')) return 'embedding';
    if (msg.includes('auth') || msg.includes('token') || msg.includes('login') ||
        msg.includes('websocket')) return 'auth';
    if (msg.includes('/api/')) return 'api';
    return 'system';
}

// Patterns to identify noise logs that should be hidden by default
function isNoiseLog(message: string): boolean {
    const msg = message.toLowerCase();
    // Health checks and routine polling
    if (msg.includes('/health') || msg.includes('health →')) return true;
    // Static asset requests
    if (msg.includes('.js') || msg.includes('.css') || msg.includes('.ico')) return true;
    // Frequent polling endpoints
    if (msg.includes('/datasets/tasks') && msg.includes('→ 200')) return true;
    if (msg.includes('/telemetry/metrics') && msg.includes('→ 200')) return true;
    // OPTIONS preflight requests
    if (msg.startsWith('options ')) return true;
    return false;
}

// Generate human-readable message from log
function getHumanMessage(message: string, activityType: ActivityType): string {
    // Already has human-readable prefix
    if (message.startsWith('🤖') || message.startsWith('🔗') || message.startsWith('✅') ||
        message.startsWith('❌') || message.startsWith('📊')) return message;

    // API responses - make more readable
    const apiMatch = message.match(/^(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)\s+→\s+(\d+)/i);
    if (apiMatch) {
        const [, method, path, status] = apiMatch;
        const statusNum = parseInt(status);
        const endpoint = path.split('/').pop() || path;
        if (statusNum >= 200 && statusNum < 300) {
            return `${endpoint} ${method.toLowerCase()} successful`;
        } else if (statusNum >= 400) {
            return `${endpoint} ${method.toLowerCase()} failed (${status})`;
        }
    }

    return message;
}

// Process incoming log entry 
function processLog(log: LogEntry): LogEntry {
    const activityType = detectActivityType(log.message);
    const isNoise = isNoiseLog(log.message);
    const humanMessage = log.humanMessage || getHumanMessage(log.message, activityType);

    return {
        ...log,
        activityType,
        isNoise,
        humanMessage,
    };
}

export function useSystemLogs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [filter, setFilter] = useState<LogCategory | 'all'>('all');
    const [showNoise, setShowNoise] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Filter logs by category and noise
    const filteredLogs = logs.filter(log => {
        // Filter out noise unless showNoise is enabled
        if (!showNoise && log.isNoise) return false;
        // Filter by category
        if (filter !== 'all' && log.category !== filter) return false;
        return true;
    });

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
                    const rawLog: LogEntry = JSON.parse(event.data);
                    const processedLog = processLog(rawLog);
                    setLogs((prev) => [processedLog, ...prev].slice(0, 1000)); // Keep last 1000 logs, newest first
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
        showNoise,
        setShowNoise,
        clearLogs,
        togglePause,
        toggleExpanded,
    };
}
