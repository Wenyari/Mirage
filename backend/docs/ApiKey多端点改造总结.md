# ApiKey 多端点改造完成总结

## ✅ 改造已完成

### 问题背景
一个 API Key 支持多个模型时，不同模型可能需要不同的 api_base 端点。例如：
- 视频生成：`https://ai.t8star.cn/v2/videos/generations`
- 图片生成：`https://ai.t8star.cn/v1/images/generations`

之前的设计中 `ApiKey.api_base` 只能设置一个值，无法满足此需求。

### 解决方案
将 `api_base` 从 `ApiKey` 表移到 `api_key_models` 关联表，实现每个 (密钥, 模型) 组合有独立的端点配置。

---

## 📋 已完成的工作

### 1. 数据库模型层 ✅
**文件**: `app/models/model.py`

- [x] `ApiKeyModel` 添加 `api_base` 字段
- [x] `ApiKeyModel` 添加 `to_dict()` 方法
- [x] `ApiKey` 添加 `model_configs` 关系（访问关联表）
- [x] `ApiKey.to_dict()` 返回 `model_configs` 详细配置
- [x] 语法验证通过 ✓

**关键变更**：
```python
class ApiKeyModel(db.Model):
    api_base = db.Column(db.String(512), nullable=False, default='')  # 新增

class ApiKey(db.Model):
    model_configs = db.relationship('ApiKeyModel', ...)  # 新增关系
```

### 2. 密钥分配逻辑 ✅
**文件**: `app/services/key_manager.py`

- [x] `allocate_key()` 返回 `(ApiKey, api_base)` 元组
- [x] `_dispatch_next_task()` 从关联表查询 api_base
- [x] 语法验证通过 ✓

**关键变更**：
```python
# 返回密钥和对应模型的 api_base
return selected, api_base  # 之前只返回 selected
```

### 3. 任务创建服务 ✅
**文件**: `app/services/task_service.py`

- [x] 修改 `allocate_key()` 调用，接收返回的 `(key, api_base)`
- [x] 语法验证通过 ✓

**关键变更**：
```python
key, api_base = KeyManager.allocate_key(model_key)  # 解包元组
payload['api_base'] = api_base  # 使用分配的 api_base
```

### 4. 密钥管理服务 ✅
**文件**: `app/services/admin/key_service.py`

- [x] `create_key()` 支持两种格式（简单/详细）
- [x] `batch_create_keys()` 支持两种格式
- [x] `update_key()` 支持更新模型的 api_base
- [x] 手动创建 `ApiKeyModel` 记录
- [x] 语法验证通过 ✓

**支持格式**：
```python
# 格式1：简单（所有模型共享 api_base）
models = ['sora-video', 'sora-image']
api_base = 'https://ai.t8star.cn'

# 格式2：详细（每个模型独立 api_base）
models = [
    {'model': 'sora-video', 'api_base': 'https://ai.t8star.cn/v2/videos/generations'},
    {'model': 'sora-image', 'api_base': 'https://ai.t8star.cn/v1/images/generations'}
]
```

### 5. API 接口层 ✅
**文件**: `app/api/admin/keys.py`

- [x] 更新 POST `/api/admin/keys` 文档注释
- [x] 更新 POST `/api/admin/keys/batch` 文档注释
- [x] 更新 PATCH `/api/admin/keys/{id}` 文档注释
- [x] 语法验证通过 ✓

### 6. 数据库迁移脚本 ✅
**文件**: `migrations/add_api_base_to_api_key_models.py`

- [x] 创建迁移脚本
- [x] 实现 `upgrade()` 函数（添加字段、迁移数据）
- [x] 实现 `downgrade()` 函数（回滚）
- [x] 添加数据验证逻辑
- [x] 语法验证通过 ✓

**执行方式**：
```bash
python migrations/add_api_base_to_api_key_models.py  # 升级
python migrations/add_api_base_to_api_key_models.py --downgrade  # 回滚
```

### 7. 文档更新 ✅
**文件**:
- `docs/数据库表设计.md` - 更新表结构说明
- `docs/ApiKey多模型多端点改造文档.md` - 创建完整改造文档（本文档）

- [x] 更新 `api_key_models` 表结构文档
- [x] 添加 `api_base` 字段说明
- [x] 更新数据示例
- [x] 创建完整的改造文档

---

## 🧪 待执行任务

### 1. 数据库迁移 ⏳
```bash
# 步骤 1: 备份数据库
mysqldump -u root -p sora_platform > backup_multibase_20260107.sql

# 步骤 2: 执行迁移
cd F:\Mirage\backend
"F:\software\anaconda\envs\sora_env\python.exe" migrations/add_api_base_to_api_key_models.py
```

### 2. 功能测试 ⏳

#### 测试用例 1：创建密钥（详细格式）
```bash
POST /api/admin/keys
{
  "models": [
    {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
    {"model": "sora-image", "api_base": "https://ai.t8star.cn/v1/images/generations"}
  ],
  "key_secret": "sk-test-xxx",
  "max_concurrency": 5,
  "weight": 20
}
```

**预期结果**：
- 创建成功，返回 `model_configs` 包含两个模型的独立 api_base
- 数据库 `api_key_models` 表有两条记录，api_base 不同

#### 测试用例 2：创建任务验证密钥分配
```python
# 创建视频生成任务
task = create_task(model='sora-video', ...)

# 验证：分配的 api_base 应为视频端点
assert payload['api_base'] == 'https://ai.t8star.cn/v2/videos/generations'

# 创建图片生成任务
task = create_task(model='sora-image', ...)

# 验证：分配的 api_base 应为图片端点
assert payload['api_base'] == 'https://ai.t8star.cn/v1/images/generations'
```

#### 测试用例 3：更新密钥配置
```bash
PATCH /api/admin/keys/1
{
  "models": [
    {"model": "sora-video", "api_base": "https://ai.t8star.cn/v2/videos/generations"},
    {"model": "sora-edit", "api_base": "https://ai.t8star.cn/v1/images/edits"}
  ]
}
```

**预期结果**：
- 旧的 `sora-image` 关联被删除
- 新增 `sora-edit` 关联

---

## 📊 变更统计

### 修改的文件（6个）
1. `app/models/model.py` - 数据模型
2. `app/services/key_manager.py` - 密钥分配
3. `app/services/task_service.py` - 任务创建
4. `app/services/admin/key_service.py` - 密钥管理
5. `app/api/admin/keys.py` - API 接口
6. `docs/数据库表设计.md` - 数据库文档

### 新增的文件（2个）
1. `migrations/add_api_base_to_api_key_models.py` - 迁移脚本
2. `docs/ApiKey多模型多端点改造文档.md` - 改造文档

### 代码行数统计
- 新增代码：约 350 行
- 修改代码：约 150 行
- 文档：约 600 行

---

## 🔍 核心技术要点

### 1. 关联表字段扩展
```sql
ALTER TABLE api_key_models
ADD COLUMN api_base VARCHAR(512) NOT NULL DEFAULT ''
AFTER model;
```

### 2. ORM 关系配置
```python
# 直接访问关联表（非 secondary 方式）
model_configs = db.relationship(
    'ApiKeyModel',
    foreign_keys='ApiKeyModel.api_key_id',
    backref='api_key',
    lazy='select',
    cascade='all, delete-orphan'
)
```

### 3. JOIN 查询优化
```python
# 一次查询获取 ApiKey 和对应的 api_base
candidates_with_base = db.session.query(ApiKey, ApiKeyModel.api_base)\
    .join(ApiKeyModel, ApiKey.id == ApiKeyModel.api_key_id)\
    .filter(ApiKeyModel.model == model, ApiKey.status == 1)\
    .all()
```

### 4. 灵活的参数格式
```python
# 支持字符串和字典混合
models = ['model1', {'model': 'model2', 'api_base': '...'}]

# 统一规范化处理
normalized_models = []
for item in models:
    if isinstance(item, str):
        normalized_models.append({'model': item, 'api_base': default_base})
    elif isinstance(item, dict):
        normalized_models.append(item)
```

---

## 🎯 改造收益

### 功能增强
- ✅ 支持一个密钥服务多个不同端点的模型
- ✅ 解决 t8star 等多端点场景
- ✅ API 保持向后兼容

### 可维护性
- ✅ 数据结构更清晰
- ✅ 便于后续扩展（如添加超时、重试等配置）
- ✅ 减少密钥冗余

### 性能影响
- 查询：新增一次 JOIN，已优化索引
- 存储：每条关联 +512 bytes
- 整体：影响可忽略

---

## 📝 后续建议

### 短期
1. 执行数据库迁移
2. 完成功能测试
3. 更新前端适配新的响应格式

### 长期
1. 考虑在关联表中添加更多配置项：
   - `timeout` - 请求超时时间
   - `retry_count` - 重试次数
   - `headers` - 自定义请求头
2. 监控不同端点的性能和错误率
3. 优化密钥分配算法（考虑端点健康度）

---

## 🔧 故障排查

### 问题1：迁移失败
**症状**：执行迁移时报错
**排查**：
1. 检查数据库连接
2. 检查表是否存在
3. 查看错误日志
4. 使用备份恢复

### 问题2：密钥分配失败
**症状**：`allocate_key()` 返回 `(None, None)`
**排查**：
1. 检查 `api_key_models` 表是否有对应记录
2. 检查密钥状态是否为启用
3. 检查是否所有密钥都在冷却中
4. 查看日志中的 WARNING 信息

### 问题3：api_base 为空
**症状**：任务执行时 api_base 为空字符串
**排查**：
1. 检查创建密钥时是否指定了 api_base
2. 查询 `api_key_models` 表确认 api_base 值
3. 检查 `_dispatch_next_task()` 的查询逻辑
4. 确认是否命中了兜底逻辑

---

## ✅ 验收标准

- [x] 所有修改文件语法验证通过
- [ ] 数据库迁移执行成功
- [ ] 可以创建详细格式的密钥
- [ ] 可以创建简单格式的密钥（向后兼容）
- [ ] 密钥分配返回正确的 api_base
- [ ] 不同模型使用不同的 api_base
- [ ] 更新密钥配置功能正常
- [ ] 原有密钥功能不受影响

---

**生成时间**：2026-01-07
**改造状态**：代码完成 ✅ | 测试待执行 ⏳
**预计工作量**：迁移 5min | 测试 30min
