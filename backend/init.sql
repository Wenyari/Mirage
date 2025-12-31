-- 数据库初始化 SQL
-- 用于 Docker 容器启动时自动执行

USE sora_platform;

-- 插入会员等级配置 (T1-T5)
INSERT INTO membership_configs (level, name, concurrent_limit, queue_weight, price, description) VALUES
(1, 'T1', 1, 1, 0.00, '免费用户'),
(2, 'T2', 3, 2, 29.00, '基础会员'),
(3, 'T3', 5, 3, 99.00, '高级会员'),
(4, 'T4', 10, 4, 299.00, '专业会员'),
(5, 'T5', 20, 5, 999.00, '旗舰会员')
ON DUPLICATE KEY UPDATE
    name=VALUES(name),
    concurrent_limit=VALUES(concurrent_limit),
    queue_weight=VALUES(queue_weight),
    price=VALUES(price),
    description=VALUES(description);

-- 插入平台基本信息
INSERT INTO platforms (`key`, name, enabled, description, color, icon_url, max_concurrency_limit) VALUES
('openai', 'OpenAI', 1, 'OpenAI GPT 系列模型', 'bg-green-500', NULL, 20),
('sora', 'Sora', 1, 'OpenAI Sora 视频生成模型', 'bg-blue-500', NULL, 10),
('midjourney', 'Midjourney', 1, 'Midjourney 图像生成', 'bg-purple-500', NULL, 15)
ON DUPLICATE KEY UPDATE
    name=VALUES(name),
    enabled=VALUES(enabled),
    description=VALUES(description),
    color=VALUES(color),
    max_concurrency_limit=VALUES(max_concurrency_limit);

-- 插入平台配置
INSERT INTO platform_configs (platform, allowed_tiers, cost_per_call, token_cost_config, is_active, description) VALUES
('openai', '["T1","T2","T3","T4","T5"]', 10.00, '{"enabled":true,"input_cost":0.03,"output_cost":0.06}', 1, 'OpenAI GPT 模型配置'),
('sora', '["T3","T4","T5"]', 100.00, '{"enabled":false}', 1, 'Sora 视频生成配置'),
('midjourney', '["T2","T3","T4","T5"]', 50.00, '{"enabled":false}', 1, 'Midjourney 图像生成配置')
ON DUPLICATE KEY UPDATE
    allowed_tiers=VALUES(allowed_tiers),
    cost_per_call=VALUES(cost_per_call),
    token_cost_config=VALUES(token_cost_config),
    is_active=VALUES(is_active),
    description=VALUES(description);

-- 创建默认管理员账号
-- 密码: admin123 (请在生产环境中修改)
-- 密码 hash 使用 bcrypt 加密
INSERT INTO users (email, password_hash, balance, level, role, status, created_at) VALUES
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqXjqOjG8G', 10000.00, 5, 'admin', 1, NOW())
ON DUPLICATE KEY UPDATE
    role='admin',
    level=5;

-- 注意：API 密钥需要手动添加，不在初始化 SQL 中提供
-- 请使用管理界面或直接在数据库中添加您的 API 密钥
