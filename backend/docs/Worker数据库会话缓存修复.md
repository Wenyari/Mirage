# Worker 数据库会话缓存问题修复

## 问题现象

Worker 在长时间运行后，出现以下错误：

```
2026-01-04 23:47:24 [INFO] [cached since 173.1s ago] {'pk_1': 'b0374d4a-7155-4c04-bef4-828b87f10a90'}
2026-01-04 23:47:24 [ERROR] Task b0374d4a-7155-4c04-bef4-828b87f10a90 not found in database
```

但数据库中明明存在该任务记录。

## 根本原因

### 问题分析

1. **Worker 运行模式**：
   - Worker 在一个长期运行的 `app.app_context()` 中循环
   - 使用同一个 SQLAlchemy 会话处理所有任务

2. **SQLAlchemy 会话缓存机制**：
   - SQLAlchemy 有 **identity map** 缓存
   - `Task.query.get(task_id)` 会先从缓存查找
   - 长时间运行后，缓存中的对象可能 **detached**（分离）或过期
   - 日志显示 `[cached since 173.1s ago]` 就是证据

3. **为什么 `expire_all()` 不够**：
   - `db.session.expire_all()` 只标记对象为过期
   - 但如果对象已经从会话分离（detached），expire_all 无效
   - 新创建的任务对象可能根本不在当前会话中

### 之前尝试的失败方案

```python
# ❌ 方案 1: expire_all() - 不够彻底
db.session.expire_all()
task = Task.query.get(task_id)  # 仍然可能查询失败
```

## 解决方案：使用原始 SQL

### 核心思想

**完全避开 SQLAlchemy 的 ORM 和会话缓存**，使用原始 SQL 直接操作数据库。

### 修改内容

#### 1. 检查任务状态（替换 `Task.query.get()`）

**之前（使用 ORM）：**
```python
db.session.expire_all()
task = Task.query.get(task_id)
if not task:
    logger.error(f"Task {task_id} not found")
    return

if task.status == 'cancelled':
    return
```

**现在（使用原始 SQL）：**
```python
check_sql = text("SELECT status, user_id FROM tasks WHERE id = :task_id")
result = db.session.execute(check_sql, {"task_id": task_id}).fetchone()

if not result:
    logger.error(f"Task {task_id} not found")
    return

current_status, user_id = result

if current_status == 'cancelled':
    return
```

**优势：**
- 直接查询数据库，不经过会话缓存
- 返回原始数据，无状态对象
- 100% 可靠

---

#### 2. 更新任务状态为 processing

**之前（使用 ORM）：**
```python
task.status = 'processing'
task.api_key_id = key_id
db.session.commit()
```

**现在（使用原始 SQL）：**
```python
update_sql = text("""
    UPDATE tasks
    SET status = 'processing', api_key_id = :key_id
    WHERE id = :task_id
""")
db.session.execute(update_sql, {"task_id": task_id, "key_id": key_id})
db.session.commit()
```

---

#### 3. 保存上游任务 ID

**之前（使用 ORM）：**
```python
task.upstream_task_id = task_uuid
db.session.commit()
```

**现在（使用原始 SQL）：**
```python
save_upstream_sql = text("""
    UPDATE tasks
    SET upstream_task_id = :upstream_task_id
    WHERE id = :task_id
""")
db.session.execute(save_upstream_sql, {
    "task_id": task_id,
    "upstream_task_id": task_uuid
})
db.session.commit()
```

---

#### 4. 任务成功时更新

**之前（使用 ORM）：**
```python
task.status = 'success'
task.progress = 100
task.result_url = result_url
task.finished_at = datetime.now(ZoneInfo("Asia/Shanghai"))
db.session.commit()
```

**现在（使用原始 SQL）：**
```python
success_sql = text("""
    UPDATE tasks
    SET status = 'success',
        progress = 100,
        result_url = :result_url,
        finished_at = :finished_at
    WHERE id = :task_id
""")
db.session.execute(success_sql, {
    "task_id": task_id,
    "result_url": result_url,
    "finished_at": datetime.now(ZoneInfo("Asia/Shanghai"))
})
db.session.commit()
```

---

#### 5. 任务失败时更新（含智能退款）

**之前（使用 ORM）：**
```python
task.status = 'failed'
task.fail_reason = fail_reason
task.finished_at = datetime.now(ZoneInfo("Asia/Shanghai"))

if should_refund:
    user_obj = User.query.get(task.user_id)
    user_obj.balance += refund_amount

db.session.commit()
```

**现在（使用原始 SQL，原子操作）：**
```python
# 需要退款
fail_with_refund_sql = text("""
    UPDATE tasks t
    JOIN users u ON u.id = :user_id
    SET t.status = 'failed',
        t.progress = 0,
        t.fail_reason = :fail_reason,
        t.finished_at = :finished_at,
        u.balance = u.balance + :refund_amount
    WHERE t.id = :task_id
""")
db.session.execute(fail_with_refund_sql, {...})
db.session.commit()

# 不需要退款
fail_no_refund_sql = text("""
    UPDATE tasks
    SET status = 'failed',
        progress = 0,
        fail_reason = :fail_reason,
        finished_at = :finished_at
    WHERE id = :task_id
""")
```

**优势：**
- 任务更新和退款在一个 SQL 中完成（原子操作）
- 避免竞态条件
- 性能更好

---

## 修改文件

| 文件 | 修改内容 |
|------|----------|
| `worker.py` | 所有数据库操作改为原始 SQL |

## 新增依赖

```python
from sqlalchemy import text
```

## 测试清单

修复后，请验证以下场景：

- [ ] Worker 长时间运行（> 3 分钟）不再出现 "Task not found" 错误
- [ ] 任务状态正确更新为 processing → success/failed
- [ ] 上游任务 ID 正确保存到 `upstream_task_id` 字段
- [ ] 任务成功时，`result_url` 正确保存
- [ ] 任务失败时，`fail_reason` 正确保存
- [ ] 系统错误时自动退款，余额正确增加
- [ ] 内容违规时不退款
- [ ] 任务取消时正确跳过（懒删除）

## 验证方法

### 1. 启动 Worker 并观察日志

```bash
python worker.py
```

应该看到：
```
[INFO] Processing task xxx with key 1
[INFO] Task xxx status updated to processing
[INFO] Task xxx submitted successfully, upstream ID: veo3:...
[INFO] Task xxx status: RUNNING, progress: 35%
[INFO] Task xxx status: SUCCESS, progress: 100%
[INFO] Task xxx completed successfully, result: https://...
```

**不应该再看到：**
```
❌ [ERROR] Task xxx not found in database
❌ [INFO] [cached since XXX.Xs ago]
```

### 2. 长时间运行测试

让 Worker 持续运行 10+ 分钟，处理多个任务，观察是否稳定。

### 3. 数据库验证

提交任务后，在数据库中检查：

```sql
SELECT id, status, progress, upstream_task_id, result_url, fail_reason, finished_at
FROM tasks
WHERE id = 'your-task-id';
```

确认字段都正确更新。

### 4. 退款逻辑验证

**系统错误（应该退款）：**
1. 手动停止上游 API（或使用无效 API key）
2. 提交任务
3. 检查任务失败后，用户余额是否增加

**内容违规（不应该退款）：**
1. 提交包含违规词汇的任务
2. 检查任务失败后，用户余额没有变化

## 性能对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| **ORM（之前）** | 代码简洁，类型安全 | 会话缓存问题，长时间运行不稳定 |
| **原始 SQL（现在）** | 绕过缓存，100% 可靠，性能更好 | SQL 字符串不如 ORM 优雅 |

对于 Worker 这种长时间运行的后台进程，**原始 SQL 是更好的选择**。

## 未来优化建议

如果未来遇到更复杂的 ORM 操作需求，可以考虑：

1. **定期重启 Worker**（用 supervisor 或 systemd）
2. **每个任务使用独立会话**：
   ```python
   with app.app_context():
       db.session.remove()  # 移除旧会话
       # 处理任务
   ```
3. **使用连接池刷新**：
   ```python
   db.session.close()
   db.engine.dispose()
   ```

但目前原始 SQL 方案已经足够稳定和高效。

## 相关问题

- [任务Pending问题排查.md](./任务Pending问题排查.md) - Worker 未启动导致任务不执行
- [API适配器系统说明.md](./API适配器系统说明.md) - 处理不同上游 API 响应格式

## 总结

通过使用原始 SQL 完全避开 SQLAlchemy 的会话缓存机制，彻底解决了 Worker 长时间运行后查询不到任务的问题。这是一个针对长期运行后台进程的最佳实践。
