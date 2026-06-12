"""终态 SQLite 数据层。"""

from .connection import DB_PATH, get_connection, init_db
from .app_state import get_active_save_key, set_active_save_key

__all__ = [
    "DB_PATH",
    "get_connection",
    "init_db",
    "get_active_save_key",
    "set_active_save_key",
]
