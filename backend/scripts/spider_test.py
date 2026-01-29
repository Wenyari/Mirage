import httpx
from bs4 import BeautifulSoup, Tag
import json
import hashlib

TARGET_URL = "https://github.com/PicoTrex/Awesome-Nano-Banana-images"
BASE_DOMAIN = "https://github.com"

def generate_source_id(unique_string):
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def fetch_and_parse():
    print(f"1. 正在请求: {TARGET_URL} ...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = httpx.get(TARGET_URL, headers=headers, timeout=30)
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    article = soup.find('article', class_='markdown-body')
    
    if not article:
        print("!! 未找到 markdown-body")
        return []

    results = []
    headers_list = article.find_all('h3')
    print(f"3. 找到 {len(headers_list)} 个 H3 标题，开始解析...")

    for index, h3 in enumerate(headers_list):
        title_text = h3.get_text(strip=True)
        
        # === 核心修复 1: 确定查找的起点 ===
        # 如果 h3 被包裹在 div.markdown-heading 里，我们要用这个 div 作为起点
        start_node = h3
        if h3.parent and h3.parent.name == 'div' and 'markdown-heading' in h3.parent.get('class', []):
            start_node = h3.parent
        
        # 调试模式
        debug_mode = (index == 0)
        if debug_mode: print(f"\n--- [DEBUG] 分析组: {title_text} (起点: <{start_node.name}>) ---")

        current_data = {
            "source_id": None,
            "title": title_text,
            "prompt_zh": None,
            "original_image_url": None,
            "media_type": "image",
            "width": None, "height": None, "r2_key": None, "r2_url": None, "cover_r2_key": None, "cover_r2_url": None
        }

        # === 核心修复 2: 遍历起点的兄弟节点 ===
        siblings = start_node.find_next_siblings()
        
        for sibling in siblings:
            if not isinstance(sibling, Tag): continue

            # === 核心修复 3: 停止条件升级 ===
            # 如果遇到下一个 h3 (旧结构) 或者下一个 markdown-heading (新结构)，就停止
            is_next_header = (sibling.name == 'h3')
            is_next_header_div = (sibling.name == 'div' and 'markdown-heading' in sibling.get('class', []))
            
            if is_next_header or is_next_header_div:
                if debug_mode: print(f"   [停止] 遇到下一个标题节点: <{sibling.name}>")
                break

            if debug_mode: print(f"   检查: <{sibling.name}>")

            # --- A. 查找图片 ---
            if not current_data['original_image_url']:
                # 针对 markdown-accessiblity-table 这种特殊标签，递归查 img
                img = sibling.find('img')
                if img:
                    src = img.get('src') or img.get('data-canonical-src')
                    if src:
                        if src.startswith('/'): src = BASE_DOMAIN + src
                        src = src.replace('/blob/', '/raw/')
                        current_data['original_image_url'] = src
                        if debug_mode: print(f"   -> 找到图片: {src}")

            # --- B. 查找提示词 ---
            if not current_data['prompt_zh']:
                # 你的目标页面中，提示词在 <pre><code> 里
                # 这里的 sibling 可能是 div.snippet-clipboard-content，也可能是其他
                pre = sibling.find('pre')
                if pre:
                    text = pre.get_text(strip=True)
                    current_data['prompt_zh'] = text
                    if debug_mode: print(f"   -> 找到提示词: {text[:20]}...")

            if current_data['original_image_url'] and current_data['prompt_zh']:
                break
        
        if current_data['original_image_url']:
            unique_str = current_data['original_image_url']
            current_data['source_id'] = generate_source_id(unique_str)
            results.append(current_data)

    return results

if __name__ == "__main__":
    data = fetch_and_parse()
    if data:
        with open("github_data_test.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n解析成功！获取 {len(data)} 条数据。")
    else:
        print("\n依然没有数据，请检查 HTML 结构。")