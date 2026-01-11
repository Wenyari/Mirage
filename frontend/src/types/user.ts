// 用户管理相关类型定义（根据数据库表设计）

// 用户等级类型
export type UserLevel = 1 | 2 | 3 | 4 | 5; // T1-T5

// 用户状态类型
export type UserStatus = 0 | 1; // 1=正常, 0=封禁

// 用户角色类型
export type UserRole = 'user' | 'admin';

// 用户基础信息（与数据库表设计完全匹配）
export interface User {
  id: number;
  email: string;
  password_hash: string;         // 加盐加密后的密码
  balance: number;               // 积分余额（DECIMAL(10, 2)）
  balance_detail?: {             // 余额详情（可选）
    recharge_balance: number;    // 充值余额
    activity_balance: number;    // 活动余额
  };
  level: UserLevel;              // 会员等级：1-5
  role: UserRole;                // 角色：user/admin
  status: UserStatus;            // 状态：1=正常, 0=封禁
  register_ip: string;           // 注册时的IP（用于风控）
  last_login_at: string;         // 最后登录时间
  created_at: string;            // 注册时间
}

// 用户列表查询参数
export interface UserListParams {
  page?: number;
  limit?: number;
  email?: string;
  level?: UserLevel;
  status?: UserStatus;
}

// 用户列表响应
export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  limit: number;
}

// 充值/扣费请求
export interface UpdateBalanceRequest {
  amount: number;
  reason: string;
}

// 修改用户资料请求
export interface UpdateProfileRequest {
  level?: UserLevel;
  status?: UserStatus;
}

// 用户状态枚举常量
export const USER_STATUS_LABELS = {
  0: '封禁',
  1: '正常'
} as const;

// 用户角色枚举常量
export const USER_ROLE_LABELS = {
  user: '普通用户',
  admin: '管理员'
} as const;

// 用户等级枚举常量
export const USER_LEVEL_LABELS = {
  1: 'T1',
  2: 'T2',
  3: 'T3',
  4: 'T4',
  5: 'T5'
} as const;

// 等级颜色映射
export const LEVEL_COLORS = {
  1: 'bg-gray-100 text-gray-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-green-100 text-green-800',
  4: 'bg-orange-100 text-orange-800',
  5: 'bg-purple-100 text-purple-800'
} as const;

// 用户详情（含交易记录和任务记录）
export interface UserDetails {
  user: User;
  recent_transactions: Transaction[];
  recent_tasks: Task[];
}

// 交易记录
export interface Transaction {
  id: number;
  type: 'recharge' | 'consume' | 'refund' | 'activity_grant';
  balance_type?: 'recharge' | 'activity'; // 余额类型
  activity_id?: number;                   // 活动ID
  amount: number;
  balance_snapshot?: number;              // 余额快照
  reason?: string;                        // 说明 (兼容旧字段)
  remark?: string;                        // 说明 (兼容旧字段)
  created_at: string;
}

// 任务记录
export interface Task {
  id: number;
  model: string;
  prompt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  token_used: number;
  created_at: string;
}
