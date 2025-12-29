"""
RQ Worker 异步任务处理入口
这是后台"苦力"，负责从 Redis 队列中取任务并执行

启动方式:
    python worker.py

注意: Worker 需要在 Flask App 上下文中运行，否则无法访问数据库
"""
import redis
from rq import Worker, Queue, Connection
from app import create_app
from app.config import Config

# 创建 Flask 应用上下文
app = create_app()

# 要监听的队列列表 (优先级从高到低)
LISTEN_QUEUES = ['high_priority', 'default']


def main():
    """启动 Worker"""
    redis_conn = redis.from_url(Config.REDIS_URL)

    # 在 Flask 上下文中运行 Worker
    with app.app_context():
        with Connection(redis_conn):
            worker = Worker(list(map(Queue, LISTEN_QUEUES)))
            print(f'[Worker] Starting to listen on queues: {LISTEN_QUEUES}')
            worker.work()


if __name__ == '__main__':
    main()
