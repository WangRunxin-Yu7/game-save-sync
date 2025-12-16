# 更新日志

## [v1.1.0] - 2025-12-15

### 🎉 新增功能

#### 配置文件热重载 (Config Hot Reload)
- ✨ 自动检测 `config.ini` 文件变化
- 🔄 无需手动重启应用即可应用新配置
- 🎯 支持添加/删除/修改游戏配置
- ⚡ 重载速度快（通常 < 1 秒）
- 🛡️ 防止重复重载的锁机制

**使用示例**:
```bash
# 默认启用热重载
python main.py

# 禁用热重载（如需要）
python main.py --no-config-watch
```

**典型场景**:
- 添加新游戏到同步列表
- 修改游戏存档路径
- 调整同步策略参数
- 修改 Git 仓库配置

详见: [CONFIG_RELOAD_GUIDE.md](CONFIG_RELOAD_GUIDE.md)

### 🔧 改进

#### 配置管理
- 新增 `get_config_path()` 公开函数，获取配置文件路径
- 优化 `reload_config()` 函数，支持热重载场景

#### SyncApp 增强
- 新增 `enable_config_watch` 参数控制热重载开关
- 新增 `_load_config()` 方法统一配置加载逻辑
- 新增 `_restart_on_config_change()` 方法处理配置变更
- 保留命令行覆盖参数，重载时保持不变

#### 命令行参数
- 新增 `--no-config-watch` 参数禁用配置热重载

### 📚 文档

- 新增 `CONFIG_RELOAD_GUIDE.md` - 配置热重载完整指南
- 新增 `CHANGELOG.md` - 本更新日志
- 新增 `test_config_reload.py` - 热重载功能测试脚本

### 🐛 修复

- 无

---

## [v1.0.0] - 2025-12-15

### 🎉 首次发布

#### 核心功能

##### 游戏存档同步
- 📦 自动备份本地存档到本地目录
- ☁️ 使用 Git 同步存档到远程仓库
- 🔄 定时拉取远程更新
- 👀 实时监控本地存档变化并自动推送
- 🎮 支持多个游戏、多个存档位置

##### 配置管理
- 📝 INI 格式配置文件
- 🎯 支持游戏分组和索引
- 🎨 支持文件模式匹配（allow/deny）
- 🔧 命令行参数覆盖配置

##### Git 集成
- 🔐 支持 Token 认证（GitHub, GitLab 等）
- 🌿 自动分支管理
- 💪 强制推送和强制拉取
- 🔒 日志中自动脱敏 Token

##### 任务队列
- ⚡ 异步执行 Git 操作
- 🎯 唯一任务去重
- 📊 任务插入策略（tail/fixed）

##### 文件监控
- 👁️ 跨平台轮询监控
- 🔍 基于哈希的变化检测
- ⏱️ 可配置的防抖延迟
- 📁 支持多目录监控

##### 日志系统
- 📅 按日期分割日志
- 🗑️ 自动清理旧日志
- 🔒 线程安全写入
- 📊 结构化日志格式

### 🏗️ 代码重构

#### 模块化设计
- 每个文件只包含一个主要的类（单一职责原则）
- 清晰的职责分离（类/工具函数/工厂/管理器）
- 高内聚低耦合的模块结构

#### 模块列表
```
src/
├── sync_util/      # 同步核心模块
├── config_util/    # 配置管理模块
├── git_util/       # Git 操作模块
├── task_util/      # 任务队列模块
├── watcher_util/   # 文件监控模块
├── log_util/       # 日志管理模块
└── file_util/      # 文件工具模块
```

详见: [CODE_STRUCTURE.md](CODE_STRUCTURE.md)

### 📚 文档

- `README.md` - 项目说明
- `CODE_STRUCTURE.md` - 代码结构说明
- `QUICK_REFERENCE.md` - 快速参考指南
- `REFACTORING_NOTES.md` - 重构说明

### 🛠️ 开发工具

- `build_game_save_sync.bat` - Windows 构建脚本（PyInstaller）
- `test_imports.py` - 模块导入测试脚本

---

## 版本说明

版本号格式: `MAJOR.MINOR.PATCH`

- **MAJOR**: 重大功能更新或不兼容的 API 变更
- **MINOR**: 新增功能，向后兼容
- **PATCH**: 问题修复，向后兼容

## 即将推出 (Roadmap)

### v1.2.0 (计划中)
- [ ] GUI 界面
- [ ] 更多云存储后端支持（OneDrive, Dropbox）
- [ ] 存档冲突解决机制
- [ ] 加密存档支持

### v1.1.1 (计划中)
- [ ] 单元测试覆盖
- [ ] 性能优化
- [ ] 配置文件验证
- [ ] 更详细的错误提示

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**许可证**: MIT
**作者**: v_runxwang
**项目主页**: (待添加)
