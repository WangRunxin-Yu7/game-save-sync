"""
Git 仓库工厂函数
"""
from pathlib import Path
from typing import Optional
import threading
from log_util import log
from .git_repo import GitRepo
from .git_helpers import redact_token


def create_git(remote: str, repo_dir: str | Path, branch: str = "main", token: Optional[str] = None, username: Optional[str] = None) -> GitRepo:
    """
    创建 Git 实例并返回
    - remote: 远端地址（可为空）
    - repo_dir: 仓库目录
    - branch: 分支名
    - token: 可选令牌（仅用于构造远端地址，日志中会打码）
    """
    rp = Path(repo_dir).resolve()
    log("git_instance_create: path={path} branch={branch} remote={remote}", path=str(rp), branch=branch, remote=redact_token(remote, token or None))
    return GitRepo(repo_dir=rp, remote=remote or "", branch=branch or "main", token=token, username=username, _lock=threading.Lock())
