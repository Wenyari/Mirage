import json
import pymysql
import os

# ================= 配置区域 =================
# 对应 docker-compose.yml 中的环境变量
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),  # 连接宿主机映射的端口
    'port': int(os.environ.get('MYSQL_PORT', 3306)),    # 对应 ports: - "3306:3306"
    'user': os.environ.get('MYSQL_USER', 'mirage_user'),
    'password': os.environ['MYSQL_PASSWORD'],
    'db': os.environ.get('MYSQL_DATABASE', 'mirage'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

JSON_FILE = 'scripts/final_data_to_sync.json'

# ================= SQL 定义 =================

# 1. 建表语句 (如果表不存在)
# 增加了 title 的索引以提高查询效率
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `ai_media_assets` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_id` VARCHAR(128) NOT NULL COMMENT '爬虫生成的唯一ID',
  `title` VARCHAR(255) COMMENT '标题',
  `media_type` VARCHAR(50) DEFAULT 'image',
  `prompt_en` TEXT COMMENT '英文提示词',
  `prompt_zh` TEXT COMMENT '中文提示词',
  `width` INT DEFAULT 0,
  `height` INT DEFAULT 0,
  `r2_key` VARCHAR(255) COMMENT 'R2存储路径',
  `r2_url` VARCHAR(512) COMMENT 'R2访问链接',
  `cover_r2_key` VARCHAR(255) COMMENT '封面路径',
  `cover_r2_url` VARCHAR(512) COMMENT '封面链接',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_title` (`title`), -- 用于标题去重加速
  UNIQUE KEY `uk_source_id` (`source_id`) -- 物理层面的唯一约束
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# 2. 插入语句
INSERT_SQL = """
INSERT INTO ai_media_assets 
(source_id, title, media_type, prompt_en, prompt_zh, width, height, r2_key, r2_url, cover_r2_key, cover_r2_url)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# ================= 核心逻辑 =================

def import_data():
    if not os.path.exists(JSON_FILE):
        print(f"错误: 找不到文件 {JSON_FILE}")
        return

    # 1. 读取 JSON 数据
    print(f"正在读取 {JSON_FILE} ...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        new_items = json.load(f)
    print(f"JSON 中共有 {len(new_items)} 条数据")

    try:
        # 2. 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("数据库连接成功")

        # 3. 如果表不存在，创建表
        cursor.execute(CREATE_TABLE_SQL)
        print("表结构检查完成 (如果不存在已自动创建)")

        # 4. 获取现有标题 (用于去重)
        # 策略：为了极致性能，先拉取所有现有标题到内存 Set 中
        print("正在获取数据库现有标题进行去重...")
        cursor.execute("SELECT title FROM ai_media_assets WHERE title IS NOT NULL")
        existing_titles = set(row['title'] for row in cursor.fetchall())
        print(f"数据库中已有 {len(existing_titles)} 条不同标题的记录")

        # 5. 过滤数据
        items_to_insert = []
        for item in new_items:
            title = item.get('title')
            # 逻辑：如果没有标题，或者是新标题，则加入待插入列表
            # 注意：如果标题为空(None)，通常建议用 source_id 去重，或者允许插入
            if title and title in existing_titles:
                continue # 跳过重复
            
            # 如果这一批次里有重复的标题，也要防止内部冲突
            if title:
                existing_titles.add(title) 

            items_to_insert.append((
                item.get('source_id'),
                item.get('title'),
                item.get('media_type', 'image'),
                item.get('prompt_en'),
                item.get('prompt_zh'),
                item.get('width', 0),
                item.get('height', 0),
                item.get('r2_key'),
                item.get('r2_url'),
                item.get('cover_r2_key'),
                item.get('cover_r2_url')
            ))

        # 6. 批量插入
        if items_to_insert:
            print(f"准备插入 {len(items_to_insert)} 条新数据...")
            # executemany 性能远高于循环 execute
            cursor.executemany(INSERT_SQL, items_to_insert)
            conn.commit()
            print("✅ 导入成功！")
        else:
            print("⚠️ 没有新数据需要导入 (全部重复)。")

    except pymysql.MySQLError as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    import_data()