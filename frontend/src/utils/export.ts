import * as XLSX from 'xlsx';
import type { CDK } from '@/types/cdk';

/**
 * 导出 CDK 列表到 Excel
 */
export function exportCDKToExcel(cdkList: CDK[], filename: string = 'cdk-export'): void {
  // 准备导出数据
  const exportData = cdkList.map((cdk) => ({
    '兑换码': cdk.code,
    '积分面额': cdk.points,
    '类型': cdk.type === 'once' ? '一次性' : '通用码',
    '批次号': cdk.batch_no || '-',
    '状态': cdk.status === 0 ? '未使用' : cdk.status === 1 ? '已使用' : '已作废',
    '使用者ID': cdk.used_by || '-',
    '使用时间': cdk.used_at ? new Date(cdk.used_at).toLocaleString('zh-CN') : '-',
    '过期时间': cdk.expire_at ? new Date(cdk.expire_at).toLocaleString('zh-CN') : '-',
    '创建时间': new Date(cdk.created_at).toLocaleString('zh-CN'),
  }));

  // 创建工作表
  const worksheet = XLSX.utils.json_to_sheet(exportData);

  // 设置列宽
  const columnWidths = [
    { wch: 30 }, // 兑换码
    { wch: 12 }, // 积分面额
    { wch: 10 }, // 类型
    { wch: 20 }, // 批次号
    { wch: 10 }, // 状态
    { wch: 12 }, // 使用者ID
    { wch: 20 }, // 使用时间
    { wch: 20 }, // 过期时间
    { wch: 20 }, // 创建时间
  ];
  worksheet['!cols'] = columnWidths;

  // 创建工作簿
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'CDK列表');

  // 导出文件
  const timestamp = new Date().getTime();
  XLSX.writeFile(workbook, `${filename}-${timestamp}.xlsx`);
}

/**
 * 导出生成的 CDK 代码列表到 Excel（仅包含兑换码）
 */
export function exportCDKCodesToExcel(
  codes: string[],
  batchNo: string,
  points: number,
  filename: string = 'cdk-codes'
): void {
  // 准备导出数据
  const exportData = codes.map((code, index) => ({
    '序号': index + 1,
    '兑换码': code,
    '积分面额': points,
    '批次号': batchNo,
  }));

  // 创建工作表
  const worksheet = XLSX.utils.json_to_sheet(exportData);

  // 设置列宽
  const columnWidths = [
    { wch: 8 },  // 序号
    { wch: 30 }, // 兑换码
    { wch: 12 }, // 积分面额
    { wch: 20 }, // 批次号
  ];
  worksheet['!cols'] = columnWidths;

  // 创建工作簿
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'CDK兑换码');

  // 导出文件
  const timestamp = new Date().getTime();
  XLSX.writeFile(workbook, `${filename}-${timestamp}.xlsx`);
}

/**
 * 通用的 JSON 数据导出到 Excel
 */
export function exportToExcel<T extends Record<string, any>>(
  data: T[],
  filename: string,
  sheetName: string = 'Sheet1'
): void {
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  // 创建工作表
  const worksheet = XLSX.utils.json_to_sheet(data);

  // 创建工作簿
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

  // 导出文件
  const timestamp = new Date().getTime();
  XLSX.writeFile(workbook, `${filename}-${timestamp}.xlsx`);
}
