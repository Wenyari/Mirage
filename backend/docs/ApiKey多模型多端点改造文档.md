# ApiKey 多模型多端点改造文档

## 改造背景

在之前的设计中，一个 API Key 虽然可以关联多个模型（多对多关系），但所有模型共享同一个 `api_base` 端点地址。这在某些场景下存在限制：

**问题场景**：
- t8star 的同一个 API Key 支持多种服务：
  - 视频生成：`https://ai.t8star.cn/v2/videos/generations`
  - 图片生成：`https://ai.t8star.cn/v1/images/generations`
  - 图片编辑：`https://ai.t8star.cn/v1/images/edits`
- 之前的设计中，`ApiKey.api_base` 只能设置一个值，无法为不同模型指定不同的端点

**解决方案**：
将 `api_base` 从 `ApiKey` 表移到 `api_key_models` 关联表，让每个 (密钥, 模型) 组合有独立的端点配置。

---

## 数据库变更

### 1. 表结构变更

#### `api_key_models` 表（关联表）
**新增字段**：
- `api_base` VARCHAR(512) NOT NULL DEFAULT ''

**修改后的完整表结构**：
```sql
CREATE TABLE api_key_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    api_key_id INT NOT NULL,
    model VARCHAR(50) NOT NULL,
    api_base VARCHAR(512) NOT NULL DEFAULT '',  -- 新增字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_key_model (api_key_id, model),
    INDEX idx_model (model),
    INDEX idx_api_key_id (api_key_id),

    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE,
    FOREIGN KEY (model) REFERENCES models(key) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### `api_keys` 表
**保留字段**（向后兼容）：
- `api_base` VARCHAR(512) NOT NULL - 保留作为默认值或兜底使用

### 2. 数据迁移

**迁移脚本**：`migrations/add_api_base_to_api_key_models.py`

**迁移步骤**：
1. 为 `api_key_models` 添加 `api_base` 字段
2. 将现有数据从 `api_keys.api_base` 复制到对应的 `api_key_models.api_base`
3. 验证数据完整性

**执行方式**：
```bash
# 升级
python migrations/add_api_base_to_api_key_models.py

# 回滚
python migrations/add_api_base_to_api_key_models.py --downgrade
```

---

## 代码变更

### 1. 数据模型层（app/models/model.py）

#### ApiKeyModel 类
```python
class ApiKeyModel(db.Model):
    """API密钥与模型关联表（多对多中间表）"""
    __tablename__ = 'api_key_models'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False)
    model = db.Column(db.String(50), db.ForeignKey('models.key', ondelete='CASCADE'), nullable=False)
    api_base = db.Column(db.String(512), nullable=False, default='')  # 新增
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)

    def to_dict(self):
        return {
            'model': self.model,
            'api_base': self.api_base
        }
```

#### ApiKey 类
**新增关系**：
```python
# 直接访问关联表，以获取每个模型的 api_base
model_configs = db.relationship(
    'ApiKeyModel',
    foreign_keys='ApiKeyModel.api_key_id',
    backref='api_key',
    lazy='select',
    cascade='all, delete-orphan'
)
```

**修改 to_dict() 方法**：
```python
def to_dict(self, include_secret=False):
    # 构建模型配置列表（包含 model 和 api_base）
    model_configs = []
    for config in self.model_configs:
        model_configs.append({
            'model': config.model,
            'api_base': config.api_base
        })

    result = {
        'id': self.id,
        'models': [m.key for m in self.models],  # 简单列表（向后兼容）
        'model_configs': model_configs,  # 详细配置（新增）
        'api_base': self.api_base,  # 默认值（向后兼容）
        # ... 其他字段
    }
```

### 2. 密钥分配逻辑（app/services/key_manager.py）

#### allocate_key() 方法
**修改前**：
```python
def allocate_key(cls, model: str):
    # 返回 ApiKey 对象
    return selected
```

**修改后**：
```python
def allocate_key(cls, model: str):
    """
    Returns:
        元组 (ApiKey对象, api_base) 或 (None, None)
    """
    # 改为查询 ApiKey 和对应的 api_base
    candidates_with_base = db.session.query(ApiKey, ApiKeyModel.api_base)\
        .join(ApiKeyModel, ApiKey.id == ApiKeyModel.api_key_id)\
        .filter(
            ApiKeyModel.model == model,
            ApiKey.status == 1
        )\
        .all()

    # ...
    return selected, api_base
```

#### _dispatch_next_task() 方法
**新增逻辑**：从关联表查询对应模型的 api_base
```python
from app.models.model import ApiKeyModel
model_key = task_data.get('model')

api_key_model = db.session.query(ApiKeyModel)\
    .filter_by(api_key_id=key_obj.id, model=model_key)\
    .first()

if api_key_model:
    api_base = api_key_model.api_base
else:
    # 兜底使用默认 api_base
    api_base = key_obj.api_base

task_data['api_base'] = api_base
```

### 3. 密钥管理服务（app/services/admin/key_service.py）

#### create_key() 函数
**支持两种格式**：

格式1 - 简单格式（所有模型共享 api_base）：
```python
create_key(
    models=['sora-video', 'sora-image'],
    api_base='https://ai.t8star.cn',
    key_secret='sk-xxx',
    max_concurrency=3,
    weight=10
)
```

格式2 - 详细格式（每个模型独立 api_base）：
```python
create_key(
    models=[
        {'model': 'sora-video', 'api_base': 'https://ai.t8star.cn/v2/videos/generations'},
        {'model': 'sora-image', 'api_base': 'https://ai.t8star.cn/v1/images/generations'}
    ],
    api_base='',  # 可选的默认值
    key_secret='sk-xxx',
    max_concurrency=3,
    weight=10
)
```

**实现逻辑**：
```python
# 规范化 models 格式
normalized_models = []
for item in models:
    if isinstance(item, str):
        # 简单格式：字符串
        normalized_models.append({'model': item, 'api_base': api_base or ''})
    elif isinstance(item, dict):
        # 详细格式：字典
        normalized_models.append({
            'model': item['model'],
            'api_base': item.get('api_base', api_base or '')
        })

# 手动创建关联记录（包含每个模型的 api_base）
for model_config in normalized_models:
    api_key_model = ApiKeyModel(
        api_key_id=api_key.id,
        model=model_config['model'],
        api_base=model_config['api_base']
    )
    db.session.add(api_key_model)
```

#### update_key() 函数
**支持更新模型的 api_base**：
```python
# 删除旧的关联记录
db.session.query(ApiKeyModel).filter_by(api_key_id=key_id).delete()

# 创建新的关联记录
for model_config in normalized_models:
    api_key_model = ApiKeyModel(
        api_key_id=key_id,
        model=model_config['model'],
        api_base=model_config['api_base']
    )
    db.session.add(api_key_model)
```

### 4. API 接口层（app/api/admin/keys.py）

#### POST /api/admin/keys（创建密钥）

**请求示例 - 格式1（简单）**：
```json
{
  "models": ["gpt-4", "gpt-4-turbo"],
  "api_base": "https://api.openai.com/v1",
  "key_secret": "sk-proj-abc123...",
  "max_concurrency": 3,
  "weight": 10
}
```

**请求示例 - 格式2（详细）**：
```json
{
  "models": [
    {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
    {"model": "sora-image", "api_base": "https://ai.t8star.cn/v1/images/generations"}
  ],
  "key_secret": "sk-proj-abc123...",
  "max_concurrency": 3,
  "weight": 10
}
```

**响应示例**：
```json
{
  "code": 0,
  "message": "Key added successfully",
  "data": {
    "id": 1,
    "models": ["sora-video", "sora-image"],
    "model_configs": [
      {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
      {"model": "sora-image", "api_base": "https://ai.t8star.cn/v1/images/generations"}
    ],
    "api_base": "",
    "max_concurrency": 3,
    "weight": 10,
    "status": 1
  }
}
```

#### PATCH /api/admin/keys/{id}（更新密钥）

**请求示例**：
```json
{
  "models": [
    {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
    {"model": "sora-image", "api_base": "https://ai.t8star.cn/v1/images/generations"},
    {"model": "sora-edit", "api_base": "https://ai.t8star.cn/v1/images/edits"}
  ]
}
```

---

## 测试验证

### 1. 功能测试

#### 创建密钥（详细格式）
```bash
curl -X POST http://localhost:5000/api/admin/keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "models": [
      {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
      {"model": "sora-image", "api_base": "https://ai.t8star.cn/v1/images/generations"}
    ],
    "key_secret": "sk-test-xxx",
    "max_concurrency": 5,
    "weight": 20
  }'
```

#### 验证密钥分配
```python
# 创建视频任务
task = create_task(user_id=1, model='sora-video', ...)

# 验证分配的 api_base 是否为视频端点
assert task.api_base == 'https://ai.t8star.cn/v2/videos/generations'

# 创建图片任务
task = create_task(user_id=1, model='sora-image', ...)

# 验证分配的 api_base 是否为图片端点
assert task.api_base == 'https://ai.t8star.cn/v1/images/generations'
```

### 2. 数据验证

```sql
-- 查看密钥的模型配置
SELECT
    ak.id,
    ak.key_secret,
    akm.model,
    akm.api_base
FROM api_keys ak
JOIN api_key_models akm ON ak.id = akm.api_key_id
WHERE ak.id = 1;

-- 预期结果：
-- id | key_secret | model       | api_base
-- 1  | sk-xxx     | sora-video  | https://ai.t8star.cn/v2/videos/generations
-- 1  | sk-xxx     | sora-image  | https://ai.t8star.cn/v1/images/generations
```

---

## 兼容性说明

### 1. 向后兼容

- **保留 `ApiKey.api_base` 字段**：作为默认值或兜底使用
- **支持简单格式**：仍然可以使用字符串数组创建密钥，此时所有模型共享 api_base
- **响应格式**：同时返回 `models` 简单列表和 `model_configs` 详细配置，供不同客户端使用

### 2. API 变更

**非破坏性变更**：
- 原有的简单格式请求仍然有效
- 新增详细格式支持
- 响应字段向后兼容（新增 `model_configs` 字段）

**前端需要调整**：
- 如果前端需要显示每个模型的 api_base，使用 `model_configs` 字段
- 如果只需要模型列表，继续使用 `models` 字段

---

## 部署步骤

### 1. 备份数据库
```bash
mysqldump -u root -p sora_platform > backup_before_multibase_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 执行数据库迁移
```bash
cd F:\Mirage\backend
"F:\software\anaconda\envs\sora_env\python.exe" migrations/add_api_base_to_api_key_models.py
```

### 3. 重启应用服务
```bash
# 停止当前服务
# 拉取最新代码
# 启动新服务
```

### 4. 验证功能
- 创建新密钥（测试两种格式）
- 创建任务验证密钥分配
- 检查任务使用的 api_base 是否正确

---

## 回滚方案

如果迁移后出现问题，可以回滚：

### 1. 代码回滚
```bash
git revert <commit_hash>
```

### 2. 数据库回滚
```bash
# 方式1：使用回滚脚本
python migrations/add_api_base_to_api_key_models.py --downgrade

# 方式2：使用数据库备份
mysql -u root -p sora_platform < backup_before_multibase_<timestamp>.sql
```

---

## 改造收益

### 1. 功能增强
- ✅ 支持一个密钥服务多个端点不同的模型
- ✅ 解决 t8star 等服务商的多端点场景
- ✅ 更灵活的密钥配置

### 2. 可维护性
- ✅ 数据结构更清晰，每个模型配置独立
- ✅ 便于后续扩展（如添加超时、重试等模型级配置）
- ✅ 减少密钥冗余（不需要为每个端点创建单独的密钥）

### 3. 性能影响
- 查询性能：新增一次 JOIN 查询，已通过索引优化
- 存储开销：每个关联增加 512 bytes（api_base 字段）
- 整体影响：可忽略

---

## 相关文件

### 修改的文件
1. `app/models/model.py` - 数据模型
2. `app/services/key_manager.py` - 密钥分配逻辑
3. `app/services/task_service.py` - 任务创建服务
4. `app/services/admin/key_service.py` - 密钥管理服务
5. `app/api/admin/keys.py` - API 接口

### 新增的文件
1. `migrations/add_api_base_to_api_key_models.py` - 迁移脚本
2. `docs/ApiKey多模型多端点改造文档.md` - 本文档

### 更新的文档
1. `docs/数据库表设计.md` - 数据库设计文档

---

**生成时间**：2026-01-07
**改造状态**：代码完成 ✅ | 数据库迁移待执行 ⏳
