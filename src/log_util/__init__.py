"""
日志工具门面
- 首次调用自动初始化，根据配置创建日志目录并清理多余日志文件
- 提供简单接口：log(template, **kwargs) 格式化并写入一行，包含时间
"""
from .logger import log, reload_logger

