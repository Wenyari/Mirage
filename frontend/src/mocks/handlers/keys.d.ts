/**
 * 密钥池管理相关的 Mock 处理器
 *
 * 注意：已修改为直连后端模式 (passthrough)，不再拦截请求。
 * 如需恢复 Mock 模式，请回滚此文件修改。
 */
export declare const keysHandlers: import("msw").HttpHandler[];
