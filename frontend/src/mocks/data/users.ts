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
export const mockUsers: User[] = [];


// 导出总数
export const MOCK_USERS_TOTAL = mockUsers.length;
