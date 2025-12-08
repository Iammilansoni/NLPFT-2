import asyncio
from typing import List, Dict, Any
import logging
import re
from datetime import datetime
from app.core.context_vars import user_id_ctx

class LogManager:
    def __init__(self):
        # Map user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[Any]] = {}

        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

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
        # If no target user, we don't broadcast (strict privacy)
        # Unless it's a global system admin channel (not implemented yet)
        if not target_user_id:
            return

        if target_user_id not in self.active_connections:
            return
            
        message = log_entry
        
        to_remove = []
        for connection in self.active_connections[target_user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                to_remove.append(connection)
        
        for connection in to_remove:
            self.disconnect(connection, target_user_id)

    def handle_log(self, record: logging.LogRecord):
        # 1. Get User ID from Context
        current_user_id = user_id_ctx.get()
        
        # If no user context, check if it was explicitly passed in extra
        if not current_user_id and hasattr(record, 'user_id'):
            current_user_id = str(record.user_id)
            
        # If still no user, we can't route this log to a specific user
        if not current_user_id:
            return

        # 2. Format the log record
        # Strip ANSI codes from message
        clean_message = self.ansi_escape.sub('', record.getMessage())
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": clean_message,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno
        }
        
        # 3. Broadcast
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.broadcast_log(log_entry, current_user_id))
        except RuntimeError:
            pass

# Global instance
log_manager = LogManager()
