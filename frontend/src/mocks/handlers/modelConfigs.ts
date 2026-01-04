import { http, passthrough } from 'msw';

/**
 * 模型配置管理相关的 Mock 处理器
 * 
 * 注意：已修改为直连后端模式 (passthrough)，不再拦截请求。
 * 如需恢复 Mock 模式，请回滚此文件修改。
 */
export const modelConfigHandlers = [
  /**
   * 获取模型配置列表
   * GET /api/admin/model-configs
   */
  http.get('/api/admin/model-configs', () => {
    return passthrough();
  }),

  /**
   * 获取可配置的模型列表
   * GET /api/admin/model-configs/available-models
   */
  http.get('/api/admin/model-configs/available-models', () => {
    return passthrough();
  }),

  /**
   * 创建模型配置
   * POST /api/admin/model-configs
   */
  http.post('/api/admin/model-configs', () => {
    return passthrough();
  }),

  /**
   * 更新模型配置
   * PATCH /api/admin/model-configs/:id
   */
  http.patch('/api/admin/model-configs/:id', () => {
    return passthrough();
  }),

  /**
   * 删除模型配置
   * DELETE /api/admin/model-configs/:id
   */
  http.delete('/api/admin/model-configs/:id', () => {
    return passthrough();
  }),

  /**
   * 获取会员等级配置
   * GET /api/admin/config/membership
   */
  http.get('/api/admin/config/membership', () => {
    return passthrough();
  }),

  /**
   * 更新会员等级配置
   * PUT /api/admin/config/membership
   */
  http.put('/api/admin/config/membership', () => {
    return passthrough();
  }),
];
