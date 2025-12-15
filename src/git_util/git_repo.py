"""
Git 仓库封装类
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import threading
from log_util import log
from .git_helpers import run_git_command, redact_token


@dataclass
class GitRepo:
    """
    Git 仓库实例
    - repo_dir: 仓库目录
    - remote: 远端地址（可为空）
    - branch: 分支名（默认 main）
    - token: 令牌（仅用于构造远端地址；不记录到日志）
    - 所有操作均加锁，保证并发安全
    """
    repo_dir: Path
    remote: str
    branch: str
    token: Optional[str]
    username: Optional[str]
    _lock: threading.Lock

    def _git(self, *args: str) -> Tuple[int, str, str]:
        return run_git_command(["git", *args], cwd=self.repo_dir, token=self.token)

    def _ensure_repo_dir(self):
        self.repo_dir.mkdir(parents=True, exist_ok=True)

    def _is_dir_empty(self, p: Path) -> bool:
        if not p.exists():
            return True
        try:
            return next(p.iterdir(), None) is None
        except Exception:
            return False

    def _embed_token(self, url: str) -> str:
        if self.token and url.startswith("https://"):
            if self.username:
                cred = f"{self.username}:{self.token}"
            else:
                log("git_auth_username_missing: token provided without username, auth may fail")
                cred = self.token
            return url.replace("https://", f"https://{cred}@")
        return url

    def _set_user(self):
        self._git("config", "user.name", "game-save-sync")
        self._git("config", "user.email", "game-save-sync@local")
        self._git("config", "credential.helper", "")

    def ensure_cloned(self):
        """
        确保本地仓库存在：
        - 若不存在或空目录且 remote 非空：强制 clone 到 repo_dir（必要时清空空目录）
        - 若不存在且 remote 为空：在 repo_dir 初始化本地仓库
        - 若存在：确保分支可用；若设置了 remote 则写入/更新 origin
        """
        with self._lock:
            self._ensure_repo_dir()
            git_dir = self.repo_dir / ".git"
            if not git_dir.exists():
                if self.remote:
                    url = self._embed_token(self.remote)
                    # 仅当目录不存在或为空时执行 clone；为空时清理目录避免 clone 报错
                    if self._is_dir_empty(self.repo_dir):
                        try:
                            # 清理空目录（确保 clone 可写入）
                            if self.repo_dir.exists():
                                self.repo_dir.rmdir()
                        except Exception:
                            pass
                        code, _, err = run_git_command(["git", "clone", "--quiet", url, str(self.repo_dir)], cwd=self.repo_dir.parent, token=self.token)
                    else:
                        code, _, err = (1, "", "destination not empty")
                    if code != 0:
                        log("git_clone_fail: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                        return False
                    log("git_clone_ok: path={path} branch={branch}", path=str(self.repo_dir), branch=self.branch)
                else:
                    code, _, err = self._git("init")
                    if code != 0:
                        log("git_init_fail: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                        return False
                    log("git_init_ok: path={path}", path=str(self.repo_dir))
            # 写入/更新 origin
            if self.remote:
                url = self._embed_token(self.remote)
                self._git("remote", "remove", "origin")
                self._git("remote", "add", "origin", url)
            # 切换分支（若不存在则创建）
            code, _, _ = self._git("rev-parse", "--verify", self.branch)
            if code != 0:
                self._git("checkout", "-b", self.branch)
            else:
                self._git("checkout", self.branch)
            self._set_user()
            return True

    def force_pull(self):
        """
        强制拉取远端：fetch + reset --hard + clean -fdx
        - 若未配置 remote，直接跳过
        """
        with self._lock:
            if not self.remote:
                log("git_pull_skip_remote_missing: {path}", path=str(self.repo_dir))
                return False
            self._ensure_repo_dir()
            code, _, err = self._git("fetch", "origin", self.branch, "--quiet")
            if code != 0:
                log("git_pull_fail_fetch: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                return False
            code, _, err = self._git("reset", "--hard", f"origin/{self.branch}")
            if code != 0:
                log("git_pull_fail_reset: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                return False
            self._git("clean", "-fdx")
            log("git_pull_ok: path={path} branch={branch}", path=str(self.repo_dir), branch=self.branch)
            return True

    def add(self, paths: Optional[List[str | Path]] = None):
        """
        添加变更：paths 为空则 add -A
        """
        with self._lock:
            self._ensure_repo_dir()
            if not paths:
                self._git("add", "-A")
            else:
                args = ["add"]
                args += [str(Path(p)) for p in paths]
                self._git(*args)
            log("git_add_ok: path={path}", path=str(self.repo_dir))
            return True

    def _has_changes(self) -> bool:
        code, out, _ = self._git("status", "--porcelain")
        return code == 0 and bool(out.strip())

    def commit(self, message: str):
        """
        提交变更：若无变更则跳过
        """
        with self._lock:
            self._ensure_repo_dir()
            if not self._has_changes():
                log("git_commit_skip_no_changes: {path}", path=str(self.repo_dir))
                return False
            self._set_user()
            code, _, err = self._git("commit", "-m", message)
            if code != 0:
                log("git_commit_fail: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                return False
            log("git_commit_ok: path={path} msg={msg}", path=str(self.repo_dir), msg=message)
            return True

    def force_push(self):
        """
        强制推送：push --force-with-lease
        - 若未配置 remote，直接跳过
        """
        with self._lock:
            if not self.remote:
                log("git_push_skip_remote_missing: {path}", path=str(self.repo_dir))
                return False
            self._ensure_repo_dir()
            # 确保 upstream
            self._git("branch", "--set-upstream-to", f"origin/{self.branch}", self.branch)
            code, _, err = self._git("push", "--force-with-lease", "origin", self.branch)
            if code != 0:
                log("git_push_fail: path={path} err={err}", path=str(self.repo_dir), err=redact_token(err.strip(), self.token))
                return False
            log("git_push_ok: path={path} branch={branch}", path=str(self.repo_dir), branch=self.branch)
            return True
