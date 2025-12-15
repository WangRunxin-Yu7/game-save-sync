"""
配置管理器 - 单例模式
"""
from pathlib import Path
import threading
import sys
from .config_loader import ConfigLoader


_CONFIG = None
_LOCK = threading.Lock()


def _detect_config_path() -> Path:
    """
    发现配置文件路径：
    优先读取项目根目录 `config.ini`，否则回退到 `data/config.ini`
    支持 PyInstaller 打包后的路径查找
    """
    # PyInstaller 打包后，使用可执行文件所在目录
    if getattr(sys, 'frozen', False):
        root = Path(sys.executable).parent
    else:
        # 开发模式，使用当前工作目录
        root = Path(".").resolve()
    
    candidates = [root / "config.ini", root / "data" / "config.ini"]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("config.ini not found")


def _init():
    global _CONFIG
    with _LOCK:
        if _CONFIG is None:
            path = _detect_config_path()
            _CONFIG = ConfigLoader(path)


def reload_config():
    global _CONFIG
    with _LOCK:
        path = _detect_config_path()
        _CONFIG = ConfigLoader(path)


def _ensure():
    if _CONFIG is None:
        _init()


def get_value(section: str, key: str, default=None):
    """
    读取任意 section 下的 key，未找到返回 default
    """
    _ensure()
    return _CONFIG.get_value(section, key, default)


def get_general() -> dict:
    """
    获取通用配置（device_id）
    """
    _ensure()
    return _CONFIG.get_general()


def get_git() -> dict:
    """
    获取 Git 相关配置（remote/branch/repository_dir/token）
    """
    _ensure()
    return _CONFIG.get_git()


def get_sync() -> dict:
    """
    获取同步策略配置（poll_interval/debounce/dedup/force_overwrite）
    """
    _ensure()
    return _CONFIG.get_sync()


def get_backup() -> dict:
    """
    获取备份配置（backup_dir/max_backups）
    """
    _ensure()
    return _CONFIG.get_backup()


def get_logging() -> dict:
    """
    获取日志配置（log_dir/max_logs）
    """
    _ensure()
    return _CONFIG.get_logging()


def get_games() -> list:
    """
    获取游戏配置列表（GameEntry）
    """
    _ensure()
    return _CONFIG.get_games()
