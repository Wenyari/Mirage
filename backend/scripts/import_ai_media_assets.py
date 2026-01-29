"""
AI媒体资产数据导入脚本
从 final_data_to_sync.json 导入数据到数据库
使用Flask应用上下文,可在Docker容器内运行
"""
import json
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import AiMediaAsset


def import_media_assets(json_file='scripts/final_data_to_sync.json'):
    """
    从JSON文件导入AI媒体资产数据
    
    Args:
        json_file: JSON文件路径(相对于项目根目录)
    """
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查JSON文件是否存在
        if not os.path.exists(json_file):
            print(f"❌ 错误: 找不到文件 {json_file}")
            return
        
        # 读取JSON数据
        print(f"📖 正在读取 {json_file} ...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON文件读取成功,共 {len(data)} 条数据")
        
        # 创建表(如果不存在)
        print("🔧 检查数据库表...")
        db.create_all()
        print("✅ 表结构检查完成")
        
        # 获取现有的source_id集合(用于去重)
        print("🔍 检查现有数据...")
        existing_source_ids = set(
            item[0] for item in db.session.query(AiMediaAsset.source_id).all()
        )
        print(f"📊 数据库中已有 {len(existing_source_ids)} 条记录")
        
        # 过滤并导入数据
        new_count = 0
        skip_count = 0
        error_count = 0
        
        print("🚀 开始导入数据...")
        for idx, item in enumerate(data, 1):
            source_id = item.get('source_id')
            
            # 检查是否已存在
            if source_id in existing_source_ids:
                skip_count += 1
                continue
            
            try:
                # 创建新记录
                asset = AiMediaAsset(
                    source_id=source_id,
                    title=item.get('title'),
                    media_type=item.get('media_type', 'image'),
                    prompt_en=item.get('prompt_en'),
                    prompt_zh=item.get('prompt_zh'),
                    width=item.get('width', 0),
                    height=item.get('height', 0),
                    r2_key=item.get('r2_keys', []),
                    r2_url=item.get('r2_urls', []),
                    cover_r2_key=item.get('cover_r2_key'),
                    cover_r2_url=item.get('cover_r2_url')
                )
                
                db.session.add(asset)
                existing_source_ids.add(source_id)
                new_count += 1
                
                # 每100条提交一次
                if new_count % 100 == 0:
                    db.session.commit()
                    print(f"  ⏳ 已导入 {new_count} 条新数据...")
                
            except Exception as e:
                error_count += 1
                print(f"  ⚠️  导入失败 [{idx}]: {str(e)}")
                db.session.rollback()
        
        # 最终提交
        try:
            db.session.commit()
            print(f"\n{'='*50}")
            print(f"✅ 数据导入完成!")
            print(f"{'='*50}")
            print(f"📊 统计信息:")
            print(f"  - 新导入: {new_count} 条")
            print(f"  - 已跳过: {skip_count} 条 (重复)")
            print(f"  - 失败: {error_count} 条")
            print(f"  - 总计: {len(data)} 条")
            print(f"{'='*50}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 提交事务失败: {str(e)}")


if __name__ == "__main__":
    import_media_assets()
