import time
from pathlib import Path  # <--- 确保导入这个
from watchdog.observers import Observer
from src.utils import load_config, setup_logger
from src.core import FileOrganizer


def main():
    # 1. 初始化日志
    logger = setup_logger()
    logger.info("正在启动 ZenFile...")

    try:
        # 2. 加载配置
        config = load_config()

        # ⚠️ 这里从 json 读出来的是字符串，比如 "C:/Users/Downloads"
        watch_path_str = config["watch_dir"]

        # ✅ 关键修正：必须转成 Path 对象才能用 .exists()
        watch_path = Path(watch_path_str)

        logger.info(f"配置加载成功，监控目录: {watch_path}")

        # 检查文件夹是否存在
        if not watch_path.exists():
            logger.critical(f"❌ 错误：找不到文件夹 {watch_path}")
            return

        # 3. 启动核心服务
        event_handler = FileOrganizer(config, logger)
        observer = Observer()
        # watchdog 的 schedule 方法既可以传字符串，也可以传 Path 对象，这里传哪个都行
        observer.schedule(event_handler, str(watch_path), recursive=False)
        observer.start()

        logger.info("ZenFile 服务已就绪 (按 Ctrl+C 退出)")

        # 4. 保持运行
        while True:
            time.sleep(1)

    except FileNotFoundError as e:
        logger.critical(f"启动失败: {e}")
    except KeyboardInterrupt:
        observer.stop()
        logger.info("程序已停止")
    except Exception as e:
        # 打印详细错误信息，方便调试
        import traceback
        logger.critical(f"发生未知错误: {e}")
        logger.critical(traceback.format_exc())
    finally:
        if 'observer' in locals() and observer.is_alive():
            observer.join()


if __name__ == "__main__":
    main()