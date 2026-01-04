# 任务 Pending 问题排查指南

## 问题现象
任务提交后一直处于 `pending` 状态，没有分配 API 密钥，没有进入执行队列。

## 排查步骤

### 1. 检查 API 密钥是否启用

**问题根源：** init_db.py 创建的密钥默认 status=0（禁用状态）

**快速修复：**
```bash
# 方法 1: 使用修复脚本
python fix_keys.py

# 方法 2: 直接 SQL
mysql -u root -p
USE mirage_db;
UPDATE api_keys SET status=1 WHERE model='sora-2';
SELECT id, model, status FROM api_keys;
```

**验证：**
```bash
python check_system.py
```

应该看到：
```
1. API 密钥状态:
   总数: 1
   - ID: 1
     模型: sora-2
     状态: ✓ 启用  # ← 确保这里是"启用"
     并发限制: 2
```

---

### 2. 确保所有进程都在运行

**需要 3 个终端同时运行：**

| 终端 | 进程 | 作用 | 启动命令 |
|------|------|------|----------|
| 1 | run.py | Flask API 服务器 | `python run.py` |
| 2 | scheduler.py | 定期分配密钥 | `python scheduler.py` |
| 3 | worker.py | 执行任务 | `python worker.py` |

**验证方法：**
- 检查 scheduler.py 终端输出，应该看到：
  ```
  AIGC Scheduler Started
  Dispatching interval: 5 seconds
  Watchdog interval: 60 seconds
  ```

- 检查 worker.py 终端输出，应该看到：
  ```
  AIGC Worker Started
  Listening on queue: queue:runnable
  ```

**如果缺少任何一个进程，任务就会卡在 pending 状态！**

---

### 3. 检查用户等级是否符合模型要求

**查询模型配置：**
```sql
SELECT model, allowed_tiers FROM model_configs WHERE model='sora-2';
```

**查询用户等级：**
```sql
SELECT id, email, level FROM users WHERE id=<your_user_id>;
```

**检查：**
- sora-2 要求：`["T3", "T4", "T5"]`
- 如果你的用户是 T1 (level=1)，会被拦截
- 需要将用户升级到 T3：
  ```sql
  UPDATE users SET level=3 WHERE id=<your_user_id>;
  ```

---

### 4. 诊断特定任务

**使用诊断脚本：**
```bash
python diagnose.py 0dc37ed8-4f2f-440e-bbae-57b4f5ae10c8
```

**脚本会检查：**
- ✓ 任务是否存在
- ✓ 用户信息
- ✓ 模型配置
- ✓ API 密钥状态
- ✓ Redis 队列状态
- ✓ 任务是否在队列中

---

## 常见问题

### Q1: 启用密钥后任务还是 pending？
**A:** 检查 scheduler.py 是否在运行：
```bash
# 如果没运行，启动它
python scheduler.py
```

### Q2: scheduler 和 worker 都在运行，任务还是 pending？
**A:** 检查用户等级是否符合模型要求：
```sql
-- 临时升级用户等级到 T3
UPDATE users SET level=3 WHERE id=2;
```

### Q3: 如何查看 Redis 队列内容？
**A:** 使用 Redis CLI：
```bash
redis-cli

# 查看队列长度
LLEN queue:waiting:vip
LLEN queue:waiting:normal
LLEN queue:runnable

# 查看队列内容（不删除）
LRANGE queue:waiting:normal 0 -1
```

### Q4: 任务卡住了，如何重新调度？
**A:** 手动触发调度：
```python
from app import create_app
from app.services.key_manager import KeyManager

app = create_app()
with app.app_context():
    dispatched = KeyManager.dispatch_waiting_tasks()
    print(f"已分配 {dispatched} 个任务")
```

---

## 完整修复流程（推荐）

```bash
# 1. 启用所有 API 密钥
python fix_keys.py

# 2. 检查系统状态
python check_system.py

# 3. 启动所有进程（3 个终端）
# 终端 1
python run.py

# 终端 2
python scheduler.py

# 终端 3
python worker.py

# 4. 提交测试任务
# 在浏览器或 Postman 中提交任务

# 5. 观察日志
# - run.py: 看到任务创建日志
# - scheduler.py: 看到任务分配日志
# - worker.py: 看到任务执行日志
```

---

## 日志示例（正常流程）

**run.py (任务提交):**
```
[2026-01-04 22:30:00] INFO - Task abc-123 created, status: pending
[2026-01-04 22:30:00] INFO - Task enqueued to queue:waiting:normal
```

**scheduler.py (密钥分配):**
```
[2026-01-04 22:30:05] INFO - Dispatching waiting tasks...
[2026-01-04 22:30:05] INFO - Found task abc-123 in normal queue
[2026-01-04 22:30:05] INFO - Allocated key ID 1 for task abc-123
[2026-01-04 22:30:05] INFO - Task abc-123 moved to queue:runnable
```

**worker.py (任务执行):**
```
[2026-01-04 22:30:06] INFO - Received task: abc-123
[2026-01-04 22:30:06] INFO - Processing task abc-123 with key 1
[2026-01-04 22:30:06] INFO - Submitting task to https://ai.t8star.cn/v2/videos/generations
[2026-01-04 22:30:07] INFO - Task abc-123 submitted successfully, upstream ID: upstream-xyz
[2026-01-04 22:30:10] INFO - Task abc-123 status: RUNNING, progress: 10%
[2026-01-04 22:30:13] INFO - Task abc-123 status: RUNNING, progress: 35%
...
[2026-01-04 22:31:00] INFO - Task abc-123 completed successfully
```

如果看不到这些日志，说明对应的进程没有正常工作。

---

## 总结

**任务 pending 的 3 大原因：**
1. ❌ API 密钥禁用（status=0）
2. ❌ scheduler.py 没运行
3. ❌ 用户等级不符合模型要求

**解决办法：**
1. ✓ 运行 `python fix_keys.py` 启用密钥
2. ✓ 确保 3 个进程都在运行（run.py, scheduler.py, worker.py）
3. ✓ 检查用户等级是否符合 `model_configs.allowed_tiers`
