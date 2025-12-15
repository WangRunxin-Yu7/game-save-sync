# 快速参考指南

## 📁 文件与类的对应关系

### 一个文件 = 一个类 (遵循单一职责原则)

| 文件路径 | 包含的类/函数 | 职责 |
|---------|-------------|------|
| `sync_util/sync_app.py` | **SyncApp** | 同步应用主控制器 |
| `git_util/git_repo.py` | **GitRepo** | Git 仓库操作封装 |
| `task_util/task_queue.py` | **TaskQueue** | 任务队列管理 |
| `watcher_util/watcher.py` | **Watcher** | 文件监控器 |
| `log_util/logger.py` | **Logger** | 日志记录器 |
| `config_util/config_loader.py` | **ConfigLoader** | 配置文件解析器 |
| `config_util/models.py` | **GameEntry** | 游戏配置数据类 |
| `task_util/task_models.py` | **Task** | 任务数据类 |

### 工具函数模块

| 文件路径 | 包含的函数 |
|---------|-----------|
| `sync_util/helpers.py` | `get_timestamp()`, `copy_preserve_tree()`, `filter_paths_by_patterns()`, `compute_files_hash()` |
| `git_util/git_helpers.py` | `redact_token()`, `run_git_command()` |
| `watcher_util/watcher_helpers.py` | `safe_stat()`, `build_snapshot()`, `compare_snapshots()` |
| `file_util/fs.py` | `ensure_dir()`, `copy_files()`, `find_files()` |

### 工厂函数模块

| 文件路径 | 包含的工厂函数 |
|---------|--------------|
| `git_util/factory.py` | `create_git()` |
| `task_util/factory.py` | `create_queue()`, `create_task()`, `enqueue()` |
| `watcher_util/factory.py` | `create_watcher()` |

### 管理器模块 (单例模式)

| 文件路径 | 包含的函数 |
|---------|-----------|
| `config_util/config_manager.py` | `get_git()`, `get_sync()`, `get_backup()`, `get_logging()`, `get_games()`, `get_general()`, `reload_config()` |
| `log_util/log_manager.py` | `log()`, `reload_logger()` |

## 📦 模块导入速查

### 主应用
```python
from sync_util import SyncApp
```

### 配置管理
```python
from config_util import (
    get_git,          # Git 配置
    get_sync,         # 同步策略配置
    get_backup,       # 备份配置
    get_logging,      # 日志配置
    get_games,        # 游戏列表
    get_general,      # 通用配置
    reload_config     # 重载配置
)
```

### Git 操作
```python
from git_util import GitRepo, create_git

# 创建 Git 仓库实例
repo = create_git(
    remote="https://github.com/user/repo.git",
    repo_dir="./repository",
    branch="main",
    token="ghp_xxx",
    username="user"
)
```

### 任务队列
```python
from task_util import create_queue, create_task, enqueue

# 创建队列
queue = create_queue("my_queue")

# 创建任务
def my_task():
    print("执行任务")

task = create_task(my_task, unique=True, key="task1")

# 入队
enqueue(queue, task)
```

### 文件监控
```python
from watcher_util import create_watcher

def callback(root, created, modified, deleted):
    print(f"检测到变化: {len(created)} 新建, {len(modified)} 修改, {len(deleted)} 删除")

watcher = create_watcher(
    paths=["./watch_dir1", "./watch_dir2"],
    callback=callback,
    interval_ms=1000
)
watcher.start()
```

### 日志记录
```python
from log_util import log

# 简单日志
log("应用启动")

# 格式化日志
log("用户 {user} 登录成功", user="admin")
log("文件 {file} 大小: {size} 字节", file="data.txt", size=1024)
```

### 文件工具
```python
from file_util import ensure_dir, copy_files, find_files

# 确保目录存在
path = ensure_dir("./backup")

# 复制文件
copied = copy_files(["file1.txt", "file2.txt"], "./target_dir")

# 查找文件
files = find_files("./game_dir", allow=["*.sav", "*.dat"], deny=["*.tmp"])
```

## 🔧 常用操作示例

### 启动应用
```python
from sync_util import SyncApp

app = SyncApp(
    override_remote="https://github.com/user/repo.git",  # 可选
    override_token="ghp_xxx",                            # 可选
    override_username="user",                            # 可选
    override_branch="main"                               # 可选
)

try:
    app.start()
    # 应用运行中...
except KeyboardInterrupt:
    app.stop()
```

### 访问配置
```python
from config_util import get_git, get_games

# 获取 Git 配置
git_cfg = get_git()
print(f"远程仓库: {git_cfg['remote']}")
print(f"分支: {git_cfg['branch']}")

# 获取游戏列表
games = get_games()
for game in games:
    print(f"游戏: {game.name}, 路径: {game.path}")
```

### Git 操作
```python
from git_util import create_git

repo = create_git("https://github.com/user/repo.git", "./repo")

# 确保仓库存在
if repo.ensure_cloned():
    # 拉取最新
    repo.force_pull()
    
    # 添加变更
    repo.add(None)  # None = 添加所有
    
    # 提交
    repo.commit("Update saves")
    
    # 推送
    repo.force_push()
```

### 创建任务队列
```python
from task_util import create_queue, create_task, enqueue

# 创建队列
pull_queue = create_queue("pull")
push_queue = create_queue("push")

# 创建唯一任务（同 key 只保留最新）
def sync_task():
    print("执行同步")

task = create_task(
    sync_task,
    unique=True,          # 唯一任务
    insert_mode='tail',   # 重复时移到队尾
    key='sync'            # 唯一标识
)

enqueue(push_queue, task)
```

### 监控目录变化
```python
from watcher_util import create_watcher
from pathlib import Path

def on_change(root, created, modified, deleted):
    print(f"目录 {root} 发生变化:")
    for file in created:
        print(f"  新建: {file}")
    for file in modified:
        print(f"  修改: {file}")
    for file in deleted:
        print(f"  删除: {file}")

watcher = create_watcher(
    paths=[Path("./save_dir")],
    callback=on_change,
    interval_ms=1000
)

watcher.start()

# 暂停监控
watcher.pause()

# 恢复监控
watcher.resume()

# 动态添加路径
watcher.add_path("./another_dir")

# 停止监控
watcher.release()
```

## 🎯 设计原则总结

### ✅ 已实现的原则

1. **单一职责原则 (SRP)**
   - 每个类只负责一个功能
   - 每个文件只包含一个主要的类

2. **开放封闭原则 (OCP)**
   - 通过工厂函数和接口扩展
   - 不修改现有代码，只添加新功能

3. **依赖倒置原则 (DIP)**
   - 依赖抽象接口而非具体实现
   - 通过工厂函数注入依赖

4. **接口隔离原则 (ISP)**
   - 每个模块只暴露必要的接口
   - 通过 `__init__.py` 控制导出

5. **迪米特法则 (LoD)**
   - 模块间通过门面函数通信
   - 减少模块间的直接依赖

## 📝 代码规范

### 命名规范
- **类名**: PascalCase (如 `SyncApp`, `GitRepo`)
- **函数名**: snake_case (如 `create_git`, `get_config`)
- **私有方法**: 前缀 `_` (如 `_ensure_repo_dir`)
- **常量**: UPPER_CASE (如 `MAX_RETRIES`)

### 文档字符串
每个类和公开函数都有文档字符串：
```python
def create_git(remote: str, repo_dir: str | Path, ...) -> GitRepo:
    """
    创建 Git 实例并返回
    
    Args:
        remote: 远端地址（可为空）
        repo_dir: 仓库目录
        ...
    
    Returns:
        GitRepo 实例
    """
```

### 类型注解
所有公开函数都有类型注解：
```python
def compute_files_hash(files: List[Path]) -> str:
    ...
```

## 🚀 性能优化建议

1. **哈希计算**: 已使用元数据哈希，避免读取文件内容
2. **任务队列**: 已异步执行，避免阻塞主线程
3. **配置缓存**: 已使用单例模式，避免重复读取
4. **日志优化**: 已按日分割，定期清理旧日志

## 🔒 安全建议

1. **配置文件权限**: `chmod 600 data/config.ini`
2. **Token 管理**: 使用环境变量或密钥管理工具
3. **日志审计**: 定期检查日志，发现异常行为
4. **Git 权限**: 使用只读 Token 进行拉取操作

---

**提示**: 此文档随代码更新同步维护
