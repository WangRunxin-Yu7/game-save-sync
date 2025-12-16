"""
测试配置文件热重载功能

使用方法:
1. 启动此脚本
2. 修改 data/config.ini 文件（例如添加新游戏）
3. 观察日志输出，应该看到配置重新加载和应用重启的日志
"""
import sys
import time
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sync_util import SyncApp
from log_util import log

def main():
    print("=" * 60)
    print("配置文件热重载测试")
    print("=" * 60)
    print()
    print("应用正在启动，配置文件热重载功能已启用...")
    print("提示: 修改 data/config.ini 文件，应用将自动重新加载配置")
    print("按 Ctrl+C 退出")
    print("=" * 60)
    print()
    
    # 创建应用（启用配置监控）
    app = SyncApp(enable_config_watch=True)
    
    try:
        app.start()
        log("test_app_running: config_watch=enabled")
        print("\n✅ 应用已启动，正在监控配置文件变化...")
        print("   配置文件路径: data/config.ini")
        print("   请尝试修改配置文件（添加游戏、修改路径等）\n")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n正在停止应用...")
        log("test_app_interrupt")
        app.stop()
        print("✅ 应用已停止")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        log("test_app_error: err={err}", err=str(e))
        try:
            app.stop()
        except Exception:
            pass

if __name__ == "__main__":
    main()
