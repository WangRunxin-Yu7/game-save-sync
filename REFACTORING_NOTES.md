# 代码重构说明

## 重构日期
2025-12-15

## 重构目标
将项目代码结构规范化，遵循单一职责原则，让每个文件只包含一个主要的类。

## 重构前后对比

### 重构前 (16 个文件)
```
src/
├── main.py
├── sync_app.py                  [325行, 包含 SyncApp 类 + 4个工具函数]
├── config_util/
│   ├── __init__.py
│   ├── config.py                [90行, 门面模块 + 工具函数]
│   ├── loader.py                [107行, Config 类]
│   └── models.py                [23行, GameEntry 数据类]
├── git_util/
│   ├── __init__.py
│   └── git.py                   [235行, GitRepo 类 + 工具函数]
├── task_util/
│   ├── __init__.py
│   └── task.py                  [130行, Task 类 + TaskQueue 类 + 工厂函数]
├── watcher_util/
│   ├── __init__.py
│   └── watcher.py               [170行, Watcher 类 + 工具函数]
├── log_util/
│   ├── __init__.py
│   └── logger.py                [105行, Logger 类 + 门面函数]
└── file_util/
    ├── __init__.py
    └── fs.py                    [92行, 纯工具函数]
```

### 重构后 (32 个文件)
```
src/
├── main.py                      [增加 --branch 参数]
├── sync_util/                   [新建模块]
│   ├── __init__.py
│   ├── sync_app.py              [SyncApp 类, 292行]
│   └── helpers.py               [工具函数: 复制/过滤/哈希/时间戳]
├── config_util/
│   ├── __init__.py              [统一导出接口]
│   ├── config_loader.py         [ConfigLoader 类, 单一职责]
│   ├── config_manager.py        [单例管理 + 门面函数]
│   └── models.py                [GameEntry 数据类]
├── git_util/
│   ├── __init__.py
│   ├── git_repo.py              [GitRepo 类, 单一职责]
│   ├── git_helpers.py           [工具函数: redact_token, run_git_command]
│   └── factory.py               [create_git 工厂函数]
├── task_util/
│   ├── __init__.py
│   ├── task_models.py           [Task 数据类 + InsertMode 类型]
│   ├── task_queue.py            [TaskQueue 类, 单一职责]
│   └── factory.py               [create_queue, create_task, enqueue]
├── watcher_util/
│   ├── __init__.py
│   ├── watcher.py               [Watcher 类, 单一职责]
│   ├── watcher_helpers.py       [工具函数: safe_stat, build_snapshot, compare_snapshots]
│   └── factory.py               [create_watcher 工厂函数]
├── log_util/
│   ├── __init__.py
│   ├── logger.py                [Logger 类, 单一职责]
│   └── log_manager.py           [单例管理 + log 门面函数]
└── file_util/
    ├── __init__.py
    └── fs.py                    [保持不变, 纯工具函数集合]
```

## 主要改进

### 1. **模块化拆分**
- ✅ `sync_app.py` → `sync_util/` 模块 (sync_app.py + helpers.py)
- ✅ `task.py` → 拆分为 task_models.py + task_queue.py + factory.py
- ✅ `git.py` → 拆分为 git_repo.py + git_helpers.py + factory.py
- ✅ `watcher.py` → 拆分为 watcher.py + watcher_helpers.py + factory.py
- ✅ `config.py` + `loader.py` → 重组为 config_loader.py + config_manager.py
- ✅ `logger.py` → 拆分为 logger.py + log_manager.py

### 2. **单一职责原则**
每个文件现在只包含：
- **一个主要的类** (如 SyncApp, GitRepo, TaskQueue, Watcher, Logger)
- 或 **一组相关的工具函数** (如 helpers.py, git_helpers.py)
- 或 **工厂函数** (factory.py)
- 或 **数据模型** (models.py)

### 3. **清晰的职责分离**
- **类文件**: 只包含类定义及其方法
- **helpers 文件**: 只包含纯函数工具
- **factory 文件**: 只包含对象创建的工厂函数
- **manager 文件**: 单例模式管理和门面函数
- **models 文件**: 数据类定义

### 4. **改进的配置路径查找**
在 `config_manager.py` 中改进了配置文件路径检测：
- 支持 PyInstaller 打包后的路径查找 (使用 `sys.executable`)
- 开发模式使用当前工作目录
- 解决了之前提到的打包后配置文件找不到的问题

### 5. **增强的命令行参数**
在 `main.py` 中添加了 `--branch` 参数：
```python
parser.add_argument("--branch", type=str, default=None, help="覆盖配置中的 Git 分支名")
```

### 6. **优化的日志清理逻辑**
在 `logger.py` 中改进了日志文件清理：
- 改用文件名排序（日期格式 `%Y-%m-%d` 天然可排序）
- 解决了之前使用 `st_mtime` 可能导致的顺序混乱问题

## 文件命名规范

1. **类文件**: 小写下划线命名，如 `sync_app.py`, `git_repo.py`, `task_queue.py`
2. **工具函数文件**: `helpers.py` 或 `<module>_helpers.py`
3. **工厂文件**: `factory.py`
4. **管理器文件**: `<module>_manager.py`
5. **模型文件**: `models.py` 或 `<module>_models.py`

## 导入规范

每个模块的 `__init__.py` 统一管理导出接口：
```python
# 例如 sync_util/__init__.py
from .sync_app import SyncApp
from .helpers import copy_preserve_tree, filter_paths_by_patterns, compute_files_hash, get_timestamp

__all__ = ["SyncApp", "copy_preserve_tree", "filter_paths_by_patterns", "compute_files_hash", "get_timestamp"]
```

外部使用时保持简洁：
```python
from sync_util import SyncApp
from log_util import log
from config_util import get_git, get_games
```

## 兼容性保证

所有外部接口保持不变，只是内部实现被重构：
- ✅ `main.py` 只需修改导入路径
- ✅ 所有公开 API 保持一致
- ✅ 配置文件格式不变
- ✅ 命令行接口增强但向后兼容

## 优点总结

1. **可维护性**: 每个文件职责清晰，易于理解和修改
2. **可测试性**: 模块化设计便于单元测试
3. **可扩展性**: 新功能可以独立添加到相应模块
4. **代码复用**: 工具函数独立，可在多处复用
5. **团队协作**: 文件粒度更小，减少合并冲突
6. **符合规范**: 遵循 Python 社区最佳实践

## 构建说明

重构后的代码可以正常使用原有的构建脚本：
```bash
build_game_save_sync.bat
```

PyInstaller 会自动分析新的模块结构并打包所有依赖。

## 验证方式

运行以下命令验证重构是否成功：
```bash
cd src
python main.py --help
```

应该能看到增强的命令行参数帮助信息。
