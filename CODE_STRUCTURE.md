# 代码结构说明

## 项目架构

```
game-save-sync/
├── src/                          # 源代码目录
│   ├── main.py                   # 程序入口 [40行]
│   │
│   ├── sync_util/                # 同步核心模块 ⭐ 新建
│   │   ├── __init__.py           # 模块导出
│   │   ├── sync_app.py           # [SyncApp] 同步应用主类
│   │   └── helpers.py            # [函数] 复制/过滤/哈希工具
│   │
│   ├── config_util/              # 配置管理模块
│   │   ├── __init__.py           # 模块导出
│   │   ├── models.py             # [GameEntry] 游戏配置数据类
│   │   ├── config_loader.py      # [ConfigLoader] INI 配置解析
│   │   └── config_manager.py     # [函数] 单例管理 + 门面函数
│   │
│   ├── git_util/                 # Git 操作模块
│   │   ├── __init__.py           # 模块导出
│   │   ├── git_repo.py           # [GitRepo] Git 仓库封装类
│   │   ├── git_helpers.py        # [函数] 命令执行 + Token 遮蔽
│   │   └── factory.py            # [create_git] Git 实例工厂
│   │
│   ├── task_util/                # 任务队列模块
│   │   ├── __init__.py           # 模块导出
│   │   ├── task_models.py        # [Task] 任务数据类
│   │   ├── task_queue.py         # [TaskQueue] 任务队列类
│   │   └── factory.py            # [函数] 任务创建工厂
│   │
│   ├── watcher_util/             # 文件监控模块
│   │   ├── __init__.py           # 模块导出
│   │   ├── watcher.py            # [Watcher] 目录监控类
│   │   ├── watcher_helpers.py    # [函数] 快照构建 + 比较
│   │   └── factory.py            # [create_watcher] 监控器工厂
│   │
│   ├── log_util/                 # 日志管理模块
│   │   ├── __init__.py           # 模块导出
│   │   ├── logger.py             # [Logger] 日志记录器类
│   │   └── log_manager.py        # [log] 单例管理 + log 函数
│   │
│   └── file_util/                # 文件工具模块
│       ├── __init__.py           # 模块导出
│       └── fs.py                 # [函数] 目录/文件操作工具
│
├── data/                         # 配置文件目录
│   └── config.ini                # 主配置文件
│
├── test/                         # 测试文件目录
│   └── ...
│
├── build_game_save_sync.bat      # 构建脚本
├── README.md                     # 项目说明
├── REFACTORING_NOTES.md          # 重构说明
└── CODE_STRUCTURE.md             # 本文件
```

## 核心类说明

### 1. SyncApp (sync_util/sync_app.py)
**职责**: 存档同步应用主控制器
- 协调备份、拉取、覆盖、推送流程
- 管理定时器和文件监控器
- 维护任务队列

**关键方法**:
- `start()`: 启动同步流程
- `stop()`: 停止所有后台任务
- `_backup_local_saves()`: 备份本地存档
- `_apply_repo_to_local()`: 应用远程存档
- `_sync_local_to_repo()`: 同步本地到仓库

### 2. GitRepo (git_util/git_repo.py)
**职责**: Git 仓库操作封装
- 封装 git 命令行操作
- 线程安全的仓库管理
- Token 自动嵌入和脱敏

**关键方法**:
- `ensure_cloned()`: 确保仓库存在
- `force_pull()`: 强制拉取远程
- `force_push()`: 强制推送
- `add()`, `commit()`: 提交变更

### 3. TaskQueue (task_util/task_queue.py)
**职责**: 异步任务队列管理
- 独立线程执行任务
- 支持唯一任务（同 key 只保留一个）
- 自动启动和停止

**关键方法**:
- `insert()`: 插入任务
- `_run()`: 后台执行循环

### 4. Watcher (watcher_util/watcher.py)
**职责**: 目录变化监控
- 轮询方式监控文件变化
- 支持多目录监控
- 提供暂停/恢复功能

**关键方法**:
- `start()`: 启动监控
- `pause()`, `resume()`: 暂停/恢复
- `release()`: 释放资源
- `add_path()`, `remove_path()`: 动态管理监控路径

### 5. Logger (log_util/logger.py)
**职责**: 日志文件管理
- 按日期分割日志
- 自动清理旧日志
- 线程安全写入

**关键方法**:
- `write()`: 写入日志
- `_cleanup_excess_logs()`: 清理旧日志

### 6. ConfigLoader (config_util/config_loader.py)
**职责**: INI 配置文件解析
- 解析游戏配置 (game:name:index)
- 提供类型化的配置访问
- 支持模式匹配 (allow/deny)

**关键方法**:
- `get_general()`, `get_git()`, `get_sync()`, `get_backup()`, `get_logging()`
- `get_games()`: 返回 GameEntry 列表

## 工具函数模块

### sync_util/helpers.py
- `get_timestamp()`: 生成时间戳
- `copy_preserve_tree()`: 保留目录结构复制
- `filter_paths_by_patterns()`: 文件路径过滤
- `compute_files_hash()`: 计算文件列表哈希

### git_util/git_helpers.py
- `redact_token()`: Token 遮蔽
- `run_git_command()`: 执行 Git 命令

### watcher_util/watcher_helpers.py
- `safe_stat()`: 安全获取文件状态
- `build_snapshot()`: 构建目录快照
- `compare_snapshots()`: 比较快照差异

### file_util/fs.py
- `ensure_dir()`: 确保目录存在
- `copy_files()`: 批量复制文件
- `find_files()`: 模式匹配查找文件

## 工厂函数

每个核心模块都提供工厂函数简化对象创建：

- `create_git()`: 创建 GitRepo 实例
- `create_queue()`: 创建 TaskQueue 实例
- `create_task()`: 创建 Task 实例
- `create_watcher()`: 创建 Watcher 实例

## 单例管理

### config_util/config_manager.py
- 全局单例配置管理
- 门面函数: `get_git()`, `get_games()` 等
- 支持配置重载: `reload_config()`

### log_util/log_manager.py
- 全局单例日志管理
- 门面函数: `log(template, **kwargs)`
- 支持日志器重载: `reload_logger()`

## 数据模型

### GameEntry (config_util/models.py)
```python
@dataclass
class GameEntry:
    name: str           # 游戏名称
    index: str          # 存档索引
    path: str           # 本地路径
    allow: List[str]    # 允许模式
    deny: List[str]     # 忽略模式
```

### Task (task_util/task_models.py)
```python
@dataclass
class Task:
    action: Callable    # 任务函数
    args: tuple         # 位置参数
    kwargs: dict        # 关键字参数
    unique: bool        # 是否唯一
    insert_mode: str    # 插入模式
    key: str            # 唯一标识
```

## 依赖关系图

```
main.py
  └─> SyncApp
        ├─> ConfigLoader (配置)
        ├─> GitRepo (Git操作)
        ├─> TaskQueue (任务队列)
        ├─> Watcher (文件监控)
        ├─> Logger (日志)
        └─> helpers (工具函数)

SyncApp 依赖所有其他模块，是应用的核心控制器
其他模块相互独立，通过 SyncApp 协调工作
```

## 模块独立性

✅ **高内聚**: 每个模块职责单一明确
✅ **低耦合**: 模块间通过接口交互
✅ **可测试**: 每个类和函数都可独立测试
✅ **可复用**: 工具函数和类可在其他项目中复用

## 扩展建议

### 添加新的游戏类型支持
1. 在 `config.ini` 中添加新的 `[game:name:index]` 配置
2. 无需修改代码，自动识别

### 添加新的同步策略
1. 在 `sync_util/sync_app.py` 中添加新方法
2. 或创建新的策略类继承/组合 SyncApp

### 添加新的存储后端
1. 创建新的模块 (如 `cloud_util/`)
2. 实现类似 GitRepo 的接口
3. 在 SyncApp 中注入使用

### 添加 GUI
1. 创建 `gui_util/` 模块
2. 封装 SyncApp 调用
3. 保持核心逻辑不变

## 性能考虑

- **哈希计算**: 使用元数据哈希而非内容哈希，快速判断变化
- **任务队列**: 异步执行，不阻塞主流程
- **文件监控**: 轮询间隔可配置，平衡实时性和性能
- **线程安全**: 关键操作使用锁保护，避免竞态条件

## 安全考虑

- **Token 脱敏**: 日志中自动遮蔽敏感信息
- **配置文件权限**: 建议限制 config.ini 访问权限
- **Git 操作**: 禁用交互提示，避免挂起
- **错误处理**: 异常不会导致程序崩溃

---

**最后更新**: 2025-12-15
**代码总行数**: ~2,000 行 (含注释和空行)
**模块数量**: 7 个主模块
**类数量**: 7 个核心类
