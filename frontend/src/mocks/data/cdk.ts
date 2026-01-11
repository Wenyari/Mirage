import type { CDK } from '@/types/cdk';

/**
 * 生成随机兑换码
 */
function generateCode(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 20; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
    if ((i + 1) % 4 === 0 && i < 19) code += '-';
  }
  return code;
}

/**
 * Mock CDK 数据列表
 */
export const mockCDKList: CDK[] = [
];

/**
 * 下一个可用的 CDK ID
 */
let nextCDKId = mockCDKList.length + 1;

/**
 * 生成新的 CDK 列表
 */
export function generateMockCDKs(
  count: number,
  points: number,
  type: 'once' | 'universal',
  batchNo: string,
  expireAt?: string
): CDK[] {
  const newCDKs: CDK[] = [];
  const now = new Date().toISOString();

  for (let i = 0; i < count; i++) {
  }

  return newCDKs;
}

/**
 * 添加 CDK 到列表
 */
export function addCDKsToList(cdks: CDK[]): void {
  mockCDKList.unshift(...cdks);
}

/**
 * 作废 CDK（按 ID）
 */
export function voidCDKsByIds(ids: number[]): void {
}

/**
 * 作废 CDK（按批次号）
 */
export function voidCDKsByBatchNo(batchNo: string): void {
}
