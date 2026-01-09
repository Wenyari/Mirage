# ApiKey 一对多改为多对多关系改造计划

## 改造目标

将 `ApiKey` 与 `Model` 的关系从 **一对多**（一个密钥对应一个模型）改为 **多对多**（一个密钥可服务多个模型）。

**示例场景**：同一个 OpenAI API Key（如 `sk-proj-xxx`）可以同时支持 `gpt-4`、`gpt-4-turbo`、`gpt-4o` 等多个模型。

---

## 数据库变更

### 1. 新建关联表 `api_key_models`

```sql
CREATE TABLE api_key_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    api_key_id INT NOT NULL,
    model VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE,
    FOREIGN KEY (model) REFERENCES models(`key`) ON DELETE CASCADE,

    UNIQUE KEY uk_key_model (api_key_id, model),
    INDEX idx_model (model),              -- 核心查询索引
    INDEX idx_api_key_id (api_key_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**关键设计**：
- `uk_key_model`：防止重复关联 + 快速查询密钥支持的模型
- `idx_model`：**核心索引**，`allocate_key(model)` 高频查询"支持该模型的所有密钥"

### 2. 修改 `api_keys` 表

```sql
-- 删除旧索引
DROP INDEX idx_model_status ON api_keys;

-- 删除 model 字段
ALTER TABLE api_keys DROP COLUMN model;

-- 新建索引
CREATE INDEX idx_status ON api_keys(status);
```

### 3. 数据迁移

**迁移脚本**：`F:\Mirage\backend\migrations\convert_apikey_to_many_to_many.py`

```bash
# 升级
python migrations/convert_apikey_to_many_to_many.py

# 回滚（如果出错）
python migrations/convert_apikey_to_many_to_many.py downgrade
```

**迁移逻辑**：
1. 创建 `api_key_models` 表
2. 将 `api_keys.model` 的数据迁移到关联表：
   ```sql
   INSERT INTO api_key_models (api_key_id, model)
   SELECT id, model FROM api_keys WHERE model IS NOT NULL;
   ```
3. 删除旧索引 `idx_model_status`
4. 删除 `api_keys.model` 字段

---

## 代码改造范围

### 1. 数据模型层 (`app/models/model.py`)

#### 修改 `ApiKey` 类（第 91-143 行）

**关键变更**：
```python
# 删除
model = db.Column(db.String(50), db.ForeignKey('models.key'), nullable=False)

# 新增多对多关系
models = db.relationship(
    'Model',
    secondary='api_key_models',
    backref=db.backref('api_keys', lazy='dynamic'),
    lazy='select'
)

# 修改索引
__table_args__ = (
    db.Index('idx_status', 'status'),  # 移除 idx_model_status
    db.Index('idx_weight', 'weight'),
)

# 修改 to_dict() 方法
def to_dict(self, include_secret=False):
    result = {
        'models': [m.key for m in self.models],  # 改为模型列表
        # ... 其他字段
    }
```

#### 新建关联表模型（可选，显式管理）

```python
class ApiKeyModel(db.Model):
    """API密钥与模型关联表"""
    __tablename__ = 'api_key_models'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False)
    model = db.Column(db.String(50), db.ForeignKey('models.key', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('api_key_id', 'model', name='uk_key_model'),
        db.Index('idx_model', 'model'),
        db.Index('idx_api_key_id', 'api_key_id'),
    )
```

### 2. 密钥分配器 (`app/services/key_manager.py`)

#### 修改 `allocate_key` 方法（第 33-84 行）

**核心变更**：将 `filter_by(model=model)` 改为 JOIN 查询

```python
@classmethod
def allocate_key(cls, model: str):
    from app.models.model import Model

    # 修改前：
    # candidates = ApiKey.query.filter_by(model=model, status=1).all()

    # 修改后：通过 JOIN 多对多关联表查询
    candidates = db.session.query(ApiKey)\
        .join(ApiKey.models)\
        .filter(
            Model.key == model,
            ApiKey.status == 1
        )\
        .all()

    # 后续逻辑保持不变（熔断过滤、权重选择、并发控制）
    # ...
```

#### 修改 `get_key_status` 方法

```python
return {
    'models': [m.key for m in key_obj.models],  # 改为列表
    # ... 其他字段
}
```

### 3. 密钥管理服务 (`app/services/admin/key_service.py`)

#### 所有函数的参数和逻辑调整

| 函数 | 主要变更 |
|------|---------|
| `get_key_list(model_filter)` | 支持逗号分隔多模型筛选：`query.join(ApiKey.models).filter(Model.key.in_(models))` |
| `create_key(models, ...)` | 参数从单个 `model` 改为列表 `models`，验证所有模型存在性，设置 `api_key.models = model_objs` |
| `batch_create_keys(models, ...)` | 同上，所有批量创建的密钥关联相同的模型列表 |
| `update_key(key_id, models=None, ...)` | 新增 `models` 参数，允许修改密钥关联的模型列表 |
| `delete_key(key_id)` | 无需改动（级联删除由外键处理） |
| `get_key_stats()` | 统计逻辑改为 JOIN 查询：`db.session.query(ApiKey).join(ApiKey.models).filter(Model.key == model.key)` |

**示例：`create_key` 改造**

```python
def create_key(models, api_base, key_secret, max_concurrency=3, weight=10):
    # 验证 models 是非空列表
    if not isinstance(models, list) or not models:
        raise ValueError("models must be a non-empty list")

    # 验证所有模型是否存在
    model_objs = Model.query.filter(Model.key.in_(models)).all()
    found_models = {m.key for m in model_objs}
    missing_models = set(models) - found_models

    if missing_models:
        raise ValueError(f"Models not found: {', '.join(missing_models)}")

    # 创建密钥（不再设置 model 字段）
    api_key = ApiKey(
        api_base=api_base,
        key_secret=key_secret,
        max_concurrency=max_concurrency,
        weight=weight,
        status=1
    )

    # 关联模型
    api_key.models = model_objs

    db.session.add(api_key)
    db.session.commit()

    # 初始化 Redis
    redis_client.set(f"pool:usage:{api_key.id}", 0)

    return api_key.to_dict(include_secret=False)
```

### 4. API 接口层 (`app/api/admin/keys.py`)

#### 创建接口（第 63-137 行）

**请求体变更**：
```json
{
    "models": ["gpt-4", "gpt-4-turbo"],  // 改为数组
    "api_base": "https://api.openai.com/v1",
    "key_secret": "sk-proj-abc123...",
    "max_concurrency": 3,
    "weight": 10
}
```

**响应体变更**：
```json
{
    "code": 0,
    "data": {
        "id": 1,
        "models": ["gpt-4", "gpt-4-turbo"],  // 改为数组
        "api_base": "...",
        // ... 其他字段
    }
}
```

#### 批量创建接口（第 143-228 行）

同上，`model` 参数改为 `models` 数组。

#### 更新接口（第 234-289 行）

**新增可选参数**：
```json
{
    "models": ["gpt-4", "gpt-4-turbo"],  // 可选，修改关联的模型列表
    "max_concurrency": 5,
    "weight": 20,
    "status": 1
}
```

#### 查询接口（第 24-57 行）

无需修改路由代码，响应会自动包含 `models` 数组（因为 `to_dict()` 已改）。

---

## 实施步骤

### 阶段 1：数据库迁移（需停机）

```bash
# 1. 备份数据库
mysqldump -u root -p mirage_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 执行迁移脚本
python migrations/convert_apikey_to_many_to_many.py

# 3. 验证数据完整性
# 检查所有密钥都有关联
SELECT ak.id, COUNT(akm.id) as model_count
FROM api_keys ak
LEFT JOIN api_key_models akm ON ak.id = akm.api_key_id
GROUP BY ak.id
HAVING model_count = 0;  -- 应返回空结果

# 4. 如果出错，立即回滚
python migrations/convert_apikey_to_many_to_many.py downgrade
```

### 阶段 2：代码部署（可热更新）

```bash
# 1. 更新代码
git pull origin main

# 2. 重启服务
systemctl restart mirage-backend
```

---

## 关键文件清单

### 必须修改的文件

| 文件路径 | 修改内容 | 关键行数 |
|---------|---------|---------|
| `app/models/model.py` | 移除 `model` 字段，添加多对多 `models` relationship | 91-143 |
| `app/services/key_manager.py` | `allocate_key` 改为 JOIN 查询 | 33-84 |
| `app/services/admin/key_service.py` | 所有 CRUD 函数改为处理模型列表 | 全文 |
| `app/api/admin/keys.py` | 接口参数和响应改为 `models` 数组 | 63-289 |
| `docs/数据库表设计.md` | 更新表结构说明 | 160-195 |

### 新建的文件

| 文件路径 | 用途 |
|---------|------|
| `migrations/convert_apikey_to_many_to_many.py` | 数据迁移脚本（升级/回滚） |

---

## 风险与注意事项

### 1. 性能风险

**风险**：JOIN 查询可能比 `filter_by` 慢

**缓解措施**：
- 确保 `idx_model` 索引已创建
- 监控 `allocate_key` 的响应时间
- 考虑添加 Redis 缓存层缓存"模型→密钥ID集合"映射

### 2. 数据一致性风险

**风险**：迁移过程中数据丢失或损坏

**缓解措施**：
- 迁移前必须备份数据库
- 迁移脚本使用事务（如果可能）
- 迁移后验证所有密钥都有关联

### 3. 前端兼容性风险

**风险**：API 响应格式变化（`model` → `models`）

**解决方案**：
- 前端同步更新代码
- 或在 API 层添加适配层（兼容旧格式）

### 4. 回滚风险

**风险**：回滚会丢失多模型关联（只保留第一个模型）

**注意**：如果已经创建了新的多模型密钥，回滚后只会保留第一个关联的模型。

---

## 性能优化建议（可选）

### Redis 缓存层

缓存"模型→密钥ID集合"映射，减少数据库查询：

```python
def allocate_key_cached(model: str):
    cache_key = f"model:keys:{model}"
    cached_ids = redis_client.smembers(cache_key)

    if cached_ids:
        candidates = ApiKey.query.filter(ApiKey.id.in_(cached_ids), ApiKey.status == 1).all()
    else:
        # 缓存未命中，查询数据库
        candidates = db.session.query(ApiKey)\
            .join(ApiKey.models)\
            .filter(Model.key == model, ApiKey.status == 1)\
            .all()

        # 更新缓存
        if candidates:
            redis_client.sadd(cache_key, *[k.id for k in candidates])
            redis_client.expire(cache_key, 300)  # 5分钟过期

    # ... 后续逻辑
```

### 数据库索引优化

如果密钥数量 > 10万，考虑添加覆盖索引：

```sql
CREATE INDEX idx_model_key_id ON api_key_models(model, api_key_id);
```

---

## 验收标准

- ✅ 数据库迁移成功，所有密钥都有关联
- ✅ 可以创建支持多个模型的密钥
- ✅ 密钥分配逻辑正常工作
- ✅ API 接口正确返回 `models` 数组
- ✅ 现有功能未受影响（回归测试通过）
- ✅ 文档已更新
