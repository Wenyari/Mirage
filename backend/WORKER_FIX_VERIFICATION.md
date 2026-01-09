# Worker 应用上下文修复 - 快速验证

## ✅ 问题已修复

**错误信息：**
```
RuntimeError: Working outside of application context.
```

**修复文件：**
- `worker_gevent.py` - 在 `worker_wrapper` 方法中添加了 `with app.app_context():`

---

## 🚀 立即验证

### 1. 重启 Worker 容器

```bash
# 方式 1: 单独重启 Worker
docker-compose restart worker

# 方式 2: 重新构建并启动（如果有其他代码更改）
docker-compose up -d --build worker
```

### 2. 实时查看日志

```bash
# 实时查看 Worker 日志
docker-compose logs -f worker
```

### 3. 从前端创建测试任务

在前端创建一个任务（如 Sora 视频生成），观察日志输出：

**正常输出示例：**
```
2026-01-09 17:45:12 [INFO] [Worker-1] Processing task 12345 (active: 1/100)
2026-01-09 17:45:15 [INFO] Task 12345 completed
```

**不应该再出现：**
```
RuntimeError: Working outside of application context.
```

### 4. 检查任务状态

```bash
# 进入 MySQL
docker-compose exec mysql mysql -u sora_user -psora_password sora_platform

# 查询最近的任务
SELECT id, status, progress, fail_reason FROM tasks ORDER BY id DESC LIMIT 5;
```

**预期结果：**
- 任务状态正常流转：`pending` → `running` → `success`/`failed`
- `fail_reason` 不包含 "Working outside of application context"

---

## 📋 修复内容

### 修改前（worker_gevent.py 第 53-76 行）

```python
def worker_wrapper(self, payload, worker_id):
    """协程任务包装器"""
    task_id = payload.get('task_id', 'unknown')

    try:
        self.active_tasks += 1
        logger.info(f"Processing task {task_id}")

        # ❌ 没有应用上下文
        process_task(payload)  # RuntimeError!

        logger.info(f"Task {task_id} completed")
    except Exception as e:
        logger.error(f"Task {task_id} error: {str(e)}")
    finally:
        self.active_tasks -= 1
```

### 修改后（已修复）

```python
def worker_wrapper(self, payload, worker_id):
    """协程任务包装器"""
    task_id = payload.get('task_id', 'unknown')

    try:
        self.active_tasks += 1
        logger.info(f"Processing task {task_id}")

        # ✅ 每个协程单独创建应用上下文
        with app.app_context():
            process_task(payload)

        logger.info(f"Task {task_id} completed")
    except Exception as e:
        logger.error(f"Task {task_id} error: {str(e)}")
    finally:
        self.active_tasks -= 1
```

---

## 🔍 故障排查

### 如果修复后仍然报错

1. **确认代码已更新：**
   ```bash
   # 查看修改内容
   docker-compose exec worker cat /app/worker_gevent.py | grep -A 5 "with app.app_context"

   # 应该能看到第 68 行有 "with app.app_context():"
   ```

2. **强制重新构建：**
   ```bash
   # 停止所有容器
   docker-compose down

   # 删除旧镜像
   docker rmi mirage_backend

   # 重新构建并启动
   docker-compose up -d --build
   ```

3. **检查 Python 环境：**
   ```bash
   # 进入容器查看 Python 版本和依赖
   docker-compose exec worker python --version
   docker-compose exec worker pip show gevent
   ```

4. **查看完整错误堆栈：**
   ```bash
   docker-compose logs worker | grep -A 20 "RuntimeError"
   ```

---

## 📚 相关文档

- **详细技术说明：** `docs/flask-app-context-fix.md`
- **Docker 部署方案：** `DOCKER部署方案.md` (FAQ Q8)
- **快速启动指南：** `DOCKER_QUICKSTART.md`

---

## ✨ 技术要点

### 为什么需要这样修复？

1. **Flask 应用上下文的本质：**
   - Flask 使用线程本地存储（Thread-local）管理应用上下文
   - `db.engine.connect()` 需要访问 `current_app`，而这依赖应用上下文

2. **Gevent 协程池的特性：**
   - `gevent.pool.Pool.spawn()` 启动的子协程不会自动继承父协程的上下文
   - Gevent 的 `greenlet` 不是真正的线程，协程切换时不复制线程本地变量

3. **解决方案：**
   - 在每个子协程中单独创建 `with app.app_context():`
   - 确保每个协程都有独立的应用上下文

### 对比：不同 Worker 的上下文管理

| Worker 类型 | 文件 | 上下文管理 |
|------------|------|-----------|
| 单线程 | `worker.py` | 主循环创建一次，所有任务共享 |
| 多协程 | `worker_gevent.py` | **每个协程单独创建**（已修复） |
| Celery | N/A | Celery 自动管理 |

---

**修复完成时间：** 2026-01-09
**问题类型：** Flask 应用上下文 + Gevent 协程
**影响范围：** Docker 环境下的异步任务处理

---

**需要帮助？** 请查看 `docs/flask-app-context-fix.md` 获取完整技术细节。
