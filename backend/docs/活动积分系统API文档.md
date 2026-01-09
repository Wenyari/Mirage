# 活动积分系统 API 文档

## 概述

本文档描述了活动积分系统的完整 API 接口，包括用户端和管理员端接口。

**重要变更：**
- 用户积分拆分为"充值积分"和"活动积分"两种
- 消费时优先扣除活动积分，不足时扣除充值积分
- 新增每日签到、活动领取等功能

---

## 一、积分系统说明

### 1.1 积分类型

| 类型 | 字段名 | 说明 |
|------|-------|------|
| 充值积分 | `recharge_balance` | 通过 CDK 兑换、购买等方式获得 |
| 活动积分 | `activity_balance` | 通过签到、活动领取等方式获得 |
| 总余额 | `total_balance` | 两种积分的总和 |

### 1.2 扣费规则

创建任务时，系统按以下优先级扣除积分：

1. 优先扣除 `activity_balance`（活动积分）
2. 不足时扣除 `recharge_balance`（充值积分）
3. 两者合计不足时提示余额不足

**示例：**
- 用户余额：recharge_balance=100, activity_balance=50
- 任务成本：30
- 扣除结果：activity_balance=20, recharge_balance=100

### 1.3 流水记录

所有积分变动都会记录在 `transactions` 表中，新增字段：

- `balance_type`: 积分类型（`recharge` 或 `activity`）
- `activity_id`: 关联活动ID（活动相关流水）
- `type` 新增枚举值：
  - `checkin`: 签到奖励
  - `activity_grant`: 活动积分发放
  - `activity_expire`: 活动积分过期扣除

---

## 二、用户端 API

### 2.1 获取个人信息

**接口：** `GET /api/users/me`

**Headers:**
```
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "level": 3,
    "recharge_balance": 1000.00,
    "activity_balance": 500.00,
    "total_balance": 1500.00,
    "status": 1,
    "created_at": "2024-01-01T00:00:00",
    "last_checkin_at": "2024-03-01T08:00:00",
    "total_checkin_days": 15
  }
}
```

**变更说明：**
- ~~删除了 `balance` 字段~~
- 新增 `recharge_balance`、`activity_balance`、`total_balance`
- 新增 `last_checkin_at`、`total_checkin_days`

---

### 2.2 获取余额详情

**接口：** `GET /api/wallet/balance`

**Headers:**
```
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "total_balance": 1500.00,
    "recharge_balance": 1000.00,
    "activity_balance": 500.00
  }
}
```

**变更说明：**
- ~~删除了单一的 `balance` 字段~~
- 新增 `total_balance`、`recharge_balance`、`activity_balance`

---

### 2.3 获取资金流水

**接口：** `GET /api/wallet/transactions`

**Headers:**
```
Authorization: Bearer <token>
```

**参数：**
- `page`: 页码（默认 1）
- `size`: 每页大小（默认 20）

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "list": [
      {
        "id": 1,
        "user_id": 1,
        "type": "checkin",
        "balance_type": "activity",
        "amount": 10.00,
        "balance_snapshot": 510.00,
        "related_id": null,
        "activity_id": null,
        "remark": "Daily checkin (day 1)",
        "created_at": "2024-03-01T08:00:00"
      },
      {
        "id": 2,
        "type": "activity_grant",
        "balance_type": "activity",
        "amount": 100.00,
        "balance_snapshot": 600.00,
        "activity_id": 1,
        "remark": "Activity: 春季福利",
        "created_at": "2024-03-01T09:00:00"
      },
      {
        "id": 3,
        "type": "task_cost",
        "balance_type": "activity",
        "amount": -30.00,
        "balance_snapshot": 570.00,
        "related_id": "task-123",
        "remark": "Task cost (activity): task-123",
        "created_at": "2024-03-01T10:00:00"
      }
    ],
    "total": 50,
    "page": 1,
    "size": 20
  }
}
```

**变更说明：**
- 新增 `balance_type` 字段（区分充值/活动积分）
- 新增 `activity_id` 字段（关联活动）
- `type` 新增枚举值：`checkin`、`activity_grant`、`activity_expire`

---

### 2.4 每日签到

**接口：** `POST /api/activities/checkin`

**Headers:**
```
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "Checkin successful",
  "data": {
    "points": 10.00,
    "consecutive_days": 1,
    "total_checkin_days": 15,
    "current_activity_balance": 510.00,
    "total_balance": 1510.00
  }
}
```

**错误示例：**
```json
{
  "code": 400,
  "msg": "Already checked in today",
  "data": null
}
```

**说明：**
- 每日只能签到一次
- 连续签到天数从 1-7 循环
- 断签后重置为第 1 天
- 奖励积分根据连续签到天数从配置中获取

---

### 2.5 获取签到状态

**接口：** `GET /api/activities/checkin/status`

**Headers:**
```
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "has_checked_today": false,
    "consecutive_days": 2,
    "total_checkin_days": 15,
    "last_checkin_at": "2024-03-01T08:00:00",
    "next_reward": 20.00
  }
}
```

**字段说明：**
- `has_checked_today`: 今天是否已签到
- `consecutive_days`: 当前连续签到天数（0-7）
- `total_checkin_days`: 累计签到天数
- `last_checkin_at`: 最后签到时间
- `next_reward`: 下次签到奖励积分

---

### 2.6 领取活动积分

**接口：** `POST /api/activities/claim`

**Headers:**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "activity_code": "SPRING2024"
}
```

**响应示例：**
```json
{
  "code": 200,
  "msg": "Activity claimed successfully",
  "data": {
    "points": 100.00,
    "expire_at": "2024-04-01T00:00:00",
    "current_activity_balance": 610.00,
    "total_balance": 1610.00
  }
}
```

**错误示例：**
```json
{
  "code": 400,
  "msg": "Claim limit reached",
  "data": null
}
```

**说明：**
- 活动代码由管理员创建
- 可能有等级、领取次数等限制
- 积分可能有有效期（`expire_at`）

---

### 2.7 获取可用活动列表

**接口：** `GET /api/activities/list`

**说明：** 公开接口，无需登录

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "list": [
      {
        "id": 1,
        "code": "SPRING2024",
        "name": "春季福利",
        "description": "新春活动赠送积分",
        "points": 100.00,
        "expire_days": 30,
        "required_level": 1,
        "start_at": "2024-03-01T00:00:00",
        "end_at": "2024-03-31T23:59:59",
        "status": "active"
      }
    ]
  }
}
```

---

### 2.8 获取我的活动领取记录

**接口：** `GET /api/activities/my-claims`

**Headers:**
```
Authorization: Bearer <token>
```

**参数：**
- `page`: 页码（默认 1）
- `size`: 每页大小（默认 20）

**响应示例：**
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "list": [
      {
        "id": 1,
        "user_id": 1,
        "activity_id": 1,
        "activity_name": "春季福利",
        "activity_code": "SPRING2024",
        "points_granted": 100.00,
        "expire_at": "2024-04-01T00:00:00",
        "status": "active",
        "claimed_at": "2024-03-01T09:00:00",
        "expired_at": null
      }
    ],
    "total": 5,
    "page": 1,
    "size": 20
  }
}
```

**status 说明：**
- `active`: 积分有效
- `expired`: 积分已过期
- `used`: 积分已使用

---

## 三、管理员端 API

### 3.1 创建活动

**接口：** `POST /api/admin/activities`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**请求体：**
```json
{
  "code": "SPRING2024",
  "name": "春季福利",
  "description": "新春活动赠送积分",
  "points": 100,
  "expire_days": 30,
  "max_claims_per_user": 1,
  "required_level": 1,
  "start_at": "2024-03-01T00:00:00",
  "end_at": "2024-03-31T23:59:59"
}
```

**字段说明：**
- `code`: 活动代码（必填，唯一）
- `name`: 活动名称（必填）
- `description`: 活动描述（可选）
- `points`: 赠送积分（必填）
- `expire_days`: 积分有效期（天数，可选，null表示永久）
- `max_claims_per_user`: 每用户最多领取次数（默认 1）
- `required_level`: 要求的最低会员等级（可选）
- `start_at`: 活动开始时间（可选）
- `end_at`: 活动结束时间（可选）

**响应示例：**
```json
{
  "code": 0,
  "message": "Activity created successfully",
  "data": {
    "id": 1,
    "code": "SPRING2024",
    "name": "春季福利",
    ...
  }
}
```

---

### 3.2 更新活动

**接口：** `PUT /api/admin/activities/<activity_id>`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**请求体：**
```json
{
  "name": "春季福利（更新）",
  "description": "更新后的描述",
  "status": "paused"
}
```

**可更新字段：**
- `name`、`description`、`points`、`expire_days`
- `max_claims_per_user`、`required_level`
- `start_at`、`end_at`、`status`

**响应示例：**
```json
{
  "code": 0,
  "message": "Activity updated successfully",
  "data": {...}
}
```

---

### 3.3 删除活动

**接口：** `DELETE /api/admin/activities/<activity_id>`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**响应示例：**
```json
{
  "code": 0,
  "message": "Activity deleted successfully",
  "data": null
}
```

**注意：**
- 如果活动已有领取记录，无法删除
- 建议使用更新接口将 `status` 设为 `ended` 而不是删除

---

### 3.4 获取活动列表

**接口：** `GET /api/admin/activities`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**参数：**
- `page`: 页码（默认 1）
- `size`: 每页大小（默认 20）
- `status`: 状态筛选（可选，值：active/paused/ended）

**响应示例：**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "list": [...],
    "total": 10,
    "page": 1,
    "size": 20
  }
}
```

---

### 3.5 获取活动统计

**接口：** `GET /api/admin/activities/<activity_id>/stats`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**响应示例：**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "activity_id": 1,
    "total_claims": 150,
    "unique_users": 120,
    "total_points_granted": 15000.00,
    "active_claims": 100,
    "expired_claims": 30,
    "used_claims": 20
  }
}
```

**字段说明：**
- `total_claims`: 总领取次数
- `unique_users`: 领取用户数
- `total_points_granted`: 总赠送积分
- `active_claims`: 有效领取记录数
- `expired_claims`: 已过期记录数
- `used_claims`: 已使用记录数

---

### 3.6 获取签到配置

**接口：** `GET /api/admin/checkin/config`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**响应示例：**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "list": [
      {"id": 1, "day": 1, "points": 10.00, "is_active": true},
      {"id": 2, "day": 2, "points": 15.00, "is_active": true},
      {"id": 3, "day": 3, "points": 20.00, "is_active": true},
      {"id": 4, "day": 4, "points": 25.00, "is_active": true},
      {"id": 5, "day": 5, "points": 30.00, "is_active": true},
      {"id": 6, "day": 6, "points": 40.00, "is_active": true},
      {"id": 7, "day": 7, "points": 50.00, "is_active": true}
    ]
  }
}
```

---

### 3.7 更新签到配置

**接口：** `PUT /api/admin/checkin/config`

**Headers:**
```
Authorization: Bearer <token>
```

**权限：** 需要管理员权限

**请求体：**
```json
{
  "configs": [
    {"day": 1, "points": 10.00, "is_active": true},
    {"day": 2, "points": 15.00, "is_active": true},
    {"day": 3, "points": 20.00, "is_active": true},
    {"day": 4, "points": 25.00, "is_active": true},
    {"day": 5, "points": 30.00, "is_active": true},
    {"day": 6, "points": 40.00, "is_active": true},
    {"day": 7, "points": 50.00, "is_active": true}
  ]
}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "Checkin config updated successfully",
  "data": null
}
```

---

## 四、前端集成指南

### 4.1 显示用户余额

```javascript
// 获取用户信息
const response = await fetch('/api/users/me', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data } = await response.json();

// 显示余额
console.log(`总余额: ${data.total_balance}`);
console.log(`充值积分: ${data.recharge_balance}`);
console.log(`活动积分: ${data.activity_balance}`);
```

### 4.2 实现签到功能

```javascript
// 获取签到状态
const statusRes = await fetch('/api/activities/checkin/status', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data: status } = await statusRes.json();

if (!status.has_checked_today) {
  // 显示签到按钮
  // 用户点击后调用签到接口
  const checkinRes = await fetch('/api/activities/checkin', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { data: result } = await checkinRes.json();

  alert(`签到成功！获得 ${result.points} 积分`);
}
```

### 4.3 实现活动领取

```javascript
// 获取可用活动列表
const activitiesRes = await fetch('/api/activities/list');
const { data: activities } = await activitiesRes.json();

// 显示活动列表，用户点击领取
async function claimActivity(activityCode) {
  const response = await fetch('/api/activities/claim', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ activity_code: activityCode })
  });

  if (response.ok) {
    const { data } = await response.json();
    alert(`领取成功！获得 ${data.points} 积分`);
  } else {
    const { msg } = await response.json();
    alert(`领取失败：${msg}`);
  }
}
```

### 4.4 显示流水记录

```javascript
// 获取流水记录
const transRes = await fetch('/api/wallet/transactions?page=1&size=20', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data: transactions } = await transRes.json();

// 显示流水类型的中文标签
const typeLabels = {
  'recharge': 'CDK充值',
  'task_cost': '任务消费',
  'refund': '退款',
  'checkin': '每日签到',
  'activity_grant': '活动奖励',
  'activity_expire': '积分过期'
};

// 显示积分类型的标签
const balanceTypeLabels = {
  'recharge': '充值积分',
  'activity': '活动积分'
};

transactions.list.forEach(t => {
  console.log(`${typeLabels[t.type]} (${balanceTypeLabels[t.balance_type]}): ${t.amount}`);
});
```

---

## 五、错误码说明

| HTTP 状态码 | code | 说明 |
|------------|------|------|
| 200 | 200 | 成功（用户端） |
| 200 | 0 | 成功（管理员端） |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权（未登录或 token 过期） |
| 403 | 403 | 权限不足（非管理员） |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误 |

**常见业务错误：**
- "Already checked in today" - 今日已签到
- "Claim limit reached" - 达到领取上限
- "Activity not found" - 活动不存在
- "Activity has ended" - 活动已结束
- "Requires level TX or higher" - 等级不足

---

## 六、测试建议

### 6.1 单元测试

```bash
# 测试签到功能
POST /api/activities/checkin
验证：今天第一次签到成功
验证：今天第二次签到失败

# 测试领取功能
POST /api/activities/claim
验证：首次领取成功
验证：超过次数限制失败
验证：等级不足失败

# 测试余额扣除
POST /api/tasks/submit
验证：优先扣除活动积分
验证：活动积分不足时扣除充值积分
```

### 6.2 集成测试流程

1. 管理员创建活动（`POST /api/admin/activities`）
2. 用户签到（`POST /api/activities/checkin`）
3. 用户领取活动（`POST /api/activities/claim`）
4. 查看余额变化（`GET /api/wallet/balance`）
5. 创建任务（`POST /api/tasks/submit`）
6. 查看流水记录（`GET /api/wallet/transactions`）

---

## 七、注意事项

1. **时区处理**：所有时间字段均为 UTC 时间，前端需根据用户时区转换
2. **积分过期**：定时任务每小时执行一次，处理过期积分
3. **并发安全**：扣费和签到使用悲观锁，保证并发安全
4. **流水记录**：所有积分变动都有流水，支持审计和回溯
5. **向后兼容**：系统未上线，无向后兼容需求

---

## 八、联系支持

如有疑问或发现问题，请联系后端开发团队或提交 Issue。
