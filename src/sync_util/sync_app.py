"""
存档同步主流程
- 按项目概述实现：启动备份、拉取、覆盖、推送、定时器、监控器
- 日志通过 log_util 统一输出，静默运行
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime
import threading
import time

from log_util import log
from config_util import get_git, get_backup, get_sync, get_games, get_general
from git_util import create_git, GitRepo
from file_util import ensure_dir
from watcher_util import create_watcher, Watcher
from task_util import create_queue, create_task, enqueue, TaskQueue
from .helpers import copy_preserve_tree, filter_paths_by_patterns, compute_files_hash, get_timestamp


class SyncApp:
    """
    存档同步应用
    - 负责启动阶段流程、定时器、文件监控与任务队列
    """
    def __init__(self, override_remote: str | None = None, override_token: str | None = None, override_username: str | None = None, override_branch: str | None = None):
        self.git_cfg = get_git()
        if override_remote is not None:
            self.git_cfg["remote"] = override_remote
        if override_token is not None:
            self.git_cfg["token"] = override_token
        if override_username is not None:
            self.git_cfg["username"] = override_username
        if override_branch is not None:
            self.git_cfg["branch"] = override_branch
        self.backup_cfg = get_backup()
        self.sync_cfg = get_sync()
        self.general = get_general()
        self.games = get_games()
        self.repo_dir = ensure_dir(self.git_cfg.get("repository_dir", "./repository"))
        self.backup_dir = ensure_dir(self.backup_cfg.get("backup_dir", "./backup"))
        self.git: GitRepo = create_git(
            remote=self.git_cfg.get("remote", ""),
            repo_dir=str(self.repo_dir),
            branch=self.git_cfg.get("branch", "main"),
            token=self.git_cfg.get("token", ""),
            username=self.git_cfg.get("username", ""),
        )
        # 任务队列（唯一任务只保留最新）
        self.q_pull: TaskQueue = create_queue("pull")
        self.q_push: TaskQueue = create_queue("push")
        self.q_apply: TaskQueue = create_queue("apply")
        # 监控器
        self.watcher: Watcher | None = None
        # 定时器线程
        self._timer_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        # 存档文件哈希值缓存（用于判断是否真正变化）
        self._save_files_hash: Dict[str, str] = {}
        log("app_init_done")

    def start(self):
        """
        启动阶段：备份、拉取、覆盖、推送、清理
        """
        log("app_start")
        self._ensure_repository()
        self._backup_local_saves()
        self._enqueue_pull_apply()
        self._enqueue_sync_local_to_repo_and_push()
        self._cleanup_backups()
        self._start_timer()
        self._start_watcher()
        log("app_started")

    def stop(self):
        """
        停止定时器与监控器
        """
        log("app_stop")
        self._stop_event.set()
        if self._timer_thread:
            self._timer_thread.join(timeout=2)
        if self.watcher:
            self.watcher.release()
        log("app_stopped")

    def _ensure_repository(self):
        """
        确保仓库存在并在正确分支
        """
        ok = self.git.ensure_cloned()
        log("repo_ready: ok={ok}", ok=ok)

    def _backup_local_saves(self):
        """
        将本地存档备份到 backup/[timestamp]/[游戏名]/[index]/
        """
        ts_dir = ensure_dir(self.backup_dir / get_timestamp())
        for g in self.games:
            game_root = Path(g.path).resolve()
            if not game_root.exists():
                log("backup_skip_missing_root: {path}", path=str(game_root))
                continue
            files = list(game_root.rglob("*"))
            files = [f for f in files if f.is_file()]
            files = filter_paths_by_patterns(game_root, files, g.allow, g.deny)
            dst_root = ensure_dir(ts_dir / g.name / g.index)
            copy_preserve_tree(files, game_root, dst_root)
            log("backup_game_done: game={name} index={index} count={count}", name=g.name, index=g.index, count=len(files))
        log("backup_done: ts_dir={dir}", dir=str(ts_dir))

    def _apply_repo_to_local(self):
        """
        将 repository 下的存档覆盖到本地（强制覆盖）
        """
        import shutil
        for g in self.games:
            src_root = self.repo_dir / g.name / g.index
            dst_root = Path(g.path).resolve()
            if not src_root.exists():
                log("apply_skip_repo_missing: {path}", path=str(src_root))
                continue
            ensure_dir(dst_root)
            for p in src_root.rglob("*"):
                if p.is_file():
                    rel = p.resolve().relative_to(src_root.resolve())
                    target = dst_root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(p.as_posix(), target.as_posix())
                    except Exception as e:
                        log("apply_copy_error: {src} -> {dst} err={err}", src=str(p), dst=str(target), err=str(e))
            log("apply_game_done: game={name} index={index}", name=g.name, index=g.index)
        log("apply_done")

    def _sync_local_to_repo(self):
        """
        将本地新增或变化的存档复制到 repository 下对应目录
        """
        for g in self.games:
            game_root = Path(g.path).resolve()
            if not game_root.exists():
                log("sync_skip_missing_root: {path}", path=str(game_root))
                continue
            files = [p for p in game_root.rglob("*") if p.is_file()]
            files = filter_paths_by_patterns(game_root, files, g.allow, g.deny)
            dst_root = ensure_dir(self.repo_dir / g.name / g.index)
            copy_preserve_tree(files, game_root, dst_root)
            log("sync_copy_game_done: game={name} index={index} count={count}", name=g.name, index=g.index, count=len(files))

    def _enqueue_pull_apply(self):
        """
        入队拉取与应用任务（唯一任务）
        """
        def do_pull_apply():
            self.git.force_pull()
            self._apply_repo_to_local()
        t = create_task(do_pull_apply, unique=True, insert_mode='tail', key='pull_apply')
        enqueue(self.q_pull, t)

    def _enqueue_sync_local_to_repo_and_push(self):
        """
        入队本地复制到仓库并推送（唯一任务）
        """
        def do_sync_push():
            self._sync_local_to_repo()
            self.git.add(None)
            device = self.general.get("device_id", "") or "device"
            msg = f"sync by {device} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.git.commit(msg)
            self.git.force_push()
        t = create_task(do_sync_push, unique=True, insert_mode='tail', key='sync_push')
        enqueue(self.q_push, t)

    def _cleanup_backups(self):
        """
        清理多余备份，保留最近 max_backups
        """
        max_b = int(self.backup_cfg.get("max_backups", 20))
        items = sorted([p for p in self.backup_dir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        for p in items[max_b:]:
            try:
                for f in p.rglob("*"):
                    if f.is_file():
                        f.unlink()
                for d in sorted([d for d in p.rglob("*") if d.is_dir()], reverse=True):
                    d.rmdir()
                p.rmdir()
                log("backup_cleanup_removed: {path}", path=str(p))
            except Exception as e:
                log("backup_cleanup_error: {path} err={err}", path=str(p), err=str(e))
        log("backup_cleanup_done: kept={kept}", kept=min(len(items), max_b))

    def _start_timer(self):
        """
        定时器：每 poll_interval_minutes 拉取并应用远端变更
        """
        interval_min = int(self.sync_cfg.get("poll_interval_minutes", 15))
        def _timer_loop():
            log("timer_start: interval_min={m}", m=interval_min)
            while not self._stop_event.wait(interval_min * 60):
                self._enqueue_pull_apply()
            log("timer_stop")
        self._timer_thread = threading.Thread(target=_timer_loop, name="SyncTimer", daemon=True)
        self._timer_thread.start()

    def _start_watcher(self):
        """
        监控所有配置的游戏目录；发生变化时检查存档文件是否真正变化，变化才复制到 repository 并推送
        """
        debounce_ms = int(self.sync_cfg.get("debounce_ms", 1500))
        pending = {"changed": False}
        lock = threading.Lock()
        # 路径到配置映射
        path_to_cfg: Dict[str, Tuple[Path, list, list, str, str]] = {}
        for g in self.games:
            root = Path(g.path).resolve()
            path_to_cfg[root.as_posix()] = (root, g.allow, g.deny, g.name, g.index)
            # 初始化哈希值
            if root.exists():
                files = [p for p in root.rglob("*") if p.is_file()]
                files = filter_paths_by_patterns(root, files, g.allow, g.deny)
                self._save_files_hash[root.as_posix()] = compute_files_hash(files)
        
        def _cb(root: str, created: list, modified: list, deleted: list):
            with lock:
                pending["changed"] = True
            log("watch_event_cb: root={root} c={c} m={m} d={d}", root=root, c=len(created), m=len(modified), d=len(deleted))
        
        self.watcher = create_watcher([Path(g.path) for g in self.games], _cb, interval_ms=max(300, debounce_ms))
        self.watcher.start()
        
        def _debounce_loop():
            log("watch_debounce_start: interval_ms={ms}", ms=debounce_ms)
            while not self._stop_event.is_set():
                time.sleep(debounce_ms / 1000.0)
                with lock:
                    changed = pending["changed"]
                    pending["changed"] = False
                if changed:
                    # 检查存档文件是否真正变化
                    actual_changed = False
                    for key, (root, allow, deny, name, index) in path_to_cfg.items():
                        if not root.exists():
                            continue
                        files = [p for p in root.rglob("*") if p.is_file()]
                        files = filter_paths_by_patterns(root, files, allow, deny)
                        current_hash = compute_files_hash(files)
                        old_hash = self._save_files_hash.get(key, "")
                        
                        if current_hash != old_hash:
                            actual_changed = True
                            self._save_files_hash[key] = current_hash
                            # 复制变更到 repository
                            dst_root = ensure_dir(self.repo_dir / name / index)
                            copy_preserve_tree(files, root, dst_root)
                            log("watch_sync_copy_done: root={root} game={name} index={index} count={count} hash_changed=True", 
                                root=str(root), name=name, index=index, count=len(files))
                        else:
                            log("watch_skip_no_change: root={root} game={name} index={index} hash_unchanged", 
                                root=str(root), name=name, index=index)
                    
                    # 只有真正变化时才推送
                    if actual_changed:
                        self._enqueue_sync_local_to_repo_and_push()
                        log("watch_trigger_push: actual_changed=True")
                    else:
                        log("watch_skip_push: actual_changed=False")
            log("watch_debounce_stop")
        
        threading.Thread(target=_debounce_loop, name="WatchDebounce", daemon=True).start()
