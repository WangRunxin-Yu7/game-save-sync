"""
监控器辅助函数
"""
from pathlib import Path
from typing import Dict, Optional, Tuple
from log_util import log

SnapshotEntry = Tuple[int, int]  # (mtime_ns, size)


def safe_stat(p: Path) -> Optional[SnapshotEntry]:
    """安全获取文件状态"""
    try:
        st = p.stat()
        return (st.st_mtime_ns, st.st_size)
    except Exception as e:
        log("stat_error: {path} err={err}", path=str(p), err=str(e))
        return None


def build_snapshot(root: Path) -> Dict[str, SnapshotEntry]:
    """
    递归构建目录快照（文件路径 -> (mtime_ns, size)）
    """
    snap: Dict[str, SnapshotEntry] = {}
    if not root.exists():
        return snap
    # 遍历所有文件
    for p in root.rglob("*"):
        if p.is_file():
            se = safe_stat(p)
            if se is not None:
                snap[p.resolve().as_posix()] = se
    return snap


def compare_snapshots(old: Dict[str, SnapshotEntry], new: Dict[str, SnapshotEntry]):
    """比较两个快照，返回创建、修改、删除的文件列表"""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    created = sorted(list(new_keys - old_keys))
    deleted = sorted(list(old_keys - new_keys))
    modified = []
    for k in (old_keys & new_keys):
        if old[k] != new[k]:
            modified.append(k)
    modified.sort()
    return created, modified, deleted
