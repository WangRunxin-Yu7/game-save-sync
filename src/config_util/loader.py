"""
配置加载与解析
"""
from configparser import ConfigParser
import json
import re
from pathlib import Path
from typing import Dict, List
from .models import GameEntry

class Config:
    """
    封装对 INI 配置的读取与解析
    """
    def __init__(self, path: Path):
        self.path = path
        self.parser = ConfigParser()
        # 读取 UTF-8，确保中文路径与注释正常
        self.parser.read(self.path.as_posix(), encoding="utf-8")

    def get_section(self, name: str) -> Dict[str, str]:
        """
        返回指定 section 的键值对，若不存在返回空字典
        """
        if not self.parser.has_section(name):
            return {}
        return {k: v for k, v in self.parser.items(name)}

    def get_value(self, section: str, key: str, default=None):
        """
        读取指定键，若 section 或 key 不存在返回 default
        """
        if not self.parser.has_section(section):
            return default
        if not self.parser.has_option(section, key):
            return default
        return self.parser.get(section, key)

    def get_general(self) -> Dict[str, str]:
        s = self.get_section("general")
        return {
            "device_id": s.get("device_id", "").strip(),
        }

    def get_git(self) -> Dict[str, str]:
        s = self.get_section("git")
        return {
            "remote": s.get("remote", "").strip(),
            "branch": s.get("branch", "main").strip(),
            "repository_dir": s.get("repository_dir", "./repository").strip(),
            "token": s.get("token", "").strip(),
            "username": s.get("username", "").strip(),
        }

    def get_sync(self) -> Dict[str, object]:
        s = self.get_section("sync")
        return {
            "poll_interval_minutes": int(s.get("poll_interval_minutes", "15")),
            "debounce_ms": int(s.get("debounce_ms", "1500")),
            "task_dedup_latest_only": s.get("task_dedup_latest_only", "true").lower() == "true",
            "force_overwrite": s.get("force_overwrite", "true").lower() == "true",
        }

    def get_backup(self) -> Dict[str, object]:
        s = self.get_section("backup")
        return {
            "backup_dir": s.get("backup_dir", "./backup").strip(),
            "max_backups": int(s.get("max_backups", "20")),
        }

    def get_logging(self) -> Dict[str, object]:
        s = self.get_section("logging")
        return {
            "log_dir": s.get("log_dir", "./logs").strip(),
            "max_logs": int(s.get("max_logs", "1000")),
        }

    def get_games(self) -> List[GameEntry]:
        """
        解析所有以 'game:' 开头的 section，构造 GameEntry 列表
        """
        result: List[GameEntry] = []
        def _parse_patterns(raw: str) -> List[str]:
            if not raw:
                return []
            s = raw.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    val = json.loads(s)
                    if isinstance(val, list):
                        return [str(x).strip().strip('"').strip("'") for x in val if str(x).strip()]
                except Exception:
                    pass
            parts = re.split(r"[;,]", s)
            return [p.strip().strip('"').strip("'") for p in parts if p.strip()]
        for section in self.parser.sections():
            if section.startswith("game:"):
                parts = section.split(":")
                name = parts[1] if len(parts) > 1 else ""
                index = parts[2] if len(parts) > 2 else ""
                s = self.get_section(section)
                path = s.get("path", "").strip()
                allow = _parse_patterns(s.get("allow", ""))
                deny = _parse_patterns(s.get("deny", ""))
                result.append(GameEntry(name=name, index=index, path=path, allow=allow, deny=deny))
        return result
