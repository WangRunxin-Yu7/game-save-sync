"""
简单任务队列
- 队列独立运行，互不影响
- 支持任务唯一性与插入方式（尾部/固定）
"""
from dataclasses import dataclass
from typing import Callable, Any, Optional, List, Dict
from collections import deque
import threading
from log_util import log

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

class TaskQueue:
    """
    任务队列
    - 独立运行，内部线程按序执行直到队列空
    """
    def __init__(self, name: str):
        self.name = name
        self._dq: deque[Task] = deque()
        self._unique_index: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker: Optional[threading.Thread] = None
        log("queue_create: {name}", name=self.name)

    def _start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._worker = threading.Thread(target=self._run, name=f"QueueWorker-{self.name}", daemon=True)
            self._worker.start()
            log("worker_start: {name}", name=self.name)

    def _run(self):
        while True:
            task: Optional[Task] = None
            with self._lock:
                if not self._dq:
                    self._running = False
                    log("worker_done: {name}", name=self.name)
                    return
                task = self._dq.popleft()
                if task.unique:
                    # 唯一任务被取出后，从索引中移除
                    self._unique_index.pop(task.key, None)
            try:
                log("task_start: queue={q} key={key}", q=self.name, key=task.key)
                task.action(*task.args, **task.kwargs)
                log("task_done: queue={q} key={key}", q=self.name, key=task.key)
            except Exception as e:
                log("task_error: queue={q} key={key} err={err}", q=self.name, key=task.key, err=str(e))

    def insert(self, task: Task):
        with self._lock:
            op = "insert"
            if task.unique:
                existing = self._unique_index.get(task.key)
                if existing is not None:
                    if task.insert_mode == "tail":
                        # 将现有任务移动到队尾（保持唯一，不重复）
                        try:
                            # 从双端队列中删除再追加
                            self._dq.remove(existing)
                            self._dq.append(existing)
                            op = "move_tail"
                        except ValueError:
                            # 若未找到（极端竞态），直接追加现有
                            self._dq.append(existing)
                            op = "append_existing"
                    elif task.insert_mode == "fixed":
                        # 保持原位置，不做任何变更
                        op = "keep_order"
                    log("enqueue_unique_dup: queue={q} key={key} op={op}", q=self.name, key=task.key, op=op)
                else:
                    self._dq.append(task)
                    self._unique_index[task.key] = task
                    log("enqueue_unique_new: queue={q} key={key}", q=self.name, key=task.key)
            else:
                self._dq.append(task)
                log("enqueue_normal: queue={q} key={key}", q=self.name, key=task.key)
        # 自动启动
        self._start()

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

