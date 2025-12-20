import asyncio
from typing import List, Dict, Any
import logging
import re
from datetime import datetime
from app.core.context_vars import user_id_ctx

# Import activity log service for user-friendly log transformation
try:
    from app.services.activity_log_service import activity_log_service
except ImportError:
    activity_log_service = None

class LogManager:
    def __init__(self):
        # Map user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[Any]] = {}

        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        # System-level loggers that should broadcast to all connected users
        self.system_loggers = {
            "nlpforge",
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "app.main",
            "app.core",
            "app.nlp",
            "app.services",
            "app.api",
            "alembic",
        }

    async def connect(self, websocket: Any, user_id: str):
        # websocket.accept() is handled in main.py before calling this
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: Any, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_log(self, log_entry: Dict[str, Any], target_user_id: str = None):
        """Broadcast log to specific user or all connected users if target is None"""
        if target_user_id:
            # Send to specific user
            if target_user_id not in self.active_connections:
                return
            await self._send_to_connections(log_entry, self.active_connections[target_user_id], target_user_id)
        else:
            # Broadcast to ALL connected users (system logs)
            for user_id, connections in list(self.active_connections.items()):
                await self._send_to_connections(log_entry, connections, user_id)
    
    async def _send_to_connections(self, log_entry: Dict[str, Any], connections: List[Any], user_id: str):
        """Helper to send log to a list of connections"""
        to_remove = []
        for connection in connections:
            try:
                await connection.send_json(log_entry)
            except Exception:
                to_remove.append(connection)
        
        for connection in to_remove:
            self.disconnect(connection, user_id)

    def _is_system_log(self, logger_name: str) -> bool:
        """Check if this log should be broadcast to all users"""
        for sys_logger in self.system_loggers:
            if logger_name.startswith(sys_logger):
                return True
        return False

    def handle_log(self, record: logging.LogRecord):
        # 1. Get User ID from Context
        current_user_id = user_id_ctx.get()
        
        # If no user context, check if it was explicitly passed in extra
        if not current_user_id and hasattr(record, 'user_id'):
            current_user_id = str(record.user_id)
        
        # 2. Determine if this is a system log that should go to all users
        is_system_log = self._is_system_log(record.name)
        
        # If no user and not a system log, skip
        if not current_user_id and not is_system_log:
            return
        
        # If no connections at all, skip
        if not self.active_connections:
            return

        # 3. Format the log record
        # Strip ANSI codes from message
        clean_message = self.ansi_escape.sub('', record.getMessage())
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": clean_message,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "is_system": is_system_log
        }
        
        # 4. Enhance with user-friendly message using ActivityLogService
        if activity_log_service:
            log_entry = activity_log_service.enhance_log_entry(log_entry)
        
        # 5. Broadcast
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # If system log, broadcast to all; otherwise to specific user
                target = None if is_system_log else current_user_id
                loop.create_task(self.broadcast_log(log_entry, target))
        except RuntimeError:
            pass

# Global instance
log_manager = LogManager()
