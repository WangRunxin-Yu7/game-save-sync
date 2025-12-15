"""
监控器工厂函数
"""
from pathlib import Path
from typing import Callable, List, Iterable
from .watcher import Watcher


def create_watcher(paths: Iterable[str | Path], callback: Callable[[str, List[str], List[str], List[str]], None], interval_ms: int = 1000) -> Watcher:
    """
    创建 watcher 并返回
    - paths: 初始监控目录（可为空列表）
    - callback: 当目录变化时的回调，传入 root 与三类变更
    - interval_ms: 轮询间隔
    """
    return Watcher(paths, callback, interval_ms=interval_ms)
