import os
import re
import sys
import csv
import time
import random
import shutil
import tempfile
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from DrissionPage import ChromiumPage, ChromiumOptions
from DataRecorder import Recorder
from loguru import logger

# 引入 fix_district 中的完整行政区匹配逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_district import ROAD_DISTRICT_MAP, match_district

# =========================
# 配置
# =========================

def _detect_browser_path():
    """自动检测可用浏览器路径，优先 Chrome，其次 Chromium，最后 Edge"""
    candidates = [
        # Linux
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/snap/bin/chromium',
        # macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        # Windows
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None  # 让 DrissionPage 自动查找

BROWSER_PATH = _detect_browser_path()

# 输出文件路径固定在脚本所在目录，避免从其他目录运行时找不到文件
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(_SCRIPT_DIR, 'dianping_shanghai.csv')
SEEN_URLS_FILE = os.path.join(_SCRIPT_DIR, 'seen_shop_urls.txt')

# 目标采集数量（与项目目标对齐）
TARGET_COUNT = 1000

# 并发标签页数量：降为2，减少风控触发
MAX_WORKERS = 2

# 详情页请求间随机延迟范围（秒）
DETAIL_DELAY_MIN = 2.0
DETAIL_DELAY_MAX = 4.0

# 遭遇403/空页时的退避等待（秒）
BLOCK_BACKOFF = 8.0

# 连续失败超过此数量则暂停一段时间
CONSECUTIVE_FAIL_LIMIT = 3
CONSECUTIVE_FAIL_PAUSE = 15.0

# 列表页翻页上限
MAX_PAGES = 50

# 首页滚动参数
MAX_SCROLL = 18
SCROLL_PAUSE = 0.8
NO_NEW_LINKS_LIMIT = 3

# 页面等待
PAGE_LOAD_WAIT = 1.5
DETAIL_WAIT = 1.2

# 选择器超时（单个，降低叠加耗时）
SELECTOR_TIMEOUT = 0.8

# 批量写入阈值（去重只在程序结束时做一次）
BATCH_WRITE_SIZE = 10


# =========================
# 文件处理
# =========================
def create_csv():
    """如果文件已存在就继续追加，不覆盖旧文件"""
    file_exists = os.path.exists(CSV_FILE)
    recorder = Recorder(CSV_FILE)
    recorder.set.show_msg(False)
    if not file_exists:
        recorder.add_data([[
            '餐厅唯一标识', '餐厅名称', '餐厅地址', '营业时间',
            '人均消费', '综合评分', '菜系类型', '所在行政区',
            '所属商圈', '纬度', '经度', '采集时间', '创建时间', '更新时间'
        ]])
        logger.info(f'新建CSV文件: {CSV_FILE}')
    else:
        logger.info(f'追加写入已有CSV文件: {CSV_FILE}')
    return recorder


def load_seen_urls(file_path=SEEN_URLS_FILE):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def append_seen_urls(urls, file_path=SEEN_URLS_FILE):
    if not urls:
        return
    with open(file_path, 'a', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')


def deduplicate_csv_by_shop_id(csv_file=CSV_FILE):
    """程序结束时做一次全量去重，避免频繁 IO"""
    if not os.path.exists(csv_file):
        return
    try:
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = list(csv.reader(f))
        if not reader:
            return
        header = reader[0]
        rows = reader[1:]
        if '餐厅唯一标识' not in header:
            return
        idx = header.index('餐厅唯一标识')
        seen_ids, dedup_rows, removed = set(), [], 0
        for row in rows:
            if len(row) <= idx:
                dedup_rows.append(row)
                continue
            shop_id = str(row[idx]).strip()
            if not shop_id:
                dedup_rows.append(row)
                continue
            if shop_id in seen_ids:
                removed += 1
                continue
            seen_ids.add(shop_id)
            dedup_rows.append(row)
        fd, temp_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        with open(temp_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(dedup_rows)
        shutil.move(temp_path, csv_file)
        logger.info(f'CSV去重完成: {len(rows)} → {len(dedup_rows)} 行，删除重复 {removed} 行')
    except Exception as e:
        logger.error(f'CSV去重失败: {e}')


# =========================
# 工具函数
# =========================
def clean_text(text):
    if not text:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def extract_first_number(text):
    if not text:
        return ''
    m = re.search(r'(\d+(\.\d+)?)', str(text))
    return m.group(1) if m else ''


def normalize_shop_url(url):
    """
    规范化店铺 URL，去除 #fragment、/dishXXX、/photoXXX 等子路径，
    保证同一家店只有一个唯一 URL。
    例：
      .../shop/Abc123#comment       → .../shop/Abc123
      .../shop/Abc123/dish12345     → .../shop/Abc123
      .../shop/Abc123?from=xxx      → .../shop/Abc123
    """
    # 先去掉 query 和 fragment
    url = url.split('?')[0].split('#')[0]
    # 去掉 /shop/<id> 后面多余的子路径（如 /dish123、/photo456）
    m = re.match(r'(https?://[^/]+/shop/[^/]+)', url)
    return m.group(1) if m else url


def extract_shop_id(url):
    if not url:
        return ''
    # 先规范化再提取，支持字母数字混合 ID（大众点评新版 ID 格式）
    clean = normalize_shop_url(url)
    m = re.search(r'/shop/([A-Za-z0-9]+)$', clean)
    if m:
        return m.group(1)
    path = urlparse(clean).path
    return path.rstrip('/').split('/')[-1] if path else ''
    """从 area_dict 中提取商圈，长关键词优先"""
    whole_text = f'{address} {html[:2000]}'  # html 只取前2000字符，避免过慢
    sorted_keys = sorted(ROAD_DISTRICT_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keys:
        if keyword in whole_text:
            return keyword
    return ''


def extract_lat_lng_from_html(html):
    patterns = [
        r'"lat"\s*:\s*"?(?P<lat>3[0-2]\.\d+)"?.*?"lng"\s*:\s*"?(?P<lng>12[0-9]\.\d+)"?',
        r'"latitude"\s*:\s*"?(?P<lat>3[0-2]\.\d+)"?.*?"longitude"\s*:\s*"?(?P<lng>12[0-9]\.\d+)"?',
        r'(?P<lat>3[0-2]\.\d{4,})\s*,\s*(?P<lng>12[0-9]\.\d{4,})',
    ]
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            return m.group('lat'), m.group('lng')
    return '', ''


def find_text_by_selectors(page, selectors):
    """降低单个选择器超时，减少叠加等待"""
    for loc in selectors:
        try:
            ele = page.ele(loc, timeout=SELECTOR_TIMEOUT)
            if ele:
                text = clean_text(ele.text)
                if text:
                    return text
        except Exception:
            continue
    return ''


def find_html_by_patterns(html, patterns):
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            text = clean_text(m.group(1))
            if text:
                return text
    return ''


# =========================
# 浏览器
# =========================
def get_browser():
    co = ChromiumOptions()
    if BROWSER_PATH:
        co.set_browser_path(BROWSER_PATH)
        logger.info(f'使用浏览器: {BROWSER_PATH}')
    else:
        logger.info('未找到浏览器路径，由 DrissionPage 自动检测')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--no-sandbox')
    co.set_argument('--blink-settings=imagesEnabled=false')
    return ChromiumPage(addr_or_opts=co)


# =========================
# 链接采集（含翻页）
# =========================
def _collect_links_on_page(page, shop_links):
    """采集当前页面所有 shop 链接，返回本次新增数量"""
    before = len(shop_links)
    try:
        links = page.eles('tag:a')
    except Exception:
        return 0
    for a in links:
        try:
            href = a.attr('href')
            if not href or '/shop/' not in href:
                continue
            full_url = urljoin('https://www.dianping.com', href)
            full_url = normalize_shop_url(full_url)
            if 'dianping.com/shop/' in full_url:
                shop_links.add(full_url)
        except Exception:
            continue
    return len(shop_links) - before


def collect_shop_links(page, target_count=TARGET_COUNT, max_pages=MAX_PAGES):
    """
    先在当前页滚动采集，再翻页继续，直到链接数满足需求或到达翻页上限。
    大众点评列表页翻页 URL 规律：在 URL 末尾加 /pN（N 从 2 开始）
    """
    shop_links = set()
    base_url = page.url.split('?')[0].rstrip('/')

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            current_url = base_url
        else:
            current_url = f'{base_url}/p{page_num}'

        if page_num > 1:
            logger.info(f'翻页到第 {page_num} 页: {current_url}')
            page.get(current_url)
            time.sleep(PAGE_LOAD_WAIT)

        # 在当前页滚动采集
        no_new_rounds = 0
        for i in range(MAX_SCROLL):
            new_count = _collect_links_on_page(page, shop_links)
            logger.info(f'第{page_num}页 第{i+1}次滚动，累计链接: {len(shop_links)}，本轮新增: {new_count}')
            if new_count == 0:
                no_new_rounds += 1
            else:
                no_new_rounds = 0
            if no_new_rounds >= NO_NEW_LINKS_LIMIT:
                break
            try:
                page.scroll.to_bottom()
            except Exception:
                pass
            time.sleep(SCROLL_PAUSE)

        logger.info(f'第 {page_num} 页采集完毕，当前累计: {len(shop_links)} 条链接')

        if len(shop_links) >= target_count * 2:
            logger.info('链接数已充足，停止翻页')
            break

        # 检测是否还有下一页（找不到下一页按钮则停止）
        try:
            next_btn = page.ele('xpath://*[contains(@class,"next") or contains(text(),"下一页")]', timeout=1.0)
            if not next_btn:
                logger.info('未找到下一页按钮，停止翻页')
                break
        except Exception:
            logger.info('翻页检测异常，停止翻页')
            break

    return list(shop_links)


# =========================
# 详情解析
# =========================
def parse_shop_detail(page, url):
    # 规范化 URL，确保访问干净地址
    url = normalize_shop_url(url)
    logger.info(f'进入详情页: {url}')
    page.get(url)
    # 随机延迟，模拟人工浏览节奏
    time.sleep(random.uniform(DETAIL_DELAY_MIN, DETAIL_DELAY_MAX))

    html = page.html or ''

    # 检测是否被拦截（403 / 验证码页）
    if len(html) < 500 or '403 Forbidden' in html or 'forbidden' in html.lower():
        logger.warning(f'疑似被拦截: {url}，退避 {BLOCK_BACKOFF}s')
        time.sleep(BLOCK_BACKOFF)
        return None
    restaurant_id = extract_shop_id(url)

    name = find_text_by_selectors(page, ['tag:h1', '.shop-name'])
    if not name:
        name = find_html_by_patterns(html, [
            r'<h1[^>]*>(.*?)</h1>',
            r'"shopName"\s*:\s*"(.*?)"',
            r'"name"\s*:\s*"(.*?)"',
        ])
    name = clean_text(name)

    if name in ('Forbidden', '403 Forbidden', ''):
        logger.warning(f'店铺 {url} 被拦截或名称为空，跳过')
        return None

    address = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"地址")]',
        '.address', '.shop-address',
    ])
    if not address:
        address = find_html_by_patterns(html, [
            r'地址[:：]?\s*([^<\n\r]+)',
            r'"address"\s*:\s*"(.*?)"',
        ])

    business_hours = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"营业时间")]',
        '.business-hours', '.hours',
    ])
    if not business_hours:
        business_hours = find_html_by_patterns(html, [
            r'营业时间[:：]?\s*([^<\n\r]+)',
            r'"openTime"\s*:\s*"(.*?)"',
            r'"businessHours"\s*:\s*"(.*?)"',
        ])

    avg_price = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"人均")]',
        '.price', '.average',
    ])
    if not avg_price:
        avg_price = find_html_by_patterns(html, [
            r'人均[:：]?\s*[¥￥]?(\d+)',
            r'"avgPrice"\s*:\s*"?(.*?)"?(,|})',
        ])
    avg_price = extract_first_number(avg_price)

    score = find_text_by_selectors(page, ['.score', '.star-score'])
    if not score:
        score = find_html_by_patterns(html, [
            r'"score"\s*:\s*"?([0-9.]+)"?(,|})',
            r'([4-5]\.\d)',
        ])
    score = extract_first_number(score)

    cuisine = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"分类")]',
        '.category', '.breadcrumb', '.shop-tag',
    ])
    if not cuisine:
        cuisine = find_html_by_patterns(html, [
            r'分类[:：]?\s*([^<\n\r]+)',
            r'"categoryName"\s*:\s*"(.*?)"',
            r'"category"\s*:\s*"(.*?)"',
        ])

    # 使用 fix_district 中更完整的匹配逻辑
    business_area = extract_business_area(address, html)
    district = match_district(address, business_area)

    latitude, longitude = extract_lat_lng_from_html(html)
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {
        '餐厅唯一标识': restaurant_id,
        '餐厅名称': name,
        '餐厅地址': address,
        '营业时间': business_hours,
        '人均消费': avg_price,
        '综合评分': score,
        '菜系类型': cuisine,
        '所在行政区': district,
        '所属商圈': business_area,
        '纬度': latitude,
        '经度': longitude,
        '采集时间': now_time,
        '创建时间': now_time,
        '更新时间': now_time,
    }

    if not data['餐厅名称'] and not data['餐厅地址']:
        return None

    return data


def parse_shop_detail_with_new_tab(browser, url):
    """每个线程开独立标签页，避免竞争"""
    tab = None
    try:
        tab = browser.new_tab()
        data = parse_shop_detail(tab, url)
        return url, data
    except Exception as e:
        logger.error(f'采集失败: {url} | {e}')
        return url, None
    finally:
        try:
            if tab:
                tab.close()
        except Exception:
            pass


# =========================
# 主流程
# =========================
def main():
    start_url = 'https://www.dianping.com/shanghai/ch10/g110'

    recorder = create_csv()
    browser = get_browser()

    logger.info('打开大众点评上海美食页')
    browser.get(start_url)
    time.sleep(PAGE_LOAD_WAIT)
    logger.info(f'当前页面标题: {browser.title}')

    shop_links = collect_shop_links(browser, target_count=TARGET_COUNT)
    logger.info(f'最终采集到店铺链接数: {len(shop_links)}')

    if not shop_links:
        logger.warning('没有采集到任何店铺链接，请检查页面结构或是否被限制访问。')
        return

    seen_urls = load_seen_urls()
    logger.info(f'历史已抓取链接数: {len(seen_urls)}')

    candidate_links = [link for link in shop_links if link not in seen_urls]
    random.shuffle(candidate_links)

    if not candidate_links:
        logger.warning('没有可采集的新店铺链接。')
        return

    success_count = 0
    consecutive_fails = 0
    batch_rows = []
    batch_seen = []

    # 修复 as_completed 重复迭代 bug：只创建一次迭代器
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 初始提交一批任务
        init_submit = min(len(candidate_links), TARGET_COUNT, MAX_WORKERS * 3)
        futures = {
            executor.submit(parse_shop_detail_with_new_tab, browser, candidate_links[i]): candidate_links[i]
            for i in range(init_submit)
        }
        submitted = init_submit

        for future in as_completed(futures):
            if success_count >= TARGET_COUNT:
                break

            url = futures.pop(future)
            try:
                _, data = future.result()
            except Exception as e:
                logger.error(f'任务执行异常: {url} | {e}')
                data = None

            if data:
                consecutive_fails = 0
                batch_rows.append([
                    data.get('餐厅唯一标识', ''),
                    data.get('餐厅名称', ''),
                    data.get('餐厅地址', ''),
                    data.get('营业时间', ''),
                    data.get('人均消费', ''),
                    data.get('综合评分', ''),
                    data.get('菜系类型', ''),
                    data.get('所在行政区', ''),
                    data.get('所属商圈', ''),
                    data.get('纬度', ''),
                    data.get('经度', ''),
                    data.get('采集时间', ''),
                    data.get('创建时间', ''),
                    data.get('更新时间', ''),
                ])
                batch_seen.append(url)
                success_count += 1
                logger.info(f'成功采集第 {success_count} 家: {data.get("餐厅名称", "")} | {url}')

                if len(batch_rows) >= BATCH_WRITE_SIZE:
                    recorder.add_data(batch_rows)
                    append_seen_urls(batch_seen)
                    seen_urls.update(batch_seen)
                    batch_rows.clear()
                    batch_seen.clear()

            else:
                consecutive_fails += 1
                if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT:
                    logger.warning(f'连续失败 {consecutive_fails} 次，暂停 {CONSECUTIVE_FAIL_PAUSE}s 后继续')
                    time.sleep(CONSECUTIVE_FAIL_PAUSE)
                    consecutive_fails = 0

            # 补充新任务保持并发饱和
            if submitted < len(candidate_links) and success_count < TARGET_COUNT:
                new_url = candidate_links[submitted]
                new_future = executor.submit(parse_shop_detail_with_new_tab, browser, new_url)
                futures[new_future] = new_url
                submitted += 1

    # 收尾写入
    if batch_rows:
        recorder.add_data(batch_rows)
        append_seen_urls(batch_seen)

    # 程序结束时做一次全量去重
    deduplicate_csv_by_shop_id(CSV_FILE)

    logger.info(f'采集结束，本次成功采集 {success_count} 家餐饮店铺')
    logger.info(f'数据已写入文件: {CSV_FILE}')


if __name__ == '__main__':
    main()
