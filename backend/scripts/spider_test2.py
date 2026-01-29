import httpx
from bs4 import BeautifulSoup, Tag
import json
import hashlib
from urllib.parse import unquote, urljoin

# 目标 URL
TARGET_URL = "https://youmind.com/zh-TW/nano-banana-pro-prompts"
BASE_DOMAIN = "https://youmind.com"

def generate_source_id(unique_string):
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def clean_image_url(src):
    """
    处理 /cdn-cgi/image/ 的链接，尝试还原原始高清链接，
    如果还原失败，则返回拼接好的 CDN 链接。
    """
    if not src:
        return None
    
    # 1. 拼接相对路径
    full_cdn_url = urljoin(BASE_DOMAIN, src)
    
    # 2. 尝试从 CDN 链接中提取原始 URL (通常在最后一部分)
    # 格式示例: .../https%3A%2F%2Fcms-assets.youmind.com...
    try:
        if "http" in src:
            # 找到最后一个 http 开头的位置
            part = src.split("http")[-1]
            # 拼回去 'http' 并解码
            real_url = "http" + unquote(part)
            return real_url
    except:
        pass
    
    return full_cdn_url

def fetch_and_parse():
    print(f"1. 正在请求: {TARGET_URL} ...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 启用 http2 通常能过某些反爬，httpx 默认支持
        resp = httpx.get(TARGET_URL, headers=headers, timeout=30, follow_redirects=True)
        print(f"2. 请求状态码: {resp.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    results = []
    
    # === 策略：使用 CSS Selector 定位所有符合特征的 H3 标题 ===
    # class 选择器只要包含关键的几个即可，不需要写全
    titles = soup.select('h3.text-2xl.font-black')
    
    print(f"3. 找到 {len(titles)} 个潜在的标题，开始解析...")

    for h3 in titles:
        # 1. 获取标题文本
        title_text = h3.get_text(strip=True)
        
        # 2. 寻找共同父级 (Card Container)
        # 我们假设 H3 往上找 2-3 层就能找到包含图片和提示词的容器
        # 这里使用 find_parent 并不指定 class，而是找最近的 div
        card_container = h3.find_parent('div')
        
        # 为了保险，可能需要往上多找一层。
        # 判断依据：如果当前 container 找不到 font-mono 的 div，就再往上一层
        prompt_div = None
        
        # 尝试在当前父级找提示词
        if card_container:
            prompt_div = card_container.find('div', class_=lambda c: c and 'font-mono' in c and 'whitespace-pre-wrap' in c)
        
        # 如果没找到，尝试再往上一层父级找 (容错处理)
        if not prompt_div and card_container:
            parent_container = card_container.find_parent('div')
            if parent_container:
                card_container = parent_container
                prompt_div = card_container.find('div', class_=lambda c: c and 'font-mono' in c and 'whitespace-pre-wrap' in c)

        if not prompt_div:
            # 依然找不到，说明这个 h3 可能不是目标卡片的标题，跳过
            continue

        # 3. 提取提示词内容
        # get_text 会自动把里面的 <span> 拼接起来，非常方便
        prompt_text = prompt_div.get_text(strip=True)

        # 4. 在同一个容器里找图片
        # 图片特征：img 标签，class 包含 object-cover
        img_tag = card_container.find('img', class_=lambda c: c and 'object-cover' in c)
        
        original_image_url = None
        if img_tag:
            raw_src = img_tag.get('src') or img_tag.get('data-nimg')
            original_image_url = clean_image_url(raw_src)

        # 5. 组装数据
        if prompt_text:
            unique_str = original_image_url or title_text
            
            item = {
                "source_id": generate_source_id(unique_str),
                "title": title_text,
                "prompt_zh": prompt_text,
                "original_image_url": original_image_url,
                "media_type": "image", # 默认为图片
                "width": None, "height": None, 
                "r2_key": None, "r2_url": None 
            }
            results.append(item)
            print(f"   -> [成功] 解析: {title_text[:15]}...")

    return results

if __name__ == "__main__":
    data = fetch_and_parse()
    
    if data:
        output_file = "youmind_data_test.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n解析成功！共获取 {len(data)} 条数据。")
        print(f"数据已保存至 {output_file}")
    else:
        print("\n未获取到数据，请检查网络或选择器逻辑。")