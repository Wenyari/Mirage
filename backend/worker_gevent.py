"""
Gevent协程版Worker - 支持高并发任务处理

特性：
- 单进程支持100+并发
- 内存占用低（每个协程~10KB）
- 零代码侵入，只需monkey patch

启动方式：
    python worker_gevent.py --workers 100

工作原理：
1. Gevent monkey patch让所有I/O操作变成非阻塞
2. 每个任务在独立协程中执行
3. 自动在I/O等待时切换到其他协程
"""
import sys
import argparse
import logging

# 【关键】必须在导入其他模块前进行monkey patch
from gevent import monkey
monkey.patch_all()

import gevent
from gevent.pool import Pool
import json
from worker import process_task, get_redis, KeyManager, app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Worker-%(worker_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class GeventWorker:
    """基于Gevent的多协程Worker"""

    def __init__(self, max_workers=100):
        """
        初始化Worker

        Args:
            max_workers: 最大并发协程数
        """
        self.max_workers = max_workers
        self.pool = Pool(max_workers)
        self.active_tasks = 0

    def worker_wrapper(self, payload, worker_id):
        """
        协程任务包装器，用于统计和错误处理

        Args:
            payload: 任务数据
            worker_id: 协程编号
        """
        task_id = payload.get('task_id', 'unknown')

        try:
            self.active_tasks += 1
            logger.info(f"[Worker-{worker_id}] Processing task {task_id} (active: {self.active_tasks}/{self.max_workers})")

            # 🔧 关键修复：每个协程都需要独立的应用上下文
            with app.app_context():
                # 调用原有的process_task函数（无需修改）
                process_task(payload)

            logger.info(f"[Worker-{worker_id}] Task {task_id} completed")

        except Exception as e:
            logger.error(f"[Worker-{worker_id}] Task {task_id} error: {str(e)}", exc_info=True)

        finally:
            self.active_tasks -= 1

    def run(self):
        """主循环：从队列取任务并分配给协程池"""
        logger.info("=" * 60)
        logger.info(f"Gevent Worker Started (Max Concurrency: {self.max_workers})")
        logger.info(f"Listening on queue: {KeyManager.QUEUE_RUNNABLE}")
        logger.info("=" * 60)

        worker_counter = 0

        # 注意：虽然这里有 app_context，但协程池中的子协程不会自动继承
        # 所以在 worker_wrapper 中也需要单独设置 app_context
        with app.app_context():
            while True:
                try:
                    # 阻塞式取任务（Gevent会自动切换到其他协程）
                    raw_task = get_redis().blpop(KeyManager.QUEUE_RUNNABLE, timeout=1)

                    if raw_task:
                        _, task_json = raw_task
                        payload = json.loads(task_json)
                        task_id = payload.get('task_id', 'unknown')

                        logger.info(f"Received task: {task_id} (queue size: {self.pool.free_count()}/{self.max_workers})")

                        # 分配给协程池执行（非阻塞）
                        worker_counter += 1
                        worker_id = worker_counter % 1000  # 循环使用编号

                        self.pool.spawn(self.worker_wrapper, payload, worker_id)

                    # 如果池已满，Gevent会自动阻塞等待

                except KeyboardInterrupt:
                    logger.info("Shutting down gracefully...")
                    logger.info(f"Waiting for {self.active_tasks} active tasks to complete...")

                    # 等待所有任务完成
                    self.pool.join(timeout=30)

                    logger.info("Worker stopped")
                    break

                except Exception as e:
                    logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
                    gevent.sleep(1)  # 避免错误循环


def main():
    """入口函数"""
    parser = argparse.ArgumentParser(description='Gevent协程Worker')
    parser.add_argument('--workers', type=int, default=100, help='最大并发协程数（默认100）')
    args = parser.parse_args()

    # 验证参数
    if args.workers < 1 or args.workers > 1000:
        logger.error("workers must be between 1 and 1000")
        sys.exit(1)

    # 启动Worker
    worker = GeventWorker(max_workers=args.workers)
    worker.run()


if __name__ == '__main__':
    main()
