"""
基础文件工具
- ensure_dir: 检查并创建目录，记录是否已存在
- copy_files: 复制文件到目标目录，默认覆盖同名文件
- find_files: 在目录下匹配 allow 模式并排除 deny 模式，返回文件列表
"""
from pathlib import Path
from typing import List
import shutil
from log_util import log

def ensure_dir(path: str | Path) -> Path:
    """
    查看并确保目录存在，不存在则创建
    返回标准化的 Path；输出日志包含路径与是否已存在
    """
    p = Path(path).resolve()
    existed = p.exists()
    p.mkdir(parents=True, exist_ok=True)
    log("ensure_dir: {path} existed={existed}", path=str(p), existed=existed)
    return p

def copy_files(paths: List[str | Path], target_dir: str | Path) -> List[Path]:
    """
    将给定文件列表复制到目标目录
    - 目标目录不存在会自动创建
    - 遇到同名文件默认覆盖
    - 跳过不存在或非文件路径并记录日志
    返回复制后的目标文件路径列表
    """
    dst_dir = ensure_dir(target_dir)
    copied: List[Path] = []
    for src in paths:
        sp = Path(src)
        if not sp.is_file():
            log("skip_missing_file: {path}", path=str(sp))
            continue
        dp = dst_dir / sp.name
        try:
            shutil.copy2(sp.as_posix(), dp.as_posix())
            copied.append(dp.resolve())
        except Exception as e:
            log("copy_error: {src} -> {dst} err={err}", src=str(sp), dst=str(dp), err=str(e))
    log("copy_files_done: count={count} target={target}", count=len(copied), target=str(dst_dir))
    return copied

def find_files(dir_path: str | Path, allow: List[str] | None = None, deny: List[str] | None = None) -> List[Path]:
    """
    在指定目录下查找文件
    - allow: 模式数组（glob），为空则默认递归查找所有文件
    - deny: 模式数组（glob），为空则不做排除
    - 返回满足条件的文件路径列表（已排序）
    说明：支持 `**` 递归匹配；模式解析错误会记录日志但不中断
    """
    root = Path(dir_path).resolve()
    if not root.exists():
        log("find_files_root_missing: {root}", root=str(root))
        return []
    allow = allow or []
    deny = deny or []
    if allow:
        allowed_set = set()
        for pat in allow:
            try:
                for p in root.glob(pat):
                    if p.is_file():
                        allowed_set.add(p.resolve())
            except Exception as e:
                log("allow_pattern_error: {pattern} err={err}", pattern=str(pat), err=str(e))
    else:
        allowed_set = {p.resolve() for p in root.rglob("*") if p.is_file()}
    if deny:
        deny_set = set()
        for pat in deny:
            try:
                for p in root.glob(pat):
                    if p.is_file():
                        deny_set.add(p.resolve())
            except Exception as e:
                log("deny_pattern_error: {pattern} err={err}", pattern=str(pat), err=str(e))
        result = [p for p in allowed_set if p not in deny_set]
    else:
        result = list(allowed_set)
    log(
        "find_files_done: root={root} allow_n={an} deny_n={dn} out_n={out}",
        root=str(root),
        an=len(allow),
        dn=len(deny),
        out=len(result),
    )
    return sorted(result)
