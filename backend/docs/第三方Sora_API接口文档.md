# Sora 视频生成 API 接口文档

## 📋 概述

本文档描述了前端调用后端 Sora 视频生成服务的 API 接口规范。前端通过这些接口可以提交视频生成任务、查询任务状态、管理用户任务历史等。

## 🔗 API 基础信息

- **基础 URL**: `http://localhost:5000/api` (开发环境)
- **认证方式**: JWT Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON

## 🔐 认证说明

所有接口都需要在请求头中包含 JWT Token：

```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
}
```

## 📤 1. 提交视频生成任务

### 接口信息
- **URL**: `/api/tasks`
- **方法**: POST
- **权限**: 已登录用户

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `model` | string | 是 | 模型类型 | `"sora-2"` 或 `"sora-2-pro"` |
| `prompt` | string | 是 | 视频生成提示词 | `"A beautiful sunset over the ocean"` |
| `params` | object | 否 | 高级参数 | `{}` |
| `params.aspect_ratio` | string | 否 | 宽高比 | `"16:9"` 或 `"9:16"` |
| `params.hd` | boolean | 否 | 高清模式 (仅sora-2-pro) | `false` |
| `params.duration` | number | 否 | 视频时长(秒) | `10` |

### 前端请求示例

```javascript
// 提交视频生成任务
const response = await fetch('http://localhost:5000/api/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_JWT_TOKEN'  // 从登录接口获取
  },
  body: JSON.stringify({
    "model": "sora-2",
    "prompt": "A cinematic drone shot of a futuristic cyberpunk city, neon lights, rain, hyper-realistic, 4k",
    "params": {
      "aspect_ratio": "16:9",
      "hd": false,
      "duration": 10
    }
  })
});

const result = await response.json();
```

### 成功响应

```json
{
  "code": 200,
  "msg": "Task submitted successfully",
  "data": {
    "task_id": "uuid-string-here",
    "status": "pending"
  }
}
```

### 错误响应

```json
// 余额不足
{
  "code": 400,
  "msg": "Insufficient balance. Required: 100.00, Available: 50.00",
  "data": null
}

// 并发超限
{
  "code": 400,
  "msg": "Task limit exceeded. You can run at most 3 tasks simultaneously",
  "data": null
}

// 未认证
{
  "code": 401,
  "msg": "Missing Authorization Header",
  "data": null
}
```

## 📥 2. 查询任务状态

### 接口信息
- **URL**: `/api/tasks/{task_id}`
- **方法**: GET
- **权限**: 任务所有者

### URL 参数
- `task_id`: 任务ID (从提交接口获取)

### 前端请求示例

```javascript
// 查询任务状态 (轮询)
const response = await fetch(`http://localhost:5000/api/tasks/${taskId}`, {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});

const result = await response.json();
```

### 响应格式

#### 任务处理中
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "id": "task-uuid",
    "status": "processing",  // pending/processing
    "progress": 50,          // 进度百分比 (可选)
    "result_url": null,
    "fail_reason": null,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z"
  }
}
```

#### 任务成功完成
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "id": "task-uuid",
    "status": "success",
    "progress": 100,
    "result_url": "https://cdn.example.com/videos/generated-video.mp4",
    "fail_reason": null,
    "created_at": "2024-01-01T12:00:00Z",
    "finished_at": "2024-01-01T12:15:00Z"
  }
}
```

#### 任务失败
```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "id": "task-uuid",
    "status": "failed",
    "progress": 0,
    "result_url": null,
    "fail_reason": "Content violation: NSFW content detected",
    "created_at": "2024-01-01T12:00:00Z",
    "finished_at": "2024-01-01T12:02:00Z"
  }
}
```

### 轮询建议

```javascript
// 前端轮询任务状态的建议实现
async function pollTaskStatus(taskId, token, onProgress, onComplete, onError) {
  const pollInterval = 5000; // 5秒轮询一次

  const poll = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/tasks/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const result = await response.json();

      if (result.code !== 200) {
        onError(result.msg);
        return;
      }

      const task = result.data;
      onProgress(task);

      if (task.status === 'success') {
        onComplete(task);
      } else if (task.status === 'failed') {
        onError(task.fail_reason || 'Task failed');
      } else {
        // 继续轮询
        setTimeout(poll, pollInterval);
      }
    } catch (error) {
      onError('Network error');
    }
  };

  poll();
}
```

## 📋 3. 获取任务历史

### 接口信息
- **URL**: `/api/tasks`
- **方法**: GET
- **权限**: 已登录用户

### 查询参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `page` | number | 否 | 页码 (从1开始) | `1` |
| `size` | number | 否 | 每页数量 | `20` |

### 前端请求示例

```javascript
// 获取任务历史
const response = await fetch('http://localhost:5000/api/tasks?page=1&size=20', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});

const result = await response.json();
```

### 响应格式

```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "list": [
      {
        "id": "task-uuid-1",
        "model": "sora-2",
        "prompt": "A beautiful sunset...",
        "status": "success",
        "result_url": "https://cdn.example.com/video1.mp4",
        "cost_points": 100.00,
        "created_at": "2024-01-01T12:00:00Z",
        "finished_at": "2024-01-01T12:10:00Z"
      },
      {
        "id": "task-uuid-2",
        "model": "sora-2-pro",
        "prompt": "Cyberpunk city...",
        "status": "processing",
        "result_url": null,
        "cost_points": 200.00,
        "created_at": "2024-01-01T12:05:00Z",
        "finished_at": null
      }
    ],
    "total": 45,
    "page": 1,
    "size": 20
  }
}
```

## 📊 任务状态说明

| 状态值 | 说明 | 前端处理建议 |
|--------|------|-------------|
| `pending` | 任务已提交，等待处理 | 显示"排队中"，继续轮询 |
| `processing` | 任务正在生成中 | 显示进度条，继续轮询 |
| `success` | 任务成功完成 | 显示视频播放器，停止轮询 |
| `failed` | 任务执行失败 | 显示错误信息，停止轮询 |

## ⚠️ 注意事项

### 1. 并发限制
- 不同会员等级有不同的并发任务数限制
- 前端应该在用户界面显示当前并发使用情况

### 2. 费用扣除
- 任务提交时会预扣费用
- 成功完成：费用确认扣除
- 失败时：自动退款到用户账户

### 3. 内容审核
- 系统会对输入的 prompt 进行内容审核
- 违规内容会被拒绝，任务状态为 `failed`

### 4. 超时处理
- 单个任务最长处理时间为10分钟
- 如果超时仍未完成，会被标记为失败并退款

### 5. 错误处理
- 网络错误：建议重试
- 认证错误：跳转登录页
- 余额不足：提示充值
- 系统错误：显示友好提示，建议稍后重试

## 🔄 完整使用流程

```javascript
// 1. 用户输入参数
const taskParams = {
  model: "sora-2",
  prompt: "A beautiful landscape",
  params: {
    aspect_ratio: "16:9",
    duration: 10
  }
};

// 2. 提交任务
const submitResponse = await fetch('/api/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${userToken}`
  },
  body: JSON.stringify(taskParams)
});

const submitResult = await submitResponse.json();
const taskId = submitResult.data.task_id;

// 3. 开始轮询状态
pollTaskStatus(taskId, userToken,
  (task) => {
    // 更新进度
    updateProgress(task.status, task.progress);
  },
  (task) => {
    // 成功完成
    showVideoPlayer(task.result_url);
  },
  (error) => {
    // 处理错误
    showError(error);
  }
);
```

## 🧪 测试验证

后端已包含完整的API测试套件：

```bash
# 运行所有任务API测试
cd backend
python -m pytest tests/test_api/test_tasks.py -v

# 运行第三方API集成测试
python -m pytest tests/test_api/test_tasks.py::TestSoraThirdPartyAPI -v
```

## 📞 技术支持

前端集成遇到问题时，请检查：
1. JWT Token 是否有效
2. 请求头格式是否正确
3. 网络连接是否正常
4. 查看浏览器开发者工具的网络面板
5. 检查后端日志获取详细错误信息
