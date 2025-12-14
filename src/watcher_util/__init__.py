"""
文件变化监控门面
- 支持监控一个或多个目录
- 提供暂停、启动、释放与动态增删目录
"""
from .watcher import create_watcher, Watcher

