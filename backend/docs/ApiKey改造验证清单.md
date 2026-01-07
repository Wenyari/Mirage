# ApiKey 多对多关系改造 - 验证清单

## 改造完成情况

### ✅ 已完成的修改

#### 1. 数据库模型层 (app/models/model.py)
- [x] 移除 `ApiKey.model` 字段
- [x] 添加 `ApiKey.models` 多对多关系
- [x] 创建 `ApiKeyModel` 关联表模型
- [x] 更新 `to_dict()` 方法返回 models 数组
- [x] 更新 `__repr__()` 方法
- [x] 语法验证通过 ✓

#### 2. 密钥分配逻辑 (app/services/key_manager.py)
- [x] `allocate_key()` 改为 JOIN 查询
- [x] `get_key_status()` 返回 models 数组
- [x] 语法验证通过 ✓

#### 3. 密钥管理服务 (app/services/admin/key_service.py)
- [x] `create_key()` 参数从 model 改为 models (列表)
- [x] `batch_create_keys()` 参数从 model 改为 models (列表)
- [x] `update_key()` 新增 models 参数支持修改模型关联
- [x] `get_key_list()` 支持逗号分隔的多模型筛选
- [x] `get_key_stats()` 改为 JOIN 查询
- [x] 语法验证通过 ✓

#### 4. API 接口层 (app/api/admin/keys.py)
- [x] POST /api/admin/keys - 请求体 model 改为 models 数组
- [x] POST /api/admin/keys/batch - 请求体 model 改为 models 数组
- [x] PATCH /api/admin/keys/{id} - 支持 models 参数
- [x] GET /api/admin/keys - 支持多模型筛选
- [x] 响应格式从 "model": "string" 改为 "models": ["array"]
- [x] 语法验证通过 ✓

#### 5. 模型配置服务 (app/services/admin/model_config_service.py)
- [x] `get_available_models()` 改为 JOIN 查询 (修复运行时错误)
- [x] 语法验证通过 ✓

#### 6. 模型管理服务 (app/services/admin/model_service.py)
- [x] `delete_model()` 改为 JOIN 查询 (修复运行时错误)
- [x] 语法验证通过 ✓

#### 7. 文档更新
- [x] 创建实施计划文档 `docs/ApiKey多对多关系改造计划.md`
- [x] 更新数据库设计文档 `docs/数据库表设计.md`
- [x] 记录 api_keys 表结构变更
- [x] 添加 api_key_models 表文档
- [x] 更新 ER 关系图

#### 8. 数据库迁移脚本
- [x] 创建 `migrations/convert_apikey_to_many_to_many.py`
- [x] 实现 upgrade() 函数（创建新表、迁移数据、删除旧字段）
- [x] 实现 downgrade() 函数（支持回滚）
- [x] 添加数据验证和错误处理

---

## 🔍 代码清理验证结果

### 旧查询模式清理
已搜索并修复所有生产代码中的 `filter_by(model=` 旧模式：

```bash
# 搜索 1: ApiKey.*filter_by.*model
结果: 仅在 tests/test_services/test_key_service.py:180 (测试文件，由用户手动处理)

# 搜索 2: query(ApiKey).*filter.*model
结果: 未找到匹配项 ✓

# 搜索 3: api_key\.model(?!s)
结果: 未找到匹配项 ✓

# 搜索 4: key\.model(?!s)
结果: 未找到匹配项 ✓
```

**结论**: ✅ 所有生产代码已成功更新，无残留旧查询模式

---

## ⚠️ 待执行的任务

### 1. 数据库迁移（必须）
```bash
# 步骤 1: 备份数据库
mysqldump -u root -p sora_platform > backup_before_migration.sql

# 步骤 2: 执行迁移脚本
cd F:\Mirage\backend
"F:\software\anaconda\envs\sora_env\python.exe" migrations/convert_apikey_to_many_to_many.py

# 如果出现问题，可以回滚
"F:\software\anaconda\envs\sora_env\python.exe" migrations/convert_apikey_to_many_to_many.py --downgrade
```

### 2. 测试文件更新（可选 - 用户手动处理）
- `tests/test_services/test_key_service.py:180` - 更新测试用例中的 filter_by(model=

### 3. 前端适配验证（如需）
检查前端是否需要适配新的 API 响应格式：
- 旧格式: `{ "model": "gpt-4" }`
- 新格式: `{ "models": ["gpt-4", "gpt-4-turbo"] }`

---

## 🧪 功能测试建议

### 1. 密钥管理接口测试

#### 创建密钥 (单模型)
```bash
POST /api/admin/keys
{
  "models": ["gpt-4"],
  "api_base": "https://api.openai.com/v1",
  "key_secret": "sk-test-123",
  "max_concurrency": 3,
  "weight": 10
}
```

#### 创建密钥 (多模型)
```bash
POST /api/admin/keys
{
  "models": ["gpt-4", "gpt-4-turbo", "gpt-4o"],
  "api_base": "https://api.openai.com/v1",
  "key_secret": "sk-test-456",
  "max_concurrency": 5,
  "weight": 20
}
```

#### 更新密钥模型关联
```bash
PATCH /api/admin/keys/1
{
  "models": ["gpt-4", "gpt-4o"]
}
```

#### 查询密钥列表 (多模型筛选)
```bash
GET /api/admin/keys?model=gpt-4,gpt-4-turbo
```

### 2. 密钥分配逻辑测试
- 创建任务时，验证密钥能否正确分配给支持该模型的密钥
- 验证权重选择逻辑是否正常
- 验证并发控制是否正常

### 3. 数据一致性验证
```sql
-- 验证所有旧密钥数据已迁移
SELECT ak.id, ak.key_secret, GROUP_CONCAT(akm.model) as models
FROM api_keys ak
LEFT JOIN api_key_models akm ON ak.id = akm.api_key_id
GROUP BY ak.id;

-- 验证关联表唯一约束
SELECT api_key_id, model, COUNT(*) as cnt
FROM api_key_models
GROUP BY api_key_id, model
HAVING cnt > 1;  -- 应该返回 0 行
```

### 4. 边界情况测试
- ✓ 创建空 models 数组（应该返回 400 错误）
- ✓ 创建不存在的 model（应该返回 400 错误）
- ✓ 更新密钥为空 models 列表（应该清空所有关联）
- ✓ 删除正在使用的密钥（应该返回错误）

---

## 📊 改造影响分析

### 数据库变更
- **新增表**: `api_key_models` (关联表)
- **删除字段**: `api_keys.model` (VARCHAR)
- **删除索引**: `idx_model_status`
- **新增索引**:
  - `uk_key_model` (UNIQUE)
  - `idx_model`
  - `idx_api_key_id`

### API 接口变更
**破坏性变更**:
- 请求参数: `model` (string) → `models` (array)
- 响应字段: `model` (string) → `models` (array)

**新增功能**:
- 支持一个密钥关联多个模型
- 支持更新密钥的模型关联
- 支持多模型联合筛选

### 性能影响
- **查询性能**: JOIN 查询可能略慢于原 filter_by，但已添加索引优化
- **存储开销**: 关联表占用额外存储（每个关联约 60 bytes）
- **并发性**: 多对多关系提高了密钥池的灵活性和利用率

---

## ✅ 验收标准

### 功能验收
- [ ] 可以创建支持单个模型的密钥
- [ ] 可以创建支持多个模型的密钥
- [ ] 可以更新密钥的模型关联
- [ ] 可以按模型筛选密钥列表
- [ ] 密钥分配逻辑正确选择支持目标模型的密钥
- [ ] 批量创建密钥功能正常
- [ ] 删除密钥时正确清理关联数据

### 性能验收
- [ ] 密钥列表查询响应时间 < 500ms
- [ ] 密钥分配响应时间 < 100ms
- [ ] 统计接口响应时间 < 1s

### 数据完整性验收
- [ ] 迁移前后密钥数量一致
- [ ] 所有旧密钥的 model 关联已转移到新表
- [ ] 无孤立的关联记录
- [ ] 外键约束正常工作

---

## 🐛 已知修复的运行时错误

### 错误 1: 模型配置页面 500 错误
- **文件**: `app/services/admin/model_config_service.py:48`
- **原因**: `ApiKey.query.filter_by(model=model.key)` 使用了已删除的字段
- **修复**: 改为 `db.session.query(ApiKey).join(ApiKey.models).filter(Model.key == model.key)`
- **状态**: ✅ 已修复

### 错误 2: 删除模型检查失败
- **文件**: `app/services/admin/model_service.py:129`
- **原因**: 同上，使用了已删除的 model 字段
- **修复**: 改为 JOIN 查询
- **状态**: ✅ 已修复

---

## 📝 回滚方案

如果迁移后发现严重问题，可按以下步骤回滚：

```bash
# 1. 停止应用服务
# 2. 执行回滚脚本
"F:\software\anaconda\envs\sora_env\python.exe" migrations/convert_apikey_to_many_to_many.py --downgrade

# 3. 如果回滚失败，使用数据库备份恢复
mysql -u root -p sora_platform < backup_before_migration.sql

# 4. 回退代码到改造前的版本
git revert <commit_hash>
```

---

## 📚 相关文档

- [改造实施计划](./ApiKey多对多关系改造计划.md)
- [数据库表设计](./数据库表设计.md)
- [迁移脚本](../migrations/convert_apikey_to_many_to_many.py)

---

**生成时间**: 2026-01-07
**改造状态**: 代码修改完成 ✅ | 数据库迁移待执行 ⏳
