# 任务ID映射修复说明

## 问题描述

**严重Bug**：本地任务ID与上游API任务ID不一致，导致无法正确追踪任务进度和结果。

### 问题流程

1. ❌ TaskService 创建任务 → 生成本地UUID（如 `abc-123-def`）
2. ❌ Worker 提交到上游 → 上游返回上游ID（如 `upstream-456-xyz`）
3. ❌ Worker 轮询进度 → 使用上游ID查询
4. ❌ 数据库只存本地ID → **无法关联，任务状态永远无法更新**

## 解决方案

添加 `upstream_task_id` 字段存储上游API返回的任务ID，实现ID映射。

### 修复后的流程

1. ✅ TaskService 创建任务 → 生成本地UUID（`task.id`）
2. ✅ Worker 提交成功 → 保存上游ID到 `task.upstream_task_id`
3. ✅ Worker 轮询进度 → 使用 `upstream_task_id` 查询上游API
4. ✅ 更新本地任务 → 根据本地ID更新状态和进度

## 代码修改

### 1. Task 模型 (app/models/task.py)

**新增字段：**
```python
upstream_task_id = db.Column(db.String(255), nullable=True, index=True)  # 上游 API 返回的任务 ID
```

**to_dict() 方法新增返回：**
```python
'upstream_task_id': self.upstream_task_id
```

### 2. Worker (worker.py)

**提交成功后保存上游ID：**
```python
# 解析响应
response_data = resp.json()
task_uuid = response_data.get('id')

if not task_uuid:
    raise Exception("No task ID returned from API")

logger.info(f"Task {task_id} submitted successfully, upstream ID: {task_uuid}")

# 【关键】保存上游任务ID到数据库
task.upstream_task_id = task_uuid
db.session.commit()
```

**Redis进度存储（双键兼容）：**
```python
# 同时使用本地ID和上游ID存储进度，确保兼容性
get_redis().setex(f"task:progress:{task_id}", 86400, progress)
get_redis().setex(f"task:progress:upstream:{task_uuid}", 86400, progress)
```

## 数据库迁移

### 方式 1: 运行迁移脚本（推荐）

```bash
# 添加字段
python migrations/add_upstream_task_id.py

# 回滚（如需要）
python migrations/add_upstream_task_id.py downgrade
```

### 方式 2: 手动执行SQL

```sql
-- 添加字段
ALTER TABLE tasks ADD COLUMN upstream_task_id VARCHAR(255) NULL;

-- 添加索引
CREATE INDEX idx_upstream_task_id ON tasks(upstream_task_id);

-- 回滚（如需要）
DROP INDEX idx_upstream_task_id;
ALTER TABLE tasks DROP COLUMN upstream_task_id;
```

### 方式 3: 重新初始化数据库（开发环境）

```bash
# ⚠️ 会清空所有数据！
python init_db.py
```

## 验证修复

### 1. 检查数据库字段

```sql
-- 查看表结构
DESC tasks;

-- 应该看到 upstream_task_id 字段
-- | upstream_task_id | varchar(255) | YES  | MUL  | NULL    |       |
```

### 2. 测试任务提交

```bash
# 启动服务
python run.py

# 启动 Worker
python worker.py

# 提交测试任务（通过 API 或前端）
# 观察 Worker 日志应该看到：
# Task abc-123-def submitted successfully, upstream ID: upstream-456-xyz
```

### 3. 检查数据库记录

```sql
SELECT id, upstream_task_id, status, progress FROM tasks ORDER BY created_at DESC LIMIT 5;

-- 示例输出：
-- | id                | upstream_task_id      | status     | progress |
-- |-------------------|-----------------------|------------|----------|
-- | abc-123-def       | upstream-456-xyz      | processing | 45       |
```

### 4. 验证进度更新

```bash
# 查看 Redis 进度
redis-cli

> GET task:progress:abc-123-def
"45"

> GET task:progress:upstream:upstream-456-xyz
"45"
```

## API 响应变化

### 查询任务状态 (GET /api/tasks/{task_id})

**修复前：**
```json
{
    "id": "abc-123-def",
    "status": "processing",
    "progress": 0,  // ❌ 永远是0，无法更新
    ...
}
```

**修复后：**
```json
{
    "id": "abc-123-def",
    "upstream_task_id": "upstream-456-xyz",  // ✅ 新增
    "status": "processing",
    "progress": 45,  // ✅ 实时更新
    ...
}
```

## 数据字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | String(36) | 本地任务ID（UUID） | `abc-123-def-456` |
| `upstream_task_id` | String(255) | 上游API任务ID | `upstream-789-xyz` |

**为什么需要两个ID？**

1. **本地ID (`id`)**：
   - 用户看到的任务ID
   - 前端轮询状态使用
   - 数据库主键
   - 订单关联、权限验证

2. **上游ID (`upstream_task_id`)**：
   - Worker 轮询上游API使用
   - 上游系统的唯一标识
   - 与上游API对接必需

## 回滚计划

如果修复出现问题，可以回滚：

```bash
# 1. 停止所有服务
# 2. 运行回滚脚本
python migrations/add_upstream_task_id.py downgrade

# 3. 恢复旧版本代码
git checkout HEAD~1 app/models/task.py
git checkout HEAD~1 worker.py
```

## 常见问题

### Q: 历史任务怎么办？
A: 历史任务的 `upstream_task_id` 为 `NULL`，不影响查询。只有新任务才会填充此字段。

### Q: 如果上游API不返回ID怎么办？
A: Worker 会抛出异常："No task ID returned from API"，任务标记为失败并退款。

### Q: Redis 为什么要存两个键？
A:
- `task:progress:{本地ID}` - 供 TaskService 查询使用
- `task:progress:upstream:{上游ID}` - 备用，便于调试

### Q: 性能影响？
A:
- 新增一个字段，存储开销可忽略不计
- 新增一个索引，查询性能略有提升
- Worker 多一次 commit 操作，影响极小

## 总结

这个修复解决了任务进度无法更新的严重问题，是**必须立即部署**的关键修复。

✅ **修复内容**：
- 添加 `upstream_task_id` 字段
- Worker 保存上游任务ID
- 支持双ID系统（本地ID + 上游ID）

✅ **影响范围**：
- 所有新提交的任务
- 不影响历史数据

✅ **部署步骤**：
1. 运行数据库迁移
2. 更新代码
3. 重启 Worker 和 API 服务
