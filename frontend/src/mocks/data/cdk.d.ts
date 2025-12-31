import type { CDK } from '@/types/cdk';
/**
 * Mock CDK 数据列表
 */
export declare const mockCDKList: CDK[];
/**
 * 生成新的 CDK 列表
 */
export declare function generateMockCDKs(count: number, points: number, type: 'once' | 'universal', batchNo: string, expireAt?: string): CDK[];
/**
 * 添加 CDK 到列表
 */
export declare function addCDKsToList(cdks: CDK[]): void;
/**
 * 作废 CDK（按 ID）
 */
export declare function voidCDKsByIds(ids: number[]): void;
/**
 * 作废 CDK（按批次号）
 */
export declare function voidCDKsByBatchNo(batchNo: string): void;
