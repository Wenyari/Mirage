# Flask 应用上下文问题修复说明

## 问题描述

在 Docker 环境中运行 `worker_gevent.py` 时，任务处理过程中出现以下错误：

```
RuntimeError: Working outside of application context.

This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context().
```

**错误堆栈：**
```python
File "/app/worker_gevent.py", line 68, in worker_wrapper
    process_task(payload)
File "/app/worker.py", line 166, in process_task
    result = query_sql(check_sql, {"task_id": task_id})
File "/app/worker.py", line 74, in query_sql
    with db.engine.connect() as conn:
         ^^^^^^^^^
RuntimeError: Working outside of application context.
```

---

## 根本原因

### Flask 应用上下文的特性

在 Flask 中，数据库操作（如 `db.engine.connect()`）需要在**应用上下文**中执行。应用上下文通过 `with app.app_context():` 创建。

### Gevent 协程池的特性

**关键问题：** Gevent 的协程池（`gevent.pool.Pool`）中启动的子协程**不会自动继承**父协程的应用上下文。

```python
# worker_gevent.py 的原始代码
def run(self):
    with app.app_context():  # ← 主协程有应用上下文
        while True:
            # ...
            self.pool.spawn(self.worker_wrapper, payload, worker_id)
            # ↑ 子协程没有应用上下文！
```

**为什么会这样？**

- **线程本地存储（Thread-local）：** Flask 使用线程本地存储（`werkzeug.local`）来管理应用上下文
- **Gevent 协程切换：** Gevent 的 `greenlet` 不是真正的线程，协程切换时不会自动复制线程本地变量
- **结果：** 子协程启动时，Flask 的 `current_app` 代理无法找到应用上下文，导致 `RuntimeError`

---

## 解决方案

在**每个协程**中单独创建应用上下文。

### 修复前（错误代码）

```python
def worker_wrapper(self, payload, worker_id):
    """协程任务包装器"""
    task_id = payload.get('task_id', 'unknown')

    try:
        self.active_tasks += 1
        logger.info(f"Processing task {task_id}")

        # ❌ 没有应用上下文！
        process_task(payload)  # 会报错

        logger.info(f"Task {task_id} completed")
    except Exception as e:
        logger.error(f"Task {task_id} error: {str(e)}")
    finally:
        self.active_tasks -= 1
```

### 修复后（正确代码）

```python
def worker_wrapper(self, payload, worker_id):
    """协程任务包装器"""
    task_id = payload.get('task_id', 'unknown')

    try:
        self.active_tasks += 1
        logger.info(f"Processing task {task_id}")

        # ✅ 每个协程单独创建应用上下文
        with app.app_context():
            process_task(payload)  # 现在有上下文了

        logger.info(f"Task {task_id} completed")
    except Exception as e:
        logger.error(f"Task {task_id} error: {str(e)}")
    finally:
        self.active_tasks -= 1
```

---

## 架构对比

### worker.py（单线程 Worker）

```python
def main():
    with app.app_context():  # ← 整个主循环有上下文
        while True:
            raw_task = get_redis().blpop(...)
            process_task(payload)  # ✅ 直接在当前线程执行，有上下文
```

**特点：**
- 单线程顺序执行
- 应用上下文在主循环中创建一次，所有任务共享

### worker_gevent.py（协程 Worker）

```python
def run(self):
    with app.app_context():  # ← 主协程有上下文
        while True:
            raw_task = get_redis().blpop(...)
            # ❌ 子协程不会继承父协程的上下文
            self.pool.spawn(self.worker_wrapper, payload)

def worker_wrapper(self, payload, worker_id):
    # ✅ 必须在子协程中单独创建上下文
    with app.app_context():
        process_task(payload)
```

**特点：**
- 多协程并发执行
- 每个协程需要独立的应用上下文

---

## 技术细节

### Flask 应用上下文的底层实现

Flask 使用 `werkzeug.local.LocalStack` 实现上下文管理：

```python
# Flask 内部实现（简化版）
from werkzeug.local import LocalStack

_app_ctx_stack = LocalStack()

def app_context():
    ctx = AppContext(app)
    _app_ctx_stack.push(ctx)
    try:
        yield ctx
    finally:
        _app_ctx_stack.pop()

# 访问 current_app 时
current_app = _app_ctx_stack.top.app
```

### Gevent Monkey Patch 的影响

`gevent.monkey.patch_all()` 会修改标准库的线程本地存储，但 Flask 的 `LocalStack` 在 Gevent 环境下的行为是：

- **主协程：** 可以正常访问上下文栈
- **子协程：** 启动时**不会复制**父协程的上下文栈
- **原因：** Gevent 的 `greenlet` 有独立的执行栈，但 Flask 的 `LocalStack` 绑定在操作系统线程级别

---

## 验证修复

### 1. 重启 Worker 容器

```bash
# 重启 Worker 容器以应用代码更改
docker-compose restart worker

# 查看日志确认启动成功
docker-compose logs -f worker
```

### 2. 从前端创建任务

在前端创建一个测试任务，观察日志输出：

```bash
# 查看 Worker 日志
docker-compose logs -f worker

# 正常输出应该类似：
# [Worker-1] Processing task 12345 (active: 1/100)
# Task 12345 completed
```

### 3. 检查数据库

```bash
# 进入 MySQL 查看任务状态
docker-compose exec mysql mysql -u sora_user -psora_password sora_platform

# 查询任务
SELECT id, status, progress, fail_reason FROM tasks ORDER BY id DESC LIMIT 5;
```

**预期结果：**
- 任务状态正常更新（`running` → `success` 或 `failed`）
- 不再出现 `RuntimeError` 错误

---

## 最佳实践

### 在 Worker 中使用 Flask 应用上下文的规则

1. **单线程/单进程 Worker：**
   ```python
   def main():
       with app.app_context():
           while True:
               process_task()  # ✅ 在主循环的上下文中
   ```

2. **多线程 Worker（threading.Thread）：**
   ```python
   def worker_thread():
       with app.app_context():  # ✅ 每个线程独立上下文
           process_task()

   threads = [Thread(target=worker_thread) for _ in range(10)]
   ```

3. **协程 Worker（gevent/asyncio）：**
   ```python
   def worker_coroutine():
       with app.app_context():  # ✅ 每个协程独立上下文
           process_task()

   pool.spawn(worker_coroutine)
   ```

4. **Celery Worker：**
   ```python
   @celery.task
   def process_task():
       # ✅ Celery 自动管理应用上下文
       db.session.query(...)
   ```

---

## 相关文件

| 文件 | 说明 | 修改内容 |
|------|------|----------|
| `worker_gevent.py` | Gevent 协程 Worker | 在 `worker_wrapper` 中添加 `with app.app_context():` |
| `worker.py` | 单线程 Worker | 无需修改（已在主循环中使用上下文） |

---

## 参考资料

- [Flask 官方文档 - Application Context](https://flask.palletsprojects.com/en/2.3.x/appcontext/)
- [Gevent 官方文档 - Monkey Patching](http://www.gevent.org/api/gevent.monkey.html)
- [Werkzeug Local - Thread-local Objects](https://werkzeug.palletsprojects.com/en/2.3.x/local/)

---

**修复完成时间：** 2026-01-09
**问题类型：** Flask 应用上下文 + Gevent 协程
**影响范围：** Docker 环境下的异步任务处理
