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
    "today_new_users": 42,          // 今日新增用户数
    "today_token_usage": 125000,    // 今日 Token 消耗量
    "estimated_revenue": 3580.5,    // 今日估算收入（元）
    "active_tasks": 18              // 当前活跃任务数
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
      "date": "2024-12-24",      // 日期（YYYY-MM-DD）
      "new_users": 35,           // 新增用户数
      "token_usage": 98000,      // Token 消耗量
      "revenue": 2800            // 收入（元）
    },
    {
      "date": "2024-12-25",
      "new_users": 28,
      "token_usage": 85000,
      "revenue": 2400
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
        "status": 0,                   // 状态：0=正常，1=封禁
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
  "status": 0     // 用户状态：0=正常，1=封禁（可选）
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

### 4.1 获取密钥列表

**接口路径**：`GET /api/admin/keys`

**请求参数**：无（返回所有密钥）

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "platform": "openai",           // 平台：openai、anthropic、google 等
      "key": "sk-proj-abc...xyz",     // API 密钥（后端应只返回前 10 位 + ****）
      "weight": 10,                   // 权重（用于负载均衡）
      "status": "active",             // 状态：active、error、rate_limit
      "last_used": "2024-03-20T15:30:00Z",   // 最后使用时间
      "error_message": null,          // 错误信息（status=error 时才有）
      "created_at": "2024-03-01T10:00:00Z"
    },
    {
      "id": 2,
      "platform": "openai",
      "key": "sk-proj-def...uvw",
      "weight": 5,
      "status": "rate_limit",
      "last_used": "2024-03-20T16:00:00Z",
      "error_message": "Rate limit exceeded",
      "created_at": "2024-03-05T14:00:00Z"
    }
  ]
}
```

---

### 4.2 添加密钥

**接口路径**：`POST /api/admin/keys`

**请求 Body**：

```json
{
  "platform": "openai",        // 平台
  "key": "sk-proj-abc123...",  // API 密钥
  "weight": 10                 // 权重（可选，默认 10）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Key added successfully",
  "data": {
    "id": 3,
    "platform": "openai",
    "key": "sk-proj-ab****",   // 返回时已脱敏
    "weight": 10,
    "status": "active",
    "created_at": "2024-03-20T17:00:00Z"
  }
}
```

---

### 4.3 删除密钥

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

---

### 4.4 触发健康检测

**接口路径**：`POST /api/admin/keys/check`

**请求参数**：无

**说明**：
- 触发后端异步检测所有密钥的连通性
- 建议返回一个任务 ID，前端可轮询查询检测进度
- 或者直接等待检测完成后返回结果（适用于密钥数量较少的情况）

**响应示例**（同步方式）：

```json
{
  "code": 0,
  "message": "Health check completed",
  "data": {
    "total": 10,       // 总密钥数
    "active": 8,       // 正常数量
    "error": 1,        // 错误数量
    "rate_limit": 1    // 限流数量
  }
}
```

**响应示例**（异步方式）：

```json
{
  "code": 0,
  "message": "Health check started",
  "data": {
    "task_id": "health_check_12345"   // 任务 ID，前端可用于轮询查询
  }
}
```

---

## 五、模型与配置管理 (Models & Config)

### 5.1 获取模型配置列表

**接口路径**：`GET /api/admin/models`

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "model_id": "gpt-4",              // 模型 ID
      "name": "GPT-4",                  // 模型名称
      "base_cost": 50,                  // 基础成本（每千 token）
      "price_multiplier": 1.5,          // 价格倍率
      "is_active": true,                // 是否启用
      "vip_limit": 2,                   // VIP 等级限制（0=无限制，1-5=T1-T5）
      "max_tokens": 8192,               // 最大 token 数
      "description": "GPT-4 模型"
    },
    {
      "id": 2,
      "model_id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "base_cost": 10,
      "price_multiplier": 1.0,
      "is_active": true,
      "vip_limit": 0,
      "max_tokens": 4096,
      "description": "GPT-3.5 Turbo 模型"
    }
  ]
}
```

---

### 5.2 修改模型配置

**接口路径**：`PATCH /api/admin/models/{model_id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| model_id | integer | 模型配置 ID（注意：不是 model_id 字段） |

**请求 Body**：

```json
{
  "base_cost": 50,           // 基础成本（可选）
  "price_multiplier": 1.5,   // 价格倍率（可选）
  "is_active": true,         // 是否启用（可选）
  "vip_limit": 2             // VIP 等级限制（可选）
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Model updated successfully",
  "data": null
}
```

---

### 5.3 获取会员等级配置

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

### 5.4 更新会员等级配置

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
