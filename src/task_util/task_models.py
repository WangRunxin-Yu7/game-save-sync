"""
任务模型定义
"""
from dataclasses import dataclass
from typing import Callable, Any

InsertMode = str  # "tail" | "fixed"


@dataclass
class Task:
    """
    任务定义
    - action: 可调用任务
    - args/kwargs: 任务参数
    - unique: 是否唯一（同 key 只保留一个）
    - insert_mode: 唯一任务插入策略（tail: 重复插入移至队尾；fixed: 保持原位置不变）
    - key: 唯一标识（默认使用函数名）
    """
    action: Callable[..., Any]
    args: tuple
    kwargs: dict
    unique: bool
    insert_mode: InsertMode
    key: str
