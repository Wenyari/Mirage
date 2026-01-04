# AIGC 平台管理员后台 API 接口文档

## 文档说明

**版本**：v1.0
**基础路径**：`/api/admin`
**认证方式**：JWT Token（Header: `Authorization: Bearer <token>`）
**权限要求**：所有接口需验证 `user.role === 'admin'`，否则返回 403

---

## 通用规范

### 响应格式

所有接口统一返回以下格式：

```json
{
  "code": 0,          // 0 表示成功，非 0 表示失败
  "message": "Success",  // 消息描述
  "data": {}          // 实际数据（可以是对象、数组或 null）
}
```

### 错误码规范

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 权限不足（非管理员） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 分页参数

列表接口通用分页参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码（从 1 开始） |
| limit | integer | 否 | 10 | 每页数量 |

分页响应格式：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "items": [],      // 数据列表
    "total": 100,     // 总数量
    "page": 1,        // 当前页码
    "limit": 10       // 每页数量
  }
}
```

---

## 一、仪表盘 (Dashboard)

### 1.1 获取核心指标

**接口路径**：`GET /api/admin/stats/overview`

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "today_new_users": 42,              // 今日新增用户数
    "today_points_consumed": 12500.50,  // 今日积分消耗量
    "today_cdk_recharge": 50000.00,     // 今日通过CDK兑换充值的积分
    "active_tasks": 18                  // 当前活跃任务数
  }
}
```

---

### 1.2 获取趋势图数据

**接口路径**：`GET /api/admin/stats/chart`

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | string | 否 | "7" | 查询天数，可选值：`"7"` 或 `"30"` |

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "date": "2024-12-24",            // 日期（YYYY-MM-DD）
      "new_users": 35,                 // 新增用户数
      "points_consumed": 9800.50,      // 积分消耗量
      "cdk_recharge": 28000.00         // CDK充值积分
    },
    {
      "date": "2024-12-25",
      "new_users": 28,
      "points_consumed": 8500.00,
      "cdk_recharge": 24000.00
    }
    // ... 更多数据点
  ]
}
```

**说明**：
- `days=7` 返回近 7 天的数据（7 个数据点）
- `days=30` 返回近 30 天的数据（30 个数据点）
---

## 二、用户管理 (User Management)

### 2.1 获取用户列表

**接口路径**：`GET /api/admin/users`

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 10 | 每页数量 |
| email | string | 否 | - | 邮箱搜索（模糊匹配） |
| level | integer | 否 | - | 用户等级筛选（1-5，对应 T1-T5） |
| status | integer | 否 | - | 用户状态筛选（0=正常，1=封禁） |

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "email": "user1@example.com",
        "avatar": "https://i.pravatar.cc/150?img=1",  // 头像 URL（可选）
        "level": 1,                    // 用户等级：1-5（T1-T5）
        "balance": 1000,               // 账户余额（元）
        "status": 0,                   // 状态：1=正常，0=封禁
        "created_at": "2024-01-15T10:30:00Z",  // 注册时间（ISO 8601）
        "last_active": "2024-03-20T15:45:00Z"  // 最后活跃时间
      },
      {
        "id": 2,
        "email": "user2@example.com",
        "avatar": "https://i.pravatar.cc/150?img=2",
        "level": 3,
        "balance": 5000,
        "status": 0,
        "created_at": "2024-02-10T09:20:00Z",
        "last_active": "2024-03-21T10:30:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 10
  }
}
```

---

### 2.2 获取用户详情

**接口路径**：`GET /api/admin/users/{user_id}/details`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户 ID |

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "user": {
      "id": 1,
      "email": "user1@example.com",
      "avatar": "https://i.pravatar.cc/150?img=1",
      "level": 1,
      "balance": 1000,
      "status": 0,
      "created_at": "2024-01-15T10:30:00Z",
      "last_active": "2024-03-20T15:45:00Z"
    },
    "recent_transactions": [
      {
        "id": 101,
        "type": "recharge",           // 类型：recharge（充值）、consume（消费）、refund（退款）
        "amount": 100,                // 金额
        "reason": "管理员充值",
        "created_at": "2024-03-20T14:30:00Z"
      }
    ],
    "recent_tasks": [
      {
        "id": 201,
        "model": "gpt-4",
        "prompt": "生成一张图片...",
        "status": "completed",        // 状态：pending、processing、completed、failed
        "token_used": 500,
        "created_at": "2024-03-20T15:00:00Z"
      }
    ]
  }
}
```

---

### 2.3 人工充值/扣费

**接口路径**：`PATCH /api/admin/users/{user_id}/balance`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户 ID |

**请求 Body**：

```json
{
  "amount": 100,        // 变动金额（正数=充值，负数=扣费）
  "reason": "活动奖励"   // 原因说明
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Balance updated successfully",
  "data": {
    "new_balance": 1100   // 更新后的余额
  }
}
```

---

### 2.4 修改用户资料

**接口路径**：`PATCH /api/admin/users/{user_id}/profile`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户 ID |

**请求 Body**：

```json
{
  "level": 3,     // 用户等级：1-5（可选）
  "status": 0     // 用户状态：1=正常，0=封禁（可选）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "User profile updated successfully",
  "data": null
}
```

---

## 三、CDK 兑换码管理 (CDK Management)

### 3.1 批量生成 CDK

**接口路径**：`POST /api/admin/cdk/generate`

**请求 Body**：

```json
{
  "amount": 500,              // 单个 CDK 面额（元）
  "count": 20,                // 生成数量
  "type": "once",             // 类型：once（单次使用）、multi（可重复使用）
  "batch_name": "春节活动"    // 批次名称
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "CDK generated successfully",
  "data": {
    "batch_no": "BATCH20240320001",   // 批次号
    "cdks": [
      {
        "id": 1,
        "code": "CDK-ABCD1234EFGH5678",   // CDK 码
        "value": 500,                      // 面额
        "type": "once",
        "status": "unused",                // 状态：unused（未使用）、used（已使用）、void（已作废）
        "created_at": "2024-03-20T16:00:00Z"
      },
      {
        "id": 2,
        "code": "CDK-IJKL5678MNOP9012",
        "value": 500,
        "type": "once",
        "status": "unused",
        "created_at": "2024-03-20T16:00:00Z"
      }
      // ... 更多 CDK
    ]
  }
}
```

**说明**：
- 前端会将返回的 CDK 列表导出为 Excel 文件
- 批次号用于后续批量作废操作

---

### 3.2 获取 CDK 列表

**接口路径**：`GET /api/admin/cdk`

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 10 | 每页数量 |
| batch_no | string | 否 | - | 批次号筛选 |
| status | string | 否 | - | 状态筛选（unused、used、void） |
| search | string | 否 | - | 模糊搜索（批次号或CDK码） |

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "code": "CDK-ABCD1234EFGH5678",
        "value": 500,
        "batch_no": "BATCH20240320001",
        "batch_name": "春节活动",
        "type": "once",
        "status": "used",
        "used_by": "user1@example.com",          // 使用者邮箱（已使用时才有）
        "used_at": "2024-03-21T10:00:00Z",       // 使用时间
        "created_at": "2024-03-20T16:00:00Z"
      },
      {
        "id": 2,
        "code": "CDK-IJKL5678MNOP9012",
        "value": 500,
        "batch_no": "BATCH20240320001",
        "batch_name": "春节活动",
        "type": "once",
        "status": "unused",
        "used_by": null,
        "used_at": null,
        "created_at": "2024-03-20T16:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "limit": 10
  }
}
```

---

### 3.3 批量作废 CDK

**接口路径**：`POST /api/admin/cdk/void`

**请求 Body** (方式一：按批次作废)：

```json
{
  "batch_no": "BATCH20240320001"   // 批次号
}
```

**请求 Body** (方式二：按 ID 作废)：

```json
{
  "ids": [1, 2, 3, 4, 5]   // CDK ID 数组
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "CDKs voided successfully",
  "data": {
    "voided_count": 15   // 作废数量
  }
}
```

---

## 四、密钥池管理 (Key Pool Management)

> **架构说明**：密钥池采用 MySQL + Redis 双层架构
> - **MySQL**：存储密钥配置（platform, key_secret, max_concurrency, weight, status）
> - **Redis**：维护实时状态（并发计数、熔断标记、统计缓冲）

> **⚠️ 重要变更**：平台配置已改为动态管理，不再硬编码
> - 新增 `GET /api/admin/platforms` 接口获取可用平台列表
> - 支持动态添加新的 AI 模型平台，无需修改前端代码
> - Platform 字段类型从 `enum` 改为 `string`

### 4.1 获取平台配置列表

**接口路径**：`GET /api/admin/platforms`

**说明**：获取系统支持的所有平台配置，前端通过此接口动态渲染平台选择器。

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "key": "openai",
      "name": "OpenAI",
      "enabled": true,
      "description": "OpenAI GPT 系列模型",
      "color": "bg-green-500",
      "max_concurrency_limit": 20
    },
    {
      "key": "sora",
      "name": "Sora",
      "enabled": true,
      "description": "OpenAI Sora 视频生成模型",
      "color": "bg-blue-500",
      "max_concurrency_limit": 10
    },
    {
      "key": "stability",
      "name": "Stability AI",
      "enabled": false,
      "description": "Stable Diffusion 系列模型",
      "color": "bg-indigo-500",
      "max_concurrency_limit": 10
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | string | ✅ | 平台标识符（用于数据库存储） |
| name | string | ✅ | 平台显示名称 |
| enabled | boolean | ✅ | 是否启用（false 表示禁用，不在前端显示） |
| description | string | ❌ | 平台描述信息 |
| color | string | ❌ | Tailwind CSS 颜色类（用于 UI 展示） |
| max_concurrency_limit | number | ❌ | 该平台建议的最大并发限制 |

---

### 4.2 创建平台

**接口路径**：`POST /api/admin/platforms`

**说明**：创建新的AI平台配置。

**请求体**：

```json
{
  "key": "claude",                      // 平台唯一标识
  "name": "Claude",                     // 显示名称
  "enabled": true,                      // 是否启用
  "description": "Anthropic Claude 系列模型",  // 描述（可选）
  "color": "bg-purple-500",             // Tailwind颜色类（可选）
  "icon_url": "https://example.com/icon.png",  // 图标URL（可选）
  "max_concurrency_limit": 15           // 建议最大并发（可选）
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | string | ✅ | 平台唯一标识（仅支持小写字母、数字、下划线）|
| name | string | ✅ | 平台显示名称 |
| enabled | boolean | ✅ | 是否启用 |
| description | string | ❌ | 平台描述信息 |
| color | string | ❌ | Tailwind CSS 颜色类 |
| icon_url | string | ❌ | 平台图标URL |
| max_concurrency_limit | number | ❌ | 建议的最大并发限制 |

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform created successfully",
  "data": {
    "key": "claude",
    "name": "Claude",
    "enabled": true,
    "description": "Anthropic Claude 系列模型",
    "color": "bg-purple-500",
    "icon_url": "https://example.com/icon.png",
    "max_concurrency_limit": 15,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应**：

```json
{
  "code": 400,
  "message": "Platform key already exists",
  "data": null
}
```

---

### 4.3 更新平台

**接口路径**：`PATCH /api/admin/platforms/:key`

**说明**：更新平台配置信息（平台key不可修改）。

**请求体**：

```json
{
  "name": "Claude API",                 // 可选
  "enabled": false,                     // 可选
  "description": "Updated description", // 可选
  "color": "bg-indigo-500",            // 可选
  "icon_url": "https://new-icon.png",  // 可选
  "max_concurrency_limit": 20          // 可选
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform updated successfully",
  "data": {
    "key": "claude",
    "name": "Claude API",
    "enabled": false,
    "description": "Updated description",
    "color": "bg-indigo-500",
    "icon_url": "https://new-icon.png",
    "max_concurrency_limit": 20,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:20:00Z"
  }
}
```

---

### 4.4 删除平台

**接口路径**：`DELETE /api/admin/platforms/:key`

**说明**：删除平台配置。

**注意事项**：
- 只有当该平台没有关联的密钥和任务时才能删除
- 如果有关联数据，应先禁用平台（enabled: false）而非删除

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform deleted successfully",
  "data": null
}
```

**错误响应（有关联数据）**：

```json
{
  "code": 400,
  "message": "Cannot delete platform with existing keys or tasks",
  "data": {
    "key_count": 5,
    "task_count": 120
  }
}
```

---

### 4.5 获取密钥列表

**接口路径**：`GET /api/admin/keys`

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | - | 平台筛选（openai、sora、midjourney 等） |

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "platform": "openai",                 // 平台标识
      "key_secret": "sk-proj-abc****xyz",   // 密钥（脱敏：前8位 + **** + 后4位）
      "max_concurrency": 3,                 // 最大并发限制
      "weight": 10,                         // 权重（用于负载均衡，1-100）
      "status": 1,                          // 状态：1=启用，0=手动停用

      // 统计字段（MySQL 存储，定时从 Redis 同步）
      "total_calls": 15420,                 // 总调用次数
      "total_errors": 23,                   // 总失败次数

      // 实时状态（从 Redis 读取）
      "current_usage": 2,                   // 当前并发数（0-max_concurrency）
      "is_cooling": false,                  // 是否在冷却期（熔断中）
      "cooling_until": null,                // 冷却结束时间（ISO 8601，冷却中才有值）

      "last_used_at": "2024-03-20T15:30:00Z",  // 最后使用时间
      "created_at": "2024-03-01T10:00:00Z"
    },
    {
      "id": 2,
      "platform": "openai",
      "key_secret": "sk-proj-def****uvw",
      "max_concurrency": 5,
      "weight": 20,
      "status": 1,
      "total_calls": 8930,
      "total_errors": 156,
      "current_usage": 5,                   // 并发已满
      "is_cooling": false,
      "cooling_until": null,
      "last_used_at": "2024-03-20T16:00:00Z",
      "created_at": "2024-03-05T14:00:00Z"
    },
    {
      "id": 3,
      "platform": "sora",
      "key_secret": "sk-sora-xyz****abc",
      "max_concurrency": 2,
      "weight": 5,
      "status": 1,
      "total_calls": 234,
      "total_errors": 45,
      "current_usage": 0,
      "is_cooling": true,                   // 正在冷却（触发了熔断）
      "cooling_until": "2024-03-20T16:10:00Z",  // 预计恢复时间
      "last_used_at": "2024-03-20T16:05:00Z",
      "created_at": "2024-03-15T09:00:00Z"
    }
  ]
}
```

**字段说明**：
- `max_concurrency`：核心配置，控制该 Key 同时运行的任务数上限
- `weight`：权重越高，被选中的概率越大（用于"大号优先"策略）
- `current_usage`：从 Redis `pool:usage:{key_id}` 实时读取
- `is_cooling` / `cooling_until`：从 Redis `pool:cooldown:{key_id}` 读取（TTL 300s）

---

### 4.6 添加密钥

**接口路径**：`POST /api/admin/keys`

**请求 Body**：

```json
{
  "platform": "openai",              // 平台标识（必填）
  "key_secret": "sk-proj-abc123...", // API 密钥完整串（必填）
  "max_concurrency": 3,              // 最大并发数（可选，默认 3）
  "weight": 10                       // 权重（可选，默认 10）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Key added successfully",
  "data": {
    "id": 4,
    "platform": "openai",
    "key_secret": "sk-proj-ab****",    // 返回时已脱敏
    "max_concurrency": 3,
    "weight": 10,
    "status": 1,
    "created_at": "2024-03-20T17:00:00Z"
  }
}
```

---

### 4.7 批量添加密钥

**接口路径**：`POST /api/admin/keys/batch`

**请求 Body**：

```json
{
  "platform": "openai",              // 平台（必填）
  "keys": [                          // 密钥数组（必填，最多 100 个）
    "sk-proj-abc123...",
    "sk-proj-def456...",
    "sk-proj-ghi789..."
  ],
  "max_concurrency": 3,              // 统一的最大并发（可选，默认 3）
  "weight": 10                       // 统一的权重（可选，默认 10）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Batch import completed",
  "data": {
    "success_count": 3,              // 成功导入数量
    "failed_count": 0,               // 失败数量
    "failed_keys": []                // 失败的密钥列表（脱敏）
  }
}
```

---

### 4.8 更新密钥配置

**接口路径**：`PATCH /api/admin/keys/{id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 密钥 ID |

**请求 Body**：

```json
{
  "max_concurrency": 5,   // 最大并发数（可选）
  "weight": 20,           // 权重（可选）
  "status": 1             // 状态：1=启用，0=停用（可选）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Key updated successfully",
  "data": null
}
```

---

### 4.9 删除密钥

**接口路径**：`DELETE /api/admin/keys/{id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 密钥 ID |

**响应示例**：

```json
{
  "code": 0,
  "message": "Key deleted successfully",
  "data": null
}
```

**注意**：删除密钥时，如果该密钥正在被使用（current_usage > 0），后端应返回 400 错误，提示先等待任务完成或手动停用。

---

### 4.10 手动触发熔断/解除熔断

**接口路径**：`POST /api/admin/keys/{id}/cooldown`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 密钥 ID |

**请求 Body**：

```json
{
  "action": "trigger",   // 操作：trigger（触发熔断）、release（解除熔断）
  "duration": 300        // 冷却时长（秒，仅 trigger 时需要，默认 300）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Cooldown triggered successfully",
  "data": {
    "cooling_until": "2024-03-20T16:15:00Z"
  }
}
```

---

### 4.11 触发健康检测

**接口路径**：`POST /api/admin/keys/health-check`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 否 | 指定平台检测（不填则检测所有） |

**说明**：
- 后端调用各平台 API 验证密钥有效性
- 检测结果会更新密钥状态和错误计数
- 建议异步执行，返回任务 ID 供前端轮询

**响应示例**（同步方式）：

```json
{
  "code": 0,
  "message": "Health check completed",
  "data": {
    "total": 10,           // 总密钥数
    "active": 7,           // 正常可用
    "cooling": 2,          // 冷却中
    "disabled": 1,         // 手动停用
    "details": [           // 详细结果
      {
        "id": 1,
        "platform": "openai",
        "status": 1,
        "is_cooling": false,
        "check_result": "ok"
      },
      {
        "id": 3,
        "platform": "sora",
        "status": 1,
        "is_cooling": true,
        "check_result": "rate_limit"
      }
    ]
  }
}
```

**响应示例**（异步方式）：

```json
{
  "code": 0,
  "message": "Health check started",
  "data": {
    "task_id": "health_check_12345",   // 任务 ID
    "estimated_time": 30                // 预计耗时（秒）
  }
}
```

---

### 4.12 获取密钥统计信息

**接口路径**：`GET /api/admin/keys/stats`

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "by_platform": [
      {
        "platform": "openai",
        "total_keys": 5,
        "active_keys": 4,
        "cooling_keys": 1,
        "total_concurrency": 15,        // 所有 Key 的并发数总和
        "current_usage": 8              // 当前实际使用的并发数
      },
      {
        "platform": "sora",
        "total_keys": 3,
        "active_keys": 2,
        "cooling_keys": 1,
        "total_concurrency": 6,
        "current_usage": 2
      }
    ],
    "total_calls_today": 3420,          // 今日总调用次数
    "total_errors_today": 45,           // 今日总失败次数
    "error_rate": 1.32                  // 错误率（%）
  }
}
```

---

## 五、平台配置管理 (Platform Configuration)

> **设计变更说明**：平台配置管理直接基于密钥池中的 platform
> - 后端从 `api_keys` 表中获取所有不重复的 `platform` 作为可配置的平台列表
> - 管理员可为每个 platform 配置：等级权限、积分计费、Token 费率
> - 平台配置存储在独立的 `platform_configs` 表中

### 5.1 获取平台配置列表

**接口路径**：`GET /api/admin/platform-configs`

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "platform": "openai",              // 平台标识（来自密钥池）
      "platform_name": "OpenAI",         // 平台显示名称（来自 platforms 表）
      "allowed_tiers": ["T1", "T2", "T3", "T4", "T5"],  // 允许使用的等级
      "cost_per_call": 10,               // 每次调用扣除积分（固定计费）
      "token_cost_config": {
        "enabled": true,                 // 是否启用 Token 计费
        "input_cost": 0.03,              // 输入 Token 费率（每千 token，积分）
        "output_cost": 0.06              // 输出 Token 费率（每千 token，积分）
      },
      "is_active": true,                 // 是否启用该平台
      "description": "OpenAI GPT 系列模型",
      "created_at": "2024-03-01T10:00:00Z",
      "updated_at": "2024-03-20T15:30:00Z"
    },
    {
      "id": 2,
      "platform": "sora",
      "platform_name": "Sora",
      "allowed_tiers": ["T3", "T4", "T5"],  // 仅高级会员可用
      "cost_per_call": 100,
      "token_cost_config": {
        "enabled": false                 // 不使用 Token 计费，仅固定计费
      },
      "is_active": true,
      "description": "OpenAI Sora 视频生成模型",
      "created_at": "2024-03-10T12:00:00Z",
      "updated_at": "2024-03-20T16:00:00Z"
    },
    {
      "id": 3,
      "platform": "midjourney",
      "platform_name": "Midjourney",
      "allowed_tiers": ["T2", "T3", "T4", "T5"],
      "cost_per_call": 50,
      "token_cost_config": {
        "enabled": false
      },
      "is_active": true,
      "description": "Midjourney 图像生成",
      "created_at": "2024-03-05T09:00:00Z",
      "updated_at": "2024-03-18T14:00:00Z"
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | ✅ | 配置 ID |
| platform | string | ✅ | 平台标识（来自密钥池） |
| platform_name | string | ✅ | 平台显示名称 |
| allowed_tiers | string[] | ✅ | 允许使用的等级数组（T1-T5） |
| cost_per_call | number | ✅ | 每次调用扣除积分（固定计费） |
| token_cost_config | object | ✅ | Token 计费配置 |
| token_cost_config.enabled | boolean | ✅ | 是否启用 Token 计费 |
| token_cost_config.input_cost | number | ❌ | 输入 Token 费率（每千 token，积分） |
| token_cost_config.output_cost | number | ❌ | 输出 Token 费率（每千 token，积分） |
| is_active | boolean | ✅ | 是否启用该平台 |
| description | string | ❌ | 平台描述 |

**计费逻辑说明**：
- **固定计费**：每次调用扣除 `cost_per_call` 积分
- **Token 计费**：如果 `token_cost_config.enabled = true`，则额外按 Token 消耗计费
  - 总扣除积分 = `cost_per_call` + (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)
- 如果 `token_cost_config.enabled = false`，则仅使用固定计费

---

### 5.2 获取可配置的平台列表

**接口路径**：`GET /api/admin/platform-configs/available-platforms`

**请求参数**：无

**说明**：获取密钥池中所有不重复的 platform，用于新建配置时选择。

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "platform": "openai",
      "platform_name": "OpenAI",
      "has_config": true,           // 是否已有配置
      "key_count": 5                // 该平台的密钥数量
    },
    {
      "platform": "sora",
      "platform_name": "Sora",
      "has_config": true,
      "key_count": 3
    },
    {
      "platform": "anthropic",
      "platform_name": "Anthropic",
      "has_config": false,          // 尚未配置
      "key_count": 2
    }
  ]
}
```

---

### 5.3 创建平台配置

**接口路径**：`POST /api/admin/platform-configs`

**请求 Body**：

```json
{
  "platform": "anthropic",
  "allowed_tiers": ["T1", "T2", "T3", "T4", "T5"],
  "cost_per_call": 20,
  "token_cost_config": {
    "enabled": true,
    "input_cost": 0.04,
    "output_cost": 0.08
  },
  "is_active": true,
  "description": "Anthropic Claude 系列模型"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform config created successfully",
  "data": {
    "id": 4,
    "platform": "anthropic",
    "platform_name": "Anthropic",
    "allowed_tiers": ["T1", "T2", "T3", "T4", "T5"],
    "cost_per_call": 20,
    "token_cost_config": {
      "enabled": true,
      "input_cost": 0.04,
      "output_cost": 0.08
    },
    "is_active": true,
    "description": "Anthropic Claude 系列模型",
    "created_at": "2024-03-21T10:00:00Z",
    "updated_at": "2024-03-21T10:00:00Z"
  }
}
```

---

### 5.4 更新平台配置

**接口路径**：`PATCH /api/admin/platform-configs/{id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 平台配置 ID |

**请求 Body**（所有字段可选）：

```json
{
  "allowed_tiers": ["T2", "T3", "T4", "T5"],
  "cost_per_call": 15,
  "token_cost_config": {
    "enabled": true,
    "input_cost": 0.035,
    "output_cost": 0.07
  },
  "is_active": true,
  "description": "更新后的描述"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform config updated successfully",
  "data": null
}
```

---

### 5.5 删除平台配置

**接口路径**：`DELETE /api/admin/platform-configs/{id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 平台配置 ID |

**响应示例**：

```json
{
  "code": 0,
  "message": "Platform config deleted successfully",
  "data": null
}
```

---

### 5.6 获取会员等级配置

**接口路径**：`GET /api/admin/config/membership`

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "T1": {
      "level": 1,
      "name": "T1",
      "concurrent_limit": 1,      // 并发数限制
      "queue_weight": 1,          // 队列权重
      "price": 0,                 // 价格（元/月，0 表示免费）
      "description": "免费用户"
    },
    "T2": {
      "level": 2,
      "name": "T2",
      "concurrent_limit": 3,
      "queue_weight": 2,
      "price": 29,
      "description": "基础会员"
    },
    "T3": {
      "level": 3,
      "name": "T3",
      "concurrent_limit": 5,
      "queue_weight": 3,
      "price": 99,
      "description": "高级会员"
    },
    "T4": {
      "level": 4,
      "name": "T4",
      "concurrent_limit": 10,
      "queue_weight": 4,
      "price": 299,
      "description": "专业会员"
    },
    "T5": {
      "level": 5,
      "name": "T5",
      "concurrent_limit": 20,
      "queue_weight": 5,
      "price": 999,
      "description": "企业会员"
    }
  }
}
```

---

### 5.7 更新会员等级配置

**接口路径**：`PUT /api/admin/config/membership`

**请求 Body**：

```json
{
  "T1": {
    "concurrent_limit": 1,
    "queue_weight": 1,
    "price": 0
  },
  "T2": {
    "concurrent_limit": 3,
    "queue_weight": 2,
    "price": 29
  },
  "T3": {
    "concurrent_limit": 5,
    "queue_weight": 3,
    "price": 99
  },
  "T4": {
    "concurrent_limit": 10,
    "queue_weight": 4,
    "price": 299
  },
  "T5": {
    "concurrent_limit": 20,
    "queue_weight": 5,
    "price": 999
  }
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Membership config updated successfully",
  "data": null
}
```

---

## 六、测试沙箱 (Playground)

### 6.1 管理员测试生成接口

**接口路径**：`POST /api/admin/test/generate`

**请求 Body**：

```json
{
  "model": "gpt-4",                  // 模型 ID
  "prompt": "生成一张日落的图片",   // 提示词
  "params": {                        // 额外参数（可选）
    "size": "1024x1024",
    "quality": "hd"
  }
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "result": {
      "url": "https://example.com/image.png",   // 生成结果 URL
      "type": "image",                          // 类型：image、video、text
      "size": 1024                              // 文件大小（字节）
    },
    "debug": {
      "key_used": "sk-proj-ab****",            // 使用的密钥（脱敏）
      "platform": "openai",                     // 平台
      "elapsed_time": 3.5,                      // 耗时（秒）
      "token_used": 500,                        // Token 消耗
      "upstream_response": {                    // 上游原始响应（可选）
        "id": "chatcmpl-123",
        "model": "gpt-4",
        "choices": []
      }
    }
  }
}
```

**说明**：
- 管理员测试接口**不扣费**
- 返回详细的 Debug 信息，方便排查问题
- `debug.upstream_response` 可以包含上游 API 的完整响应，帮助调试

---

## 附录

### A. 用户等级说明

| 等级 | 名称 | 并发限制 | 队列权重 | 价格 |
|------|------|----------|----------|------|
| 1 | T1 | 1 | 1 | 免费 |
| 2 | T2 | 3 | 2 | ¥29/月 |
| 3 | T3 | 5 | 3 | ¥99/月 |
| 4 | T4 | 10 | 4 | ¥299/月 |
| 5 | T5 | 20 | 5 | ¥999/月 |

### B. CDK 类型说明

- **once**（单次使用）：兑换后立即失效
- **multi**（可重复使用）：可多次兑换，直到面额用完

### C. 密钥状态说明

- **active**（正常）：密钥可用
- **error**（错误）：密钥验证失败或其他错误
- **rate_limit**（限流）：触发速率限制

### D. 任务状态说明

- **pending**（待处理）：任务已创建，等待执行
- **processing**（处理中）：任务正在执行
- **completed**（已完成）：任务成功完成
- **failed**（失败）：任务执行失败

---

## 开发建议

### 1. 安全性

- 所有接口必须验证 JWT Token
- 验证用户角色为 `admin`
- 敏感信息（如 API 密钥）必须脱敏处理
- 防止 SQL 注入、XSS 攻击

### 2. 性能优化

- 列表接口支持分页
- 大批量操作考虑异步处理
- 添加适当的数据库索引

### 3. 日志记录

- 记录所有管理员操作（充值、扣费、作废 CDK 等）
- 记录 API 调用日志（便于审计）

### 4. 错误处理

- 统一的错误响应格式
- 详细的错误信息（开发环境）
- 用户友好的错误提示（生产环境）

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2024-12-30 | 初始版本，定义所有管理员后台 API 接口 |

---

**文档维护**：前端团队
**联系方式**：tech@example.com
