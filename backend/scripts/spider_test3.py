import httpx
from bs4 import BeautifulSoup, Tag
import json
import hashlib

# !!! 请替换为包含这些卡片的实际网址 !!!
TARGET_URL = "https://soratoai.com/prompts/lists/" 

def generate_source_id(unique_string):
    """使用提示词内容的哈希作为唯一ID，防止重复"""
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def fetch_and_parse():
    print(f"1. 正在请求: {TARGET_URL} ...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 如果目标网站有分页，这里可能需要写循环逻辑
        resp = httpx.get(TARGET_URL, headers=headers, timeout=30)
        print(f"2. 请求状态码: {resp.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []

    # === 1. 定位所有卡片容器 ===
    cards = soup.find_all('div', class_='prompt-card')
    print(f"3. 找到 {len(cards)} 个提示词卡片，开始解析...")

    for card in cards:
        # === 2. 提取各个字段 ===
        
        # A. 标题
        title_tag = card.find(class_='prompt-title')
        title = title_tag.get_text(strip=True) if title_tag else "无标题"
        
        # B. 描述 (映射为中文提示词/解释)
        desc_tag = card.find(class_='prompt-description')
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        
        # C. 核心提示词 (映射为英文提示词)
        content_tag = card.find(class_='prompt-content')
        prompt_content = content_tag.get_text(strip=True) if content_tag else ""

        # === 3. 数据校验 ===
        if not prompt_content:
            continue

        # === 4. 组装数据 ===
        # 使用 content 作为唯一ID源，因为标题可能会重复
        source_id = generate_source_id(prompt_content)

        item = {
            "source_id": source_id,
            "title": title,
            
            # 映射逻辑：content是核心指令(En)，description是解释(Zh)
            "prompt_en": prompt_content,
            "prompt_zh": None,
            
            # 因为没有媒体资源，设为 None 或默认值
            "media_type": "video", # Sora 默认为视频
            "original_image_url": None,
            "width": None,
            "height": None,
            "r2_key": None,
            "r2_url": None,
            "cover_r2_key": None,
            "cover_r2_url": None
        }
        
        results.append(item)
        print(f"   -> [提取] {title}")

    return results

# ==========================================
# 本地测试用的模拟 HTML (如果你想先不联网测试解析逻辑)
# ==========================================
MOCK_HTML = """
<div class="prompt-card">
    <div class="prompt-header">
        <h3 class="prompt-title">电影预告风格场景</h3>
        <p class="prompt-description">电影预告风格场景，配有复古胶片美学和鲜艳色彩</p>
    </div>
    <div class="prompt-content-wrapper">
        <div class="prompt-content" title="点击选择全部文本">A movie trailer featuring the adventures of the 30 year old space man wearing a red wool knitted motorcycle helmet, blue sky, salt desert, cinematic style, shot on 35mm film, vivid colors.</div>
    </div>
    <div class="prompt-actions">...</div>
</div>
"""

def test_local_parsing():
    """使用上面的 HTML 片段测试解析逻辑"""
    print("\n--- 开始本地 HTML 片段测试 ---")
    soup = BeautifulSoup(MOCK_HTML, 'html.parser')
    card = soup.find('div', class_='prompt-card')
    
    if card:
        title = card.find(class_='prompt-title').get_text(strip=True)
        desc = card.find(class_='prompt-description').get_text(strip=True)
        content = card.find(class_='prompt-content').get_text(strip=True)
        
        print(f"Title: {title}")
        print(f"Desc (Zh): {desc}")
        print(f"Content (En): {content}")
        print("--- 测试通过 ---\n")

if __name__ == "__main__":
    # 1. 先运行本地测试，确保逻辑对
    # test_local_parsing()
    
    # 2. 如果填好了 TARGET_URL，可以取消下面代码的注释进行真实爬取
    data = fetch_and_parse()
    if data:
        with open("sora2_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"保存了 {len(data)} 条数据到 sora2_data.json")