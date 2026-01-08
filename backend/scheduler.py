"""
定时维护任务调度器
负责运行密钥池的后台维护任务

启动方式:
    python scheduler.py

维护任务：
1. 统计同步 (每 5 分钟): 将 Redis 中的统计数据同步到 MySQL
2. 看门狗 (每 1 分钟): 检测并修复队列死锁
3. 任务清理 (每天凌晨 2 点): 清理超过 3 天的已完成任务
"""
import time
import logging
import schedule
from app import create_app
from app.services.key_manager import KeyManager
from app.services.task_service import TaskService

# 创建 Flask 应用上下文
app = create_app()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sync_stats_job():
    """统计同步任务"""
    logger.info("Running stats sync job...")
    with app.app_context():
        try:
            synced_count = KeyManager.sync_stats_to_db()
            logger.info(f"Stats sync completed: {synced_count} keys updated")
        except Exception as e:
            logger.error(f"Stats sync failed: {str(e)}", exc_info=True)


def watchdog_job():
    """看门狗任务"""
    logger.info("Running watchdog job...")
    with app.app_context():
        try:
            dispatched = KeyManager.watchdog()
            if dispatched > 0:
                logger.info(f"Watchdog recovered {dispatched} stuck tasks")
        except Exception as e:
            logger.error(f"Watchdog failed: {str(e)}", exc_info=True)


def cleanup_tasks_job():
    """任务清理任务"""
    logger.info("Running task cleanup job...")
    with app.app_context():
        try:
            result = TaskService.cleanup_old_tasks(days=3)
            logger.info(
                f"Task cleanup completed: {result['deleted']} tasks and "
                f"{result['deleted_files']} files deleted"
            )
            if result['errors']:
                logger.warning(f"Cleanup encountered {len(result['errors'])} errors")
        except Exception as e:
            logger.error(f"Task cleanup failed: {str(e)}", exc_info=True)


def main():
    """主循环"""
    logger.info("=" * 60)
    logger.info("AIGC Scheduler Started")
    logger.info("=" * 60)

    # 检查 Redis 连接
    with app.app_context():
        redis_client = KeyManager._get_redis()
        if redis_client is None:
            logger.error("Redis client is not initialized. Please check Redis configuration.")
            return
        else:
            logger.info("Redis client connected successfully")

    logger.info("Scheduled jobs:")
    logger.info("  - Stats sync:     Every 5 minutes")
    logger.info("  - Watchdog:       Every 1 minute")
    logger.info("  - Task cleanup:   Daily at 02:00")
    logger.info("=" * 60)

    # 注册定时任务
    schedule.every(5).minutes.do(sync_stats_job)
    schedule.every(1).minutes.do(watchdog_job)
    schedule.every().day.at("02:00").do(cleanup_tasks_job)

    # 启动时立即执行一次
    logger.info("Running initial jobs...")
    sync_stats_job()
    watchdog_job()

    # 主循环
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler shutting down...")


if __name__ == '__main__':
    main()
