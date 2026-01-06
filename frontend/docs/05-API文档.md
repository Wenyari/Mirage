# API 文档

## 简要说明

本文档详细介绍 Mirage 项目的后端 API 接口规范，包括认证、用户管理、CDK 管理、任务管理等模块的接口定义。

## API 基础信息

### 基础地址

- **开发环境**：`http://localhost:5000/api`
- **生产环境**：[待补充：生产环境地址]

**说明**：前端通过 Vite 代理自动转发 `/api` 请求到后端服务。

### 认证方式

使用 **JWT (JSON Web Token)** 认证：

```http
Authorization: Bearer <token>
```

**获取 Token**：
- 用户登录后，后端返回 JWT Token
- Token 存储在 `localStorage` 中
- 前端 Axios 拦截器自动添加到请求头

### 统一响应格式

#### 成功响应

```typescript
interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
}
```

**示例**：

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "用户名"
  },
  "message": "操作成功"
}
```

#### 错误响应

```typescript
interface ErrorResponse {
  success: false;
  message: string;
  error?: string;
}
```

**示例**：

```json
{
  "success": false,
  "message": "用户不存在",
  "error": "USER_NOT_FOUND"
}
```

### 常见状态码

| 状态码 | 说明 |
|--------|------|
| **200** | 请求成功 |
| **201** | 资源创建成功 |
| **400** | 请求参数错误 |
| **401** | 未授权（未登录或 Token 失效） |
| **403** | 无权限访问 |
| **404** | 资源不存在 |
| **500** | 服务器内部错误 |

## 认证模块 (Authentication)

### 1. 发送邮箱验证码

**接口**：`POST /api/auth/code`

**说明**：发送注册验证码到用户邮箱。

**请求参数**：

```typescript
{
  email: string;  // 邮箱地址
}
```

**响应数据**：

```typescript
{
  success: true;
  message: "验证码已发送";
}
```

**示例**：

```typescript
await authService.sendCode({ email: 'user@example.com' });
```

---

### 2. 用户注册

**接口**：`POST /api/auth/register`

**说明**：使用邮箱、验证码和密码注册新用户。

**请求参数**：

```typescript
{
  email: string;     // 邮箱地址
  code: string;      // 邮箱验证码
  password: string;  // 密码（至少 6 位）
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    user_id: number;  // 新用户 ID
  }
}
```

**示例**：

```typescript
const result = await authService.register({
  email: 'user@example.com',
  code: '123456',
  password: 'password123',
});
// result.user_id = 1
```

---

### 3. 用户登录

**接口**：`POST /api/auth/login`

**说明**：用户登录，获取 JWT Token。

**请求参数**：

```typescript
{
  email: string;     // 邮箱地址
  password: string;  // 密码
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    token: string;  // JWT Token
    user: {
      id: number;
      email: string;
      name: string;
      balance: number;
      level: number;
      status: number;
      // ...
    }
  }
}
```

**示例**：

```typescript
const { token, user } = await authService.login({
  email: 'user@example.com',
  password: 'password123',
});
// 保存 token 到 localStorage
```

---

### 4. 获取当前用户信息

**接口**：`GET /api/auth/me`

**说明**：获取当前登录用户的详细信息。

**认证**：需要 JWT Token

**响应数据**：

```typescript
{
  success: true;
  data: {
    id: number;
    email: string;
    name: string;
    balance: number;
    level: number;
    status: number;
    vip_desc?: string;  // VIP 等级描述
    // ...
  }
}
```

**示例**：

```typescript
const user = await authService.me();
```

---

### 5. 用户登出

**接口**：`POST /api/auth/logout`

**说明**：用户登出，使 Token 失效。

**认证**：需要 JWT Token

**响应数据**：

```typescript
{
  success: true;
  message: "登出成功"
}
```

**示例**：

```typescript
await authService.logout();
// 清除本地 token
```

---

## 用户管理模块 (Admin - Users)

### 1. 获取用户列表

**接口**：`GET /api/admin/users`

**说明**：分页查询用户列表（管理员功能）。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  page?: number;       // 页码（默认 1）
  page_size?: number;  // 每页数量（默认 10）
  email?: string;      // 邮箱过滤（模糊搜索）
  status?: 0 | 1;      // 状态过滤（0=禁用, 1=正常）
  level?: number;      // 等级过滤
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    list: User[];     // 用户列表
    total: number;    // 总数量
    page: number;     // 当前页
    page_size: number;
  }
}
```

**User 类型定义**：

```typescript
interface User {
  id: number;
  email: string;
  name: string;
  balance: number;        // 余额（积分）
  level: number;          // 等级
  status: number;         // 状态（0=禁用, 1=正常）
  register_time: string;  // 注册时间
  last_login: string;     // 最后登录时间
  total_spent: number;    // 总消费
}
```

**示例**：

```typescript
const { list, total } = await getUsers({
  page: 1,
  page_size: 10,
  email: 'user',
  status: 1,
});
```

---

### 2. 更新用户余额

**接口**：`PATCH /api/admin/users/:userId/balance`

**说明**：管理员手动调整用户余额（充值或扣费）。

**认证**：需要管理员 Token

**路径参数**：
- `userId` - 用户 ID

**请求参数**：

```typescript
{
  amount: number;   // 变动金额（正数=充值，负数=扣费）
  reason: string;   // 变动原因
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    new_balance: number;  // 更新后的余额
  }
}
```

**示例**：

```typescript
// 充值 100 积分
const result = await updateUserBalance(1, 100, '管理员充值');
// result.new_balance = 1100

// 扣费 50 积分
const result = await updateUserBalance(1, -50, '违规扣费');
// result.new_balance = 1050
```

---

### 3. 修改用户资料

**接口**：`PATCH /api/admin/users/:userId/profile`

**说明**：管理员修改用户资料（等级、状态等）。

**认证**：需要管理员 Token

**路径参数**：
- `userId` - 用户 ID

**请求参数**：

```typescript
{
  name?: string;     // 用户名
  level?: number;    // 等级
  status?: 0 | 1;    // 状态
}
```

**响应数据**：

```typescript
{
  success: true;
  message: "更新成功"
}
```

**示例**：

```typescript
await updateUserProfile(1, {
  level: 2,
  status: 1,
});
```

---

### 4. 导出用户数据

**接口**：`GET /api/admin/users/export`

**说明**：导出用户数据为 Excel 文件。

**认证**：需要管理员 Token

**请求参数**：与获取用户列表相同

**响应**：`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**示例**：

```typescript
const blob = await exportUsers({ status: 1 });
// 下载 Excel 文件
```

---

## CDK 管理模块 (Admin - CDK)

### 1. 生成 CDK

**接口**：`POST /api/admin/cdk/generate`

**说明**：批量生成 CDK 兑换码。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  amount: number;      // CDK 面值（积分）
  count: number;       // 生成数量
  type: string;        // CDK 类型（如 'points', 'vip'）
  batch_name?: string; // 批次名称
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    codes: string[];  // 生成的 CDK 列表
    count: number;    // 生成数量
    batch_id: string; // 批次 ID
  }
}
```

**示例**：

```typescript
const result = await generateCDK({
  amount: 100,
  count: 10,
  type: 'points',
  batch_name: '新年活动',
});
// result.codes = ['CDK-XXXX-XXXX', ...]
```

---

### 2. 获取 CDK 列表

**接口**：`GET /api/admin/cdk`

**说明**：分页查询 CDK 列表。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  page?: number;       // 页码
  limit?: number;      // 每页数量
  status?: string;     // 状态过滤（unused, used, voided）
  batch?: string;      // 批次过滤
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    list: CDK[];
    total: number;
    page: number;
    limit: number;
  }
}
```

**CDK 类型定义**：

```typescript
interface CDK {
  id: number;
  code: string;           // CDK 码
  type: string;           // 类型
  amount: number;         // 面值
  status: string;         // unused | used | voided
  batch_name: string;     // 批次名称
  created_at: string;     // 创建时间
  used_at?: string;       // 使用时间
  used_by?: number;       // 使用者 ID
}
```

**示例**：

```typescript
const { list, total } = await getCDKList({
  page: 1,
  limit: 20,
  status: 'unused',
});
```

---

### 3. 作废 CDK

**接口**：`POST /api/admin/cdk/void`

**说明**：批量作废 CDK。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  cdk_ids: number[];  // CDK ID 列表
}
```

**响应数据**：

```typescript
{
  success: true;
  message: "作废成功"
}
```

**示例**：

```typescript
await voidCDK({ cdk_ids: [1, 2, 3] });
```

---

### 4. 获取批次列表

**接口**：`GET /api/admin/cdk/batches`

**说明**：获取所有 CDK 批次名称列表。

**认证**：需要管理员 Token

**响应数据**：

```typescript
{
  success: true;
  data: string[];  // 批次名称列表
}
```

**示例**：

```typescript
const batches = await getBatchList();
// batches = ['新年活动', '春节活动', ...]
```

---

## 任务管理模块 (Tasks)

### 1. 获取任务历史

**接口**：`GET /api/tasks`

**说明**：获取当前用户的任务历史记录。

**认证**：需要用户 Token

**请求参数**：

```typescript
{
  page?: number;  // 页码（默认 1）
  size?: number;  // 每页数量（默认 20）
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    list: TaskHistoryItem[];
    total: number;
    page: number;
    size: number;
  }
}
```

**TaskHistoryItem 类型定义**：

```typescript
interface TaskHistoryItem {
  id: string;               // 任务 ID
  model: string;            // 使用的模型
  prompt: string;           // 提示词
  status: string;           // pending | processing | success | failed | cancelled
  created_at: string;       // 创建时间
  result_url?: string;      // 结果文件 URL
  thumbnail_url?: string;   // 缩略图 URL
}
```

**示例**：

```typescript
const { list, total } = await taskService.getTaskHistory(1, 20);
```

---

### 2. 获取可用模型列表

**接口**：`GET /api/tasks/models`

**说明**：获取用户可用的 AI 模型列表。

**认证**：需要用户 Token

**响应数据**：

```typescript
{
  success: true;
  data: ModelOption[];
}
```

**ModelOption 类型定义**：

```typescript
interface ModelOption {
  key: string;              // 模型标识
  name: string;             // 模型名称
  description: string;      // 模型描述
  cost_per_call: number;    // 每次调用成本
  is_available: boolean;    // 是否可用
  user_tier: string;        // 用户等级
  min_tier: string;         // 最低等级要求
  allowed_tiers: string[];  // 允许的等级
  color: string;            // 主题色
  icon_url: string;         // 图标 URL
  enabled: number;          // 是否启用
  max_concurrency_limit: number;  // 最大并发数
}
```

**示例**：

```typescript
const models = await taskService.getAvailableModels();
```

---

### 3. 提交新任务

**接口**：`POST /api/tasks`

**说明**：提交新的 AI 任务（对话、视频生成等）。

**认证**：需要用户 Token

**请求参数**：

```typescript
{
  model: string;              // 模型标识
  prompt: string;             // 提示词
  params?: Record<string, any>;  // 模型参数
  input_file_url?: string;    // 输入文件 URL
}
```

**响应数据**：

```typescript
{
  success: true;
  data: {
    task_id: string;  // 任务 ID
    status: string;   // 任务状态
  }
}
```

**示例**：

```typescript
const result = await taskService.createTask({
  model: 'gpt-4',
  prompt: '写一首关于春天的诗',
  params: { temperature: 0.7 },
});
// result.task_id = 'task-xxx'
```

---

### 4. 查询任务状态

**接口**：`GET /api/tasks/:taskId`

**说明**：查询指定任务的执行状态。

**认证**：需要用户 Token

**路径参数**：
- `taskId` - 任务 ID

**响应数据**：

```typescript
{
  success: true;
  data: {
    id: string;
    status: 'pending' | 'processing' | 'success' | 'failed' | 'cancelled';
    progress?: number;         // 进度（0-100）
    queue_info?: {
      user_queue: string;      // 队列类型
      position: number;        // 队列位置
      vip_queue: number;       // VIP 队列人数
      normal_queue: number;    // 普通队列人数
    };
    result_url?: string;       // 结果 URL
    fail_reason?: string;      // 失败原因
  }
}
```

**示例**：

```typescript
const status = await taskService.getTaskStatus('task-xxx');
if (status.status === 'success') {
  console.log('结果 URL:', status.result_url);
}
```

---

### 5. 取消任务

**接口**：`POST /api/tasks/:taskId/cancel`

**说明**：取消正在执行的任务。

**认证**：需要用户 Token

**路径参数**：
- `taskId` - 任务 ID

**响应数据**：

```typescript
{
  success: true;
  message: "任务已取消"
}
```

**示例**：

```typescript
await taskService.cancelTask('task-xxx');
```

---

## 数据概览模块 (Admin - Dashboard)

### 1. 获取统计数据

**接口**：`GET /api/admin/dashboard/stats`

**说明**：获取平台统计数据概览。

**认证**：需要管理员 Token

**响应数据**：

```typescript
{
  success: true;
  data: {
    total_users: number;        // 总用户数
    active_users: number;       // 活跃用户数
    total_revenue: number;      // 总收入
    total_tasks: number;        // 总任务数
    pending_tasks: number;      // 待处理任务数
  }
}
```

---

### 2. 获取用户增长数据

**接口**：`GET /api/admin/dashboard/user-growth`

**说明**：获取用户增长趋势数据。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  start_date?: string;  // 开始日期（YYYY-MM-DD）
  end_date?: string;    // 结束日期（YYYY-MM-DD）
}
```

**响应数据**：

```typescript
{
  success: true;
  data: Array<{
    date: string;   // 日期
    count: number;  // 新增用户数
  }>
}
```

---

### 3. 获取 Token 使用数据

**接口**：`GET /api/admin/dashboard/token-usage`

**说明**：获取 Token 使用趋势数据。

**认证**：需要管理员 Token

**请求参数**：

```typescript
{
  start_date?: string;  // 开始日期
  end_date?: string;    // 结束日期
}
```

**响应数据**：

```typescript
{
  success: true;
  data: Array<{
    date: string;    // 日期
    tokens: number;  // Token 使用量
  }>
}
```

---

## 错误处理

### 错误码说明

| 错误码 | 说明 | 处理方式 |
|--------|------|---------|
| `INVALID_TOKEN` | Token 无效或过期 | 跳转登录页 |
| `PERMISSION_DENIED` | 权限不足 | 提示用户无权限 |
| `USER_NOT_FOUND` | 用户不存在 | 提示用户不存在 |
| `INVALID_PARAMS` | 参数错误 | 检查请求参数 |
| `CDK_ALREADY_USED` | CDK 已被使用 | 提示 CDK 无效 |
| `INSUFFICIENT_BALANCE` | 余额不足 | 提示充值 |

### 前端错误处理

前端通过 Axios 响应拦截器统一处理错误：

```typescript
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 401 未授权
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }

    // 统一错误格式
    return Promise.reject({
      message: error.response?.data?.message || 'Network Error',
      status: error.response?.status,
    });
  }
);
```

## API 调用示例

### 使用 Service 层调用

```typescript
// 1. 导入 service
import { authService } from '@/services/auth';

// 2. 在组件或 Hook 中调用
async function handleLogin(email: string, password: string) {
  try {
    const { token, user } = await authService.login({ email, password });
    // 保存 token 和 user
    useAuthStore.getState().login(token, user);
  } catch (error) {
    console.error('登录失败:', error.message);
  }
}
```

### 使用 TanStack Query

```typescript
// 1. 定义 Custom Hook
export function useUsers(params: UserQueryParams) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => userService.getUsers(params),
    staleTime: 5 * 60 * 1000,
  });
}

// 2. 在组件中使用
function UserManager() {
  const { data, isLoading, error } = useUsers({ page: 1, page_size: 10 });

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>错误: {error.message}</div>;

  return <UserTable users={data.list} />;
}
```

### 使用 Mutation 更新数据

```typescript
// 1. 定义 Mutation Hook
export function useUpdateUserBalance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, amount, reason }) =>
      updateUserBalance(userId, amount, reason),
    onSuccess: () => {
      // 更新成功后，失效用户列表缓存
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

// 2. 在组件中使用
function UserBalanceDialog({ userId }) {
  const mutation = useUpdateUserBalance();

  const handleSubmit = (amount: number, reason: string) => {
    mutation.mutate({ userId, amount, reason });
  };

  return <Form onSubmit={handleSubmit} />;
}
```

## 相关链接

- [技术架构](./03-技术架构.md) - 了解 API 调用流程和网络层设计
- [核心概念](./04-核心概念.md) - 理解服务层和状态管理
