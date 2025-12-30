// 用户 Mock 数据（根据数据库表设计）
import type { User } from '@/types/user';

// 生成随机日期
function randomDate(start: Date, end: Date): string {
  const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
  return date.toISOString();
}

// 生成随机 IP
function randomIP(): string {
  return `${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;
}

// 生成随机密码哈希（模拟）
function randomPasswordHash(): string {
  return '$2b$10$' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// 生成 50+ 条用户数据（与数据库表设计完全匹配）
export const mockUsers: User[] = Array.from({ length: 60 }, (_, index) => {
  const id = index + 1;
  const level = (Math.floor(Math.random() * 5) + 1) as 1 | 2 | 3 | 4 | 5;
  const status = Math.random() > 0.1 ? 1 : 0; // 90% 正常用户
  const role = Math.random() > 0.95 ? 'admin' : 'user'; // 5% 管理员
  const balance = Math.floor(Math.random() * 10000);
  const createdAt = randomDate(new Date(2024, 0, 1), new Date(2024, 11, 1));
  const lastLoginAt = randomDate(new Date(createdAt), new Date());

  return {
    id,
    email: `user${id}@example.com`,
    password_hash: randomPasswordHash(), // 新增：密码哈希字段
    balance,
    level,
    role,
    status,
    register_ip: randomIP(), // 现在是非空字段
    last_login_at: lastLoginAt,
    created_at: createdAt,
  };
});

// 添加一些特殊用户
mockUsers.unshift({
  id: 0,
  email: 'admin@aigc.com',
  password_hash: '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', // 模拟管理员密码
  balance: 999999,
  level: 5,
  role: 'admin',
  status: 1,
  register_ip: '127.0.0.1',
  last_login_at: new Date().toISOString(),
  created_at: '2024-01-01T00:00:00Z',
});

// 导出总数
export const MOCK_USERS_TOTAL = mockUsers.length;
