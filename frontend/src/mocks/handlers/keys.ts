import { http, passthrough } from 'msw';

/**
 * 密钥池管理相关的 Mock 处理器
 * 
 * 注意：已修改为直连后端模式 (passthrough)，不再拦截请求。
 * 如需恢复 Mock 模式，请回滚此文件修改。
 */
export const keysHandlers = [
  /**
   * 获取模型列表
   * GET /api/admin/models
   */
  http.get('/api/admin/models', () => {
    return passthrough();
  }),

  /**
   * 获取密钥列表
   * GET /api/admin/keys
   */
  http.get('/api/admin/keys', () => {
    return passthrough();
  }),

  /**
   * 添加密钥
   * POST /api/admin/keys
   */
  http.post('/api/admin/keys', () => {
    return passthrough();
  }),

  /**
   * 批量添加密钥
   * POST /api/admin/keys/batch
   */
  http.post('/api/admin/keys/batch', () => {
    return passthrough();
  }),

  /**
   * 更新密钥配置
   * PATCH /api/admin/keys/{id}
   */
  http.patch('/api/admin/keys/:id', () => {
    return passthrough();
  }),

  /**
   * 删除密钥
   * DELETE /api/admin/keys/{id}
   */
  http.delete('/api/admin/keys/:id', () => {
    return passthrough();
  }),

  /**
   * 手动触发/解除熔断
   * POST /api/admin/keys/{id}/cooldown
   */
  http.post('/api/admin/keys/:id/cooldown', () => {
    return passthrough();
  }),

  /**
   * 触发健康检测
   * POST /api/admin/keys/health-check
   */
  http.post('/api/admin/keys/health-check', () => {
    return passthrough();
  }),

  /**
   * 获取密钥统计信息
   * GET /api/admin/keys/stats
   */
  http.get('/api/admin/keys/stats', () => {
    return passthrough();
  }),

  /**
   * 创建模型
   * POST /api/admin/models
   */
  http.post('/api/admin/models', () => {
    return passthrough();
  }),

  /**
   * 更新模型
   * PATCH /api/admin/models/:key
   */
  http.patch('/api/admin/models/:key', () => {
    return passthrough();
  }),

  /**
   * 删除模型
   * DELETE /api/admin/models/:key
   */
  http.delete('/api/admin/models/:key', () => {
    return passthrough();
  }),
];
