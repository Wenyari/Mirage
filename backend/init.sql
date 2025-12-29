-- 数据库初始化 SQL
-- 用于 Docker 容器启动时自动执行

USE sora_platform;

-- 插入会员等级配置 (T1-T5)
INSERT INTO membership_configs (level, name, concurrency_limit, queue_priority, remark) VALUES
(1, 'T1', 1, 0, '基础用户 - 1个并发'),
(2, 'T2', 2, 5, '进阶用户 - 2个并发'),
(3, 'T3', 3, 10, '高级用户 - 3个并发'),
(4, 'T4', 4, 15, 'VIP用户 - 4个并发 + 优先队列'),
(5, 'T5', 5, 20, '至尊VIP - 5个并发 + 最高优先级')
ON DUPLICATE KEY UPDATE
    name=VALUES(name),
    concurrency_limit=VALUES(concurrency_limit),
    queue_priority=VALUES(queue_priority),
    remark=VALUES(remark);

-- 插入模型定价配置
INSERT INTO model_pricing (model_key, base_cost, is_active, config) VALUES
('sora-v2', 100.00, 1, '{"max_duration": 60, "quality_options": ["standard", "hd"]}'),
('sora-turbo', 50.00, 1, '{"max_duration": 30, "quality_options": ["standard"]}'),
('midjourney-v6', 80.00, 1, '{"aspect_ratios": ["1:1", "16:9", "9:16"]}')
ON DUPLICATE KEY UPDATE
    base_cost=VALUES(base_cost),
    is_active=VALUES(is_active),
    config=VALUES(config);

-- 创建默认管理员账号
-- 密码: admin123 (请在生产环境中修改)
-- 密码 hash 使用 bcrypt 加密
INSERT INTO users (email, password_hash, balance, level, role, status, created_at) VALUES
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqXjqOjG8G', 10000.00, 5, 'admin', 1, NOW())
ON DUPLICATE KEY UPDATE
    role='admin',
    level=5;

-- 创建测试 CDK (可选)
-- INSERT INTO cdk (code, points, type, batch_no, status, expire_at, created_at) VALUES
-- ('TEST-100-POINTS', 100, 'universal', 'TEST-BATCH', 0, DATE_ADD(NOW(), INTERVAL 30 DAY), NOW()),
-- ('TEST-500-POINTS', 500, 'universal', 'TEST-BATCH', 0, DATE_ADD(NOW(), INTERVAL 30 DAY), NOW());
