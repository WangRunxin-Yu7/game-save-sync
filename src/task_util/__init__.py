"""
任务工具门面
- 创建任务队列与任务
- 向队列插入任务并自动启动执行
"""
from .task import create_queue, create_task, enqueue

