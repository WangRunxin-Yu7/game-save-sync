"""
简单轮询型目录监控
- 不依赖第三方库，跨平台
- 回调签名：callback(root: str, created: list[str], modified: list[str], deleted: list[str])
"""
from pathlib import Path
from typing import Callable, Dict, List, Optional, Iterable
import threading
import time
from log_util import log
from .watcher_helpers import build_snapshot, compare_snapshots, SnapshotEntry


class Watcher:
    """
    目录监听器
    - 支持多个目录
    - 提供 start/pause/resume/release 与 add/remove 目录
    """
    def __init__(self, roots: Iterable[str | Path], callback: Callable[[str, List[str], List[str], List[str]], None], interval_ms: int = 1000):
        self._roots: Dict[str, Path] = {}
        for r in roots:
            rp = Path(r).resolve()
            self._roots[rp.as_posix()] = rp
        self._snapshots: Dict[str, Dict[str, SnapshotEntry]] = {}
        self._callback = callback
        self._interval = max(100, int(interval_ms))
        self._lock = threading.Lock()
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        log("watcher_create: roots={n} interval_ms={ms}", n=len(self._roots), ms=self._interval)

    def start(self):
        """
        启动监听线程
        """
        with self._lock:
            if self._running:
                return
            self._running = True
            self._paused = False
            # 初始化快照
            for key, root in self._roots.items():
                self._snapshots[key] = build_snapshot(root)
            self._thread = threading.Thread(target=self._run, name="WatcherThread", daemon=True)
            self._thread.start()
            log("watcher_start: roots={n}", n=len(self._roots))

    def pause(self):
        """
        暂停事件处理（线程保持运行）
        """
        with self._lock:
            self._paused = True
            log("watcher_pause")

    def resume(self):
        """
        恢复事件处理
        """
        with self._lock:
            self._paused = False
            log("watcher_resume")

    def release(self):
        """
        停止并释放资源
        """
        with self._lock:
            self._running = False
            self._paused = False
        # 等待线程退出
        if self._thread is not None:
            self._thread.join(timeout=self._interval / 1000 + 1)
        log("watcher_release")

    def add_path(self, path: str | Path):
        rp = Path(path).resolve()
        key = rp.as_posix()
        with self._lock:
            if key in self._roots:
                log("watcher_add_exist: {path}", path=key)
                return
            self._roots[key] = rp
            self._snapshots[key] = build_snapshot(rp)
            log("watcher_add_path: {path}", path=key)

    def remove_path(self, path: str | Path):
        rp = Path(path).resolve()
        key = rp.as_posix()
        with self._lock:
            if key not in self._roots:
                log("watcher_remove_missing: {path}", path=key)
                return
            self._roots.pop(key, None)
            self._snapshots.pop(key, None)
            log("watcher_remove_path: {path}", path=key)

    def _run(self):
        while True:
            with self._lock:
                if not self._running:
                    break
                paused = self._paused
                roots_items = list(self._roots.items())
            if not paused:
                for key, root in roots_items:
                    try:
                        new_snap = build_snapshot(root)
                        old_snap = self._snapshots.get(key, {})
                        created, modified, deleted = compare_snapshots(old_snap, new_snap)
                        if created or modified or deleted:
                            log("watcher_event: root={root} created={c} modified={m} deleted={d}", root=key, c=len(created), m=len(modified), d=len(deleted))
                            # 调用外部回调
                            try:
                                self._callback(key, created, modified, deleted)
                            except Exception as e:
                                log("watcher_callback_error: {err}", err=str(e))
                        self._snapshots[key] = new_snap
                    except Exception as e:
                        log("watcher_scan_error: root={root} err={err}", root=key, err=str(e))
            time.sleep(self._interval / 1000.0)
