"""
Git 辅助工具函数
"""
import subprocess
import shlex
import os
from pathlib import Path
from typing import Optional, Tuple, List
from log_util import log


def redact_token(s: str, token: Optional[str]) -> str:
    """使用 *** 遮蔽 token"""
    if token:
        return s.replace(token, "***")
    return s


def run_git_command(cmd: List[str], cwd: Path, token: Optional[str] = None) -> Tuple[int, str, str]:
    """
    运行 git 命令，返回 (code, stdout, stderr)，禁用交互
    """
    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "Never",
        "GIT_ASKPASS": "echo",
    }
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env=env,
            creationflags=(0x08000000 if os.name == "nt" else 0),
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        cmd_str = " ".join(shlex.quote(x) for x in cmd)
        log("git_run: cwd={cwd} cmd={cmd} code={code}", cwd=str(cwd), cmd=redact_token(cmd_str, token), code=p.returncode)
        out = p.stdout or ""
        err = p.stderr or ""
        return p.returncode, out, err
    except Exception as e:
        cmd_str = " ".join(shlex.quote(x) for x in cmd)
        log("git_run_error: cwd={cwd} cmd={cmd} err={err}", cwd=str(cwd), cmd=redact_token(cmd_str, token), err=str(e))
        return 1, "", str(e)
