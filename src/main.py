"""
程序入口
- 解析命令行参数（允许覆盖 remote/token/branch）
- 启动主流程（备份/拉取/覆盖/推送/定时器/监控器）
"""
import argparse
from sync_util import SyncApp
from log_util import log

def main():
    parser = argparse.ArgumentParser(prog="game-save-sync")
    parser.add_argument("--remote", type=str, default=None, help="覆盖配置中的 Git 远程仓库地址")
    parser.add_argument("--token", type=str, default=None, help="覆盖配置中的 Git 访问令牌")
    parser.add_argument("--username", type=str, default=None, help="覆盖配置中的 Git 用户名")
    parser.add_argument("--branch", type=str, default=None, help="覆盖配置中的 Git 分支名")
    args = parser.parse_args()

    app = SyncApp(
        override_remote=args.remote,
        override_token=args.token,
        override_username=args.username,
        override_branch=args.branch
    )
    try:
        app.start()
        log("main_running")
        while True:
            import time
            time.sleep(3600)
    except KeyboardInterrupt:
        log("main_interrupt")
        app.stop()
    except Exception as e:
        log("main_error: {err}", err=str(e))
        try:
            app.stop()
        except Exception:
            pass

if __name__ == "__main__":
    main()
