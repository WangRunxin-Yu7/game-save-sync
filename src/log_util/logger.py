"""
日志记录器类
"""
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional


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
        使用文件名排序（日期格式可排序）
        """
        files = sorted(self.log_dir.glob("*.log"), key=lambda p: p.name, reverse=True)
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
