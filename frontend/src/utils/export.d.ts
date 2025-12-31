import type { CDK } from '@/types/cdk';
/**
 * 导出 CDK 列表到 Excel
 */
export declare function exportCDKToExcel(cdkList: CDK[], filename?: string): void;
/**
 * 导出生成的 CDK 代码列表到 Excel（仅包含兑换码）
 */
export declare function exportCDKCodesToExcel(codes: string[], batchNo: string, points: number, filename?: string): void;
/**
 * 通用的 JSON 数据导出到 Excel
 */
export declare function exportToExcel<T extends Record<string, any>>(data: T[], filename: string, sheetName?: string): void;
