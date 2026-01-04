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