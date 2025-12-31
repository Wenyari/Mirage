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
  // 批次1：100积分一次性码（部分已使用）
  {
    id: 1,
    code: 'CDK1-ABCD-EFGH-IJKL-MNOP',
    points: 100,
    type: 'once',
    batch_no: 'BATCH-2024-001',
    status: 1,
    used_by: 3,
    used_at: '2024-01-15T10:30:00.000Z',
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-01-01T00:00:00.000Z',
  },
  {
    id: 2,
    code: 'CDK2-QRST-UVWX-YZ12-3456',
    points: 100,
    type: 'once',
    batch_no: 'BATCH-2024-001',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-01-01T00:00:00.000Z',
  },
  {
    id: 3,
    code: 'CDK3-7890-ABCD-EFGH-IJKL',
    points: 100,
    type: 'once',
    batch_no: 'BATCH-2024-001',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-01-01T00:00:00.000Z',
  },
  // 批次2：500积分通用码
  {
    id: 4,
    code: 'UNIV-2024-NEWUSER-WELCOME',
    points: 500,
    type: 'universal',
    batch_no: 'BATCH-2024-002',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-06-30T23:59:59.000Z',
    created_at: '2024-01-10T00:00:00.000Z',
  },
  // 批次3：1000积分一次性码（高价值）
  {
    id: 5,
    code: 'VIP1-2024-MNOP-QRST-UVWX',
    points: 1000,
    type: 'once',
    batch_no: 'BATCH-2024-003',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2025-12-31T23:59:59.000Z',
    created_at: '2024-02-01T00:00:00.000Z',
  },
  {
    id: 6,
    code: 'VIP2-2024-YZ12-3456-7890',
    points: 1000,
    type: 'once',
    batch_no: 'BATCH-2024-003',
    status: 1,
    used_by: 5,
    used_at: '2024-02-15T14:20:00.000Z',
    expire_at: '2025-12-31T23:59:59.000Z',
    created_at: '2024-02-01T00:00:00.000Z',
  },
  // 批次4：已作废的测试码
  {
    id: 7,
    code: 'TEST-VOID-ABCD-EFGH-IJKL',
    points: 50,
    type: 'once',
    batch_no: 'BATCH-TEST-001',
    status: 2,
    used_by: null,
    used_at: null,
    expire_at: '2024-03-31T23:59:59.000Z',
    created_at: '2024-01-05T00:00:00.000Z',
  },
  {
    id: 8,
    code: 'TEST-VOID-MNOP-QRST-UVWX',
    points: 50,
    type: 'once',
    batch_no: 'BATCH-TEST-001',
    status: 2,
    used_by: null,
    used_at: null,
    expire_at: '2024-03-31T23:59:59.000Z',
    created_at: '2024-01-05T00:00:00.000Z',
  },
  // 批次5：活动通用码（多次使用）
  {
    id: 9,
    code: 'SPRING2024-FESTIVAL-GIFT',
    points: 200,
    type: 'universal',
    batch_no: 'BATCH-2024-SPRING',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-04-30T23:59:59.000Z',
    created_at: '2024-03-01T00:00:00.000Z',
  },
  // 批次6：最近生成的批量码
  {
    id: 10,
    code: 'NEW1-2024-ABCD-EFGH-1234',
    points: 300,
    type: 'once',
    batch_no: 'BATCH-2024-004',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-03-15T00:00:00.000Z',
  },
  {
    id: 11,
    code: 'NEW2-2024-IJKL-MNOP-5678',
    points: 300,
    type: 'once',
    batch_no: 'BATCH-2024-004',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-03-15T00:00:00.000Z',
  },
  {
    id: 12,
    code: 'NEW3-2024-QRST-UVWX-9012',
    points: 300,
    type: 'once',
    batch_no: 'BATCH-2024-004',
    status: 0,
    used_by: null,
    used_at: null,
    expire_at: '2024-12-31T23:59:59.000Z',
    created_at: '2024-03-15T00:00:00.000Z',
  },
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
    newCDKs.push({
      id: nextCDKId++,
      code: generateCode(),
      points,
      type,
      batch_no: batchNo,
      status: 0,
      used_by: null,
      used_at: null,
      expire_at: expireAt || null,
      created_at: now,
    });
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
  mockCDKList.forEach((cdk) => {
    if (ids.includes(cdk.id) && cdk.status === 0) {
      cdk.status = 2;
    }
  });
}

/**
 * 作废 CDK（按批次号）
 */
export function voidCDKsByBatchNo(batchNo: string): void {
  mockCDKList.forEach((cdk) => {
    if (cdk.batch_no === batchNo && cdk.status === 0) {
      cdk.status = 2;
    }
  });
}
