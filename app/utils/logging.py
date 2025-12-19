"""
Structured logging utility for Labor Market RAG
"""
import logging
import sys
from datetime import datetime
from typing import Optional
import streamlit as st


class RAGLogger:
    """Centralized logging for the RAG system"""
    
    def __init__(self, name: str = "LaborRAG", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Store logs for UI display
        if 'system_logs' not in st.session_state:
            st.session_state.system_logs = []
    
    def info(self, message: str, show_ui: bool = False):
        """Log info message"""
        self.logger.info(message)
        self._add_to_ui_logs('INFO', message, show_ui)
    
    def warning(self, message: str, show_ui: bool = False):
        """Log warning message"""
        self.logger.warning(message)
        self._add_to_ui_logs('WARNING', message, show_ui)
    
    def error(self, message: str, show_ui: bool = False):
        """Log error message"""
        self.logger.error(message)
        self._add_to_ui_logs('ERROR', message, show_ui)
    
    def debug(self, message: str, show_ui: bool = False):
        """Log debug message"""
        self.logger.debug(message)
        self._add_to_ui_logs('DEBUG', message, show_ui)
    
    def _add_to_ui_logs(self, level: str, message: str, show_ui: bool):
        """Add log entry to session state for UI display"""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message
        }
        st.session_state.system_logs.append(log_entry)
        
        # Keep only last 100 logs
        if len(st.session_state.system_logs) > 100:
            st.session_state.system_logs = st.session_state.system_logs[-100:]
        
        if show_ui:
            if level == 'ERROR':
                st.error(f"🚨 {message}")
            elif level == 'WARNING':
                st.warning(f"⚠️ {message}")
            elif level == 'INFO':
                st.info(f"ℹ️ {message}")
    
    def get_ui_logs(self, level: Optional[str] = None) -> list:
        """Get logs for UI display, optionally filtered by level"""
        logs = st.session_state.get('system_logs', [])
        if level:
            return [log for log in logs if log['level'] == level]
        return logs
    
    def clear_ui_logs(self):
        """Clear UI logs"""
        st.session_state.system_logs = []
        self.info("Logs cleared")


# Global logger instance
logger = RAGLogger()
