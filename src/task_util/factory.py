"""
任务和队列的工厂函数
"""
from typing import Callable, Any, Optional
from log_util import log
from .task_models import Task, InsertMode
from .task_queue import TaskQueue


def create_queue(name: str) -> TaskQueue:
    """
    创建一个任务队列，并返回
    """
    return TaskQueue(name=name)


def create_task(action: Callable[..., Any], *args, unique: bool = False, insert_mode: InsertMode = "tail", key: Optional[str] = None, **kwargs) -> Task:
    """
    创建一个任务，并返回
    - unique: 是否唯一
    - insert_mode: 对唯一任务的插入方式（'tail' 或 'fixed'）
    - key: 唯一任务的标识（默认使用函数名）
    说明：
    - 非唯一任务插入方式无意义，忽略
    """
    k = key or getattr(action, "__name__", "task")
    t = Task(action=action, args=args, kwargs=kwargs, unique=unique, insert_mode=insert_mode, key=k)
    log("task_create: key={key} unique={unique} mode={mode}", key=t.key, unique=t.unique, mode=t.insert_mode)
    return t


def enqueue(queue: TaskQueue, task: Task):
    """
    向任务队列中插入一个任务，若队列未启动则自动启动
    """
    queue.insert(task)
