"""
数据模型定义
"""
from dataclasses import dataclass
from typing import List

@dataclass
class GameEntry:
    """
    单个游戏的存档路径条目
    - name: 游戏名（用于聚合同名游戏）
    - index: 目录索引（index0/index1...）
    - path: 本地存档目录的绝对路径
    - allow: 允许同步的文件模式（分号分隔解析后）
    - deny: 忽略同步的文件模式（分号分隔解析后）
    """
    name: str
    index: str
    path: str
    allow: List[str]
    deny: List[str]

