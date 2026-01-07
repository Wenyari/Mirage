# 前端升级指南：模型Tags分类功能

> **版本**: v1.0
> **更新日期**: 2026-01-07
> **影响范围**: 模型管理相关页面
> **优先级**: 中等（向后兼容，非破坏性更新）

---

## 📋 目录

1. [修改概述](#修改概述)
2. [后端API变更](#后端api变更)
3. [数据结构变化](#数据结构变化)
4. [前端适配方案](#前端适配方案)
5. [UI/UX设计建议](#uiux设计建议)
6. [示例代码](#示例代码)
7. [测试要点](#测试要点)

---

## 📝 修改概述

### 背景

为了提升用户体验，我们在models表中新增了`tags`字段，用于对AI模型进行分类。用户可以通过标签快速筛选和查找所需类型的模型（如视频生成、图片生成、对话等）。

### 核心变更

- ✅ **数据库**: models表新增`tags`字段（JSON类型）
- ✅ **API**: 所有模型相关接口支持tags参数
- ✅ **筛选**: 新增按tags筛选模型的功能
- ✅ **向后兼容**: 完全兼容现有前端代码，无需强制更新

### 标签体系

我们推荐以下标签分类体系：

| 维度 | 标签 | 说明 |
|------|------|------|
| **类型维度** | `video`, `image`, `text`, `audio` | 模型处理的媒体类型 |
| **功能维度** | `generation`, `edit`, `chat`, `transcription` | 模型的主要功能 |
| **特性维度** | `hd`, `realtime`, `multimodal` | 模型的特殊能力 |

**示例组合**：
- Sora: `["video", "generation"]`
- GPT-4: `["text", "chat", "multimodal"]`
- DALL-E 3: `["image", "generation"]`
- Whisper: `["audio", "transcription"]`

---

## 🔌 后端API变更

### 1. 获取模型列表 `GET /api/admin/models`

#### 新增查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tags` | String | 否 | 逗号分隔的标签，如 `"video,generation"` |

#### 请求示例

```bash
# 获取所有模型（原有功能，完全兼容）
GET /api/admin/models

# 筛选包含"video"或"generation"标签的模型（新功能）
GET /api/admin/models?tags=video,generation

# 筛选包含"chat"标签的模型
GET /api/admin/models?tags=chat
```

#### 响应数据结构（新增tags字段）

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "key": "sora-2",
      "name": "Sora 2.0",
      "enabled": 1,
      "description": "OpenAI Sora 视频生成模型",
      "color": "bg-blue-500",
      "icon_url": null,
      "max_concurrency_limit": 10,
      "tags": ["video", "generation"],  // 新增字段
      "created_at": "2024-01-07T10:00:00Z",
      "updated_at": "2024-01-07T10:00:00Z"
    },
    {
      "key": "gpt-4",
      "name": "GPT-4",
      "enabled": 1,
      "tags": ["text", "chat", "multimodal"],  // 新增字段
      ...
    },
    {
      "key": "legacy-model",
      "name": "Legacy Model",
      "enabled": 1,
      "tags": [],  // 未设置tags的模型返回空数组
      ...
    }
  ]
}
```

**重要提示**：
- ✅ `tags`字段始终存在（向后兼容）
- ✅ 未设置tags的模型返回空数组`[]`（不会是`null`）
- ✅ 不传递`tags`参数时，返回所有模型（原有行为）

---

### 2. 创建模型 `POST /api/admin/models`

#### 新增请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tags` | Array<String> | 否 | 模型标签数组 |

#### 请求示例

```bash
POST /api/admin/models
Content-Type: application/json
Authorization: Bearer {admin_token}

{
  "key": "claude-3-opus",
  "name": "Claude 3 Opus",
  "enabled": true,
  "description": "Anthropic最强大的对话模型",
  "color": "bg-orange-500",
  "max_concurrency_limit": 15,
  "tags": ["text", "chat", "multimodal"]  // 新增字段（可选）
}
```

#### 响应示例

```json
{
  "code": 0,
  "message": "Model created successfully",
  "data": {
    "key": "claude-3-opus",
    "name": "Claude 3 Opus",
    "tags": ["text", "chat", "multimodal"],
    ...
  }
}
```

#### 数据验证规则

- ❌ tags必须是数组类型（传递字符串会报错400）
- ❌ 所有tag元素必须是字符串（传递数字会报错400）
- ✅ 可以传递空数组`[]`
- ✅ 可以不传递tags字段（与传递`null`效果相同）

#### 错误响应示例

```json
// 错误：tags不是数组
{
  "code": 400,
  "message": "tags must be a list",
  "data": null
}

// 错误：tag元素不是字符串
{
  "code": 400,
  "message": "All tags must be strings",
  "data": null
}
```

---

### 3. 更新模型 `PATCH /api/admin/models/:key`

#### 新增请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tags` | Array<String> | 否 | 模型标签数组 |

#### 请求示例

```bash
# 仅更新tags
PATCH /api/admin/models/sora-2
Content-Type: application/json
Authorization: Bearer {admin_token}

{
  "tags": ["video", "generation", "hd"]
}

# 同时更新多个字段
PATCH /api/admin/models/gpt-4
Content-Type: application/json
Authorization: Bearer {admin_token}

{
  "name": "GPT-4 Turbo",
  "description": "更快的GPT-4版本",
  "tags": ["text", "chat", "multimodal", "realtime"]
}

# 清空tags（传递空数组）
PATCH /api/admin/models/legacy-model
Content-Type: application/json
Authorization: Bearer {admin_token}

{
  "tags": []
}
```

#### 响应示例

```json
{
  "code": 0,
  "message": "Model updated successfully",
  "data": {
    "key": "sora-2",
    "name": "Sora 2.0",
    "tags": ["video", "generation", "hd"],
    ...
  }
}
```

---

### 4. 删除模型 `DELETE /api/admin/models/:key`

**无变更**，与之前完全一致。

