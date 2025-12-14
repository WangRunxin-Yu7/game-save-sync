"""
日志工具实现
- 自动初始化：读取日志配置，创建目录，并清理多余日志文件
- 简单接口：log(template, **kwargs) 使用 str.format 写入一条日志
- 每条日志包含时间戳与格式化内容
"""
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional
from config_util import get_logging

_LOGGER = None
_LOCK = threading.Lock()

class Logger:
    """
    简易文件日志器（按日写入）
    """
    def __init__(self, log_dir: str, max_logs: int):
        self.log_dir = Path(log_dir).resolve()
        self.max_logs = max_logs
        self._write_lock = threading.Lock()
        self._current_path: Optional[Path] = None
        self._ensure_dir()
        self._cleanup_excess_logs()

    def _ensure_dir(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _daily_file(self) -> Path:
        """
        以当日日期命名日志文件
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{date_str}.log"

    def _rotate_if_needed(self):
        target = self._daily_file()
        if self._current_path != target:
            self._current_path = target

    def _cleanup_excess_logs(self):
        """
        清理多余日志文件，保留最新的 max_logs 个 .log 文件
        """
        files = sorted(self.log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if self.max_logs is None or self.max_logs <= 0:
            return
        for p in files[self.max_logs:]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

    def write(self, message: str):
        """
        写入一行日志，含时间戳
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} {message}\n"
        with self._write_lock:
            self._rotate_if_needed()
            path = self._current_path or self._daily_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line)

def _init():
    global _LOGGER
    with _LOCK:
        if _LOGGER is None:
            cfg = get_logging()
            _LOGGER = Logger(log_dir=cfg.get("log_dir", "./logs"), max_logs=cfg.get("max_logs", 1000))

def reload_logger():
    """
    重新加载日志配置并重建日志器（下次写入按新配置）
    """
    global _LOGGER
    with _LOCK:
        cfg = get_logging()
        _LOGGER = Logger(log_dir=cfg.get("log_dir", "./logs"), max_logs=cfg.get("max_logs", 1000))

def _ensure():
    if _LOGGER is None:
        _init()

def log(template: str, **kwargs):
    """
    简单外部接口：
    - 传入字符串与参数，按 str.format(**kwargs) 格式化
    - 写入一条包含时间戳的日志
    """
    _ensure()
    msg = template
    if kwargs:
        try:
            msg = template.format(**kwargs)
        except Exception:
            # 若格式化失败，附加原始参数
            msg = f"{template} | {kwargs}"
    _LOGGER.write(msg)

