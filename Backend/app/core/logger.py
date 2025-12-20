"""Logging configuration for NLPForge."""

import logging
import sys
from typing import Any, Dict


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "nlpforge", level: str = "INFO") -> logging.Logger:
    """Set up and configure logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

    # WebSocket Handler (System Logs)
    try:
        from app.core.log_manager import log_manager
        
        class WebSocketHandler(logging.Handler):
            def emit(self, record):
                # Filter out noisy logs (keep INFO and above)
                if record.levelno < logging.INFO:
                    return
                
                # Prevent recursion if log_manager logs something
                if "app.core.log_manager" in record.name:
                    return

                log_manager.handle_log(record)
                
        ws_handler = WebSocketHandler()
        ws_handler.setLevel(logging.INFO)
        logger.addHandler(ws_handler)
    except ImportError:
        pass # Handle case where log_manager might not be ready during initial setup if circular deps exist

    return logger


def log_request(method: str, url: str, status_code: int, duration: float) -> None:
    """Log HTTP request information."""
    logger.info(f"HTTP {method} {url} -> {status_code} ({duration:.3f}s)")


def log_health_check(status: str, checks: Dict[str, Any]) -> None:
    """Log health check results."""
    status_label = "[OK]" if status == "healthy" else "[DEGRADED]" if status == "degraded" else "[UNHEALTHY]"
    logger.info(f"{status_label} Health Check -> {status} | {checks}")


def log_error(error: Exception, context: str = "") -> None:
    """Log error with context."""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"Error: {str(error)}{context_str}", exc_info=True)


def log_startup(component: str) -> None:
    """Log component startup."""
    logger.info(f"Starting {component}...")


def log_shutdown(component: str) -> None:
    """Log component shutdown."""
    logger.info(f"Shutting down {component}...")


# Global logger instance
logger = setup_logger()