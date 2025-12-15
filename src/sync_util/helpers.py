"""
同步相关的辅助工具函数
"""
from __future__ import annotations
from pathlib import Path
from typing import List
from datetime import datetime
import fnmatch
import hashlib
import shutil
from log_util import log


def get_timestamp() -> str:
    """生成时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def copy_preserve_tree(files: List[Path], src_root: Path, dst_root: Path):
    """
    复制文件到目标根目录，保留相对目录结构，覆盖同名
    """
    for fp in files:
        rel = fp.resolve().relative_to(src_root.resolve())
        target = dst_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(fp.as_posix(), target.as_posix())
        except Exception as e:
            log("copy_preserve_error: {src} -> {dst} err={err}", src=str(fp), dst=str(target), err=str(e))


def filter_paths_by_patterns(root: Path, files: List[Path], allow: List[str], deny: List[str]) -> List[Path]:
    """
    使用 allow/deny 模式过滤文件列表；模式按相对路径匹配
    """
    rels = [(f, f.resolve().relative_to(root.resolve()).as_posix()) for f in files]
    if allow:
        allowed = [f for f, rel in rels if any(fnmatch.fnmatch(rel, pat) for pat in allow)]
    else:
        allowed = [f for f, _ in rels]
    if deny:
        result = [f for f in allowed if not any(fnmatch.fnmatch(f.resolve().relative_to(root.resolve()).as_posix(), pat) for pat in deny)]
    else:
        result = allowed
    return result


def compute_files_hash(files: List[Path]) -> str:
    """
    计算文件列表的哈希值（基于文件路径、大小和修改时间）
    用于快速判断存档文件是否发生变化
    """
    if not files:
        return ""
    hasher = hashlib.sha256()
    for fp in sorted(files, key=lambda p: p.as_posix()):
        try:
            stat = fp.stat()
            # 使用文件路径、大小和修改时间作为标识
            info = f"{fp.as_posix()}:{stat.st_size}:{stat.st_mtime}".encode('utf-8')
            hasher.update(info)
        except Exception as e:
            log("compute_hash_error: {path} err={err}", path=str(fp), err=str(e))
    return hasher.hexdigest()
