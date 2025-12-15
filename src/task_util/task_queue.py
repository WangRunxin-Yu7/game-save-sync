"""
任务队列实现
"""
from typing import Optional, Dict
from collections import deque
import threading
from log_util import log
from .task_models import Task


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
