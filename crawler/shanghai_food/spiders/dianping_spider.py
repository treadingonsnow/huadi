import os
import re
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

# =========================
# 配置
# =========================
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SEEN_URLS_FILE = 'seen_shop_urls.txt'
TARGET_COUNT = 100
EXISTING_CSV_FILE = '大众点评_上海美食_20260323_153608.csv'

# 并发标签页数量：建议 3~5，太高容易触发风控
MAX_WORKERS = 4

# 首页滚动参数
MAX_SCROLL = 18
SCROLL_PAUSE = 0.8
NO_NEW_LINKS_LIMIT = 3

# 页面等待
PAGE_LOAD_WAIT = 1.2
DETAIL_WAIT = 1.0


# =========================
# 文件处理
# =========================
def create_csv():
    """如果文件已存在就继续追加，不覆盖旧文件"""
    file_exists = os.path.exists(EXISTING_CSV_FILE)

    recorder = Recorder(EXISTING_CSV_FILE)
    recorder.set.show_msg(False)

    if not file_exists:
        recorder.add_data([[
            '餐厅唯一标识',
            '餐厅名称',
            '餐厅地址',
            '营业时间',
            '人均消费',
            '综合评分',
            '菜系类型',
            '所在行政区',
            '所属商圈',
            '纬度',
            '经度',
            '采集时间',
            '创建时间',
            '更新时间'
        ]])
        logger.info(f'新建CSV文件: {EXISTING_CSV_FILE}')
    else:
        logger.info(f'追加写入已有CSV文件: {EXISTING_CSV_FILE}')

    return recorder


def load_seen_urls(file_path=SEEN_URLS_FILE):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def append_seen_urls(urls, file_path=SEEN_URLS_FILE):
    """批量追加，减少IO次数"""
    if not urls:
        return
    with open(file_path, 'a', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')

def deduplicate_csv_by_shop_id(csv_file=EXISTING_CSV_FILE):
    """
    读取整个CSV，按“餐厅唯一标识”去重：
    - 如果某个“餐厅唯一标识”出现两次或多次，只保留最前面那一行
    - 其余重复行删除
    """
    if not os.path.exists(csv_file):
        logger.warning(f'CSV文件不存在，无法去重: {csv_file}')
        return

    try:
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = list(csv.reader(f))

        if not reader:
            logger.warning(f'CSV文件为空，无需去重: {csv_file}')
            return

        header = reader[0]
        rows = reader[1:]

        if '餐厅唯一标识' not in header:
            logger.warning('CSV中未找到“餐厅唯一标识”列，无法去重。')
            return

        shop_id_index = header.index('餐厅唯一标识')

        seen_ids = set()
        dedup_rows = []
        removed_count = 0

        for row in rows:
            # 防止某些脏数据行列数不够
            if len(row) <= shop_id_index:
                dedup_rows.append(row)
                continue

            shop_id = str(row[shop_id_index]).strip()

            # 空ID行不参与去重，直接保留
            if not shop_id:
                dedup_rows.append(row)
                continue

            if shop_id in seen_ids:
                removed_count += 1
                continue

            seen_ids.add(shop_id)
            dedup_rows.append(row)

        # 先写临时文件，再替换原文件，更稳
        fd, temp_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)

        with open(temp_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(dedup_rows)

        shutil.move(temp_path, csv_file)

        logger.info(
            f'CSV去重完成: 原数据 {len(rows)} 行，去重后 {len(dedup_rows)} 行，删除重复 {removed_count} 行'
        )

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


def extract_shop_id(url):
    if not url:
        return ''
    m = re.search(r'/shop/(\d+)', url)
    if m:
        return m.group(1)
    path = urlparse(url).path
    return path.rstrip('/').split('/')[-1] if path else ''


def extract_district(address):
    districts = [
        "黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区",
        "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区",
        "青浦区", "奉贤区", "崇明区"
    ]
    for d in districts:
        if d in address:
            return d
    return ''


def extract_business_area(address, html):
    common_areas = [
        "陆家嘴", "人民广场", "南京东路", "南京西路", "徐家汇", "淮海路", "五角场",
        "中山公园", "静安寺", "新天地", "豫园", "打浦桥", "田子坊", "七宝",
        "虹桥", "莘庄", "川沙", "张江", "世博源", "外滩", "北外滩", "前滩"
    ]
    whole_text = f'{address} {html}'
    for area in common_areas:
        if area in whole_text:
            return area
    return ''


def extract_lat_lng_from_html(html):
    patterns = [
        r'"lat"\s*:\s*"?(?P<lat>\d+\.\d+)"?.*?"lng"\s*:\s*"?(?P<lng>\d+\.\d+)"?',
        r'"latitude"\s*:\s*"?(?P<lat>\d+\.\d+)"?.*?"longitude"\s*:\s*"?(?P<lng>\d+\.\d+)"?',
        r'(?P<lat>\d{2}\.\d+)\s*,\s*(?P<lng>\d{3}\.\d+)'
    ]
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            return m.group('lat'), m.group('lng')
    return '', ''


def find_text_by_selectors(page, selectors):
    for loc in selectors:
        try:
            ele = page.ele(loc, timeout=1.2)
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
def get_page():
    co = ChromiumOptions()
    co.set_browser_path(EDGE_PATH)

    # 可选优化项
    try:
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--no-sandbox')
        co.set_argument('--blink-settings=imagesEnabled=false')  # 禁图片可提速
    except Exception:
        pass

    page = ChromiumPage(addr_or_opts=co)
    return page


# =========================
# 链接采集
# =========================
def collect_shop_links(page, max_scroll=MAX_SCROLL):
    """
    改进点：
    1. 不再死等 25 轮
    2. 连续几轮没有新增链接就提前停止
    3. 只保留 shop 链接
    """
    shop_links = set()
    no_new_rounds = 0

    for i in range(max_scroll):
        logger.info(f'第 {i + 1} 次滚动采集链接')

        time.sleep(SCROLL_PAUSE)

        current_count = len(shop_links)

        try:
            links = page.eles('tag:a')
        except Exception:
            links = []

        for a in links:
            try:
                href = a.attr('href')
                if not href:
                    continue
                if '/shop/' not in href:
                    continue
                full_url = urljoin('https://www.dianping.com', href).split('?')[0]
                if 'dianping.com/shop/' in full_url:
                    shop_links.add(full_url)
            except Exception:
                continue

        new_count = len(shop_links) - current_count
        logger.info(f'当前累计店铺链接数: {len(shop_links)}，本轮新增: {new_count}')

        if new_count == 0:
            no_new_rounds += 1
        else:
            no_new_rounds = 0

        if no_new_rounds >= NO_NEW_LINKS_LIMIT:
            logger.info('连续多轮无新增链接，提前结束滚动')
            break

        try:
            page.scroll.to_bottom()
        except Exception:
            pass

        time.sleep(SCROLL_PAUSE)

    return list(shop_links)


# =========================
# 详情解析
# =========================
def parse_shop_detail(page, url):
    logger.info(f'进入详情页: {url}')
    page.get(url)
    time.sleep(DETAIL_WAIT)

    html = page.html or ''
    restaurant_id = extract_shop_id(url)

    name = find_text_by_selectors(page, [
        'tag:h1',
        '.shop-name',
        'xpath://h1',
    ])
    if not name:
        name = find_html_by_patterns(html, [
            r'<h1[^>]*>(.*?)</h1>',
            r'"shopName"\s*:\s*"(.*?)"',
            r'"name"\s*:\s*"(.*?)"',
        ])

    name = clean_text(name)

    # 统一拦截 Forbidden
    if name in ('Forbidden', '403 Forbidden'):
        logger.warning(f'店铺 {url} 名称为 {name}，跳过！')
        return None

    address = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"地址")]',
        '.address',
        '.shop-address',
        'xpath://*[contains(@class,"address")]',
    ])
    if not address:
        address = find_html_by_patterns(html, [
            r'地址[:：]?\s*([^<\n\r]+)',
            r'"address"\s*:\s*"(.*?)"',
        ])

    business_hours = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"营业时间")]',
        '.business-hours',
        '.hours',
    ])
    if not business_hours:
        business_hours = find_html_by_patterns(html, [
            r'营业时间[:：]?\s*([^<\n\r]+)',
            r'"openTime"\s*:\s*"(.*?)"',
            r'"businessHours"\s*:\s*"(.*?)"',
        ])

    avg_price = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"人均")]',
        '.price',
        '.average',
    ])
    if not avg_price:
        avg_price = find_html_by_patterns(html, [
            r'人均[:：]?\s*[¥￥]?(\d+)',
            r'"avgPrice"\s*:\s*"?(.*?)"?(,|})',
        ])
    avg_price = extract_first_number(avg_price)

    score = find_text_by_selectors(page, [
        '.score',
        'xpath://*[contains(text(),"评分")]',
        '.star-score',
    ])
    if not score:
        score = find_html_by_patterns(html, [
            r'"score"\s*:\s*"?(.*?)"?(,|})',
            r'(\d\.\d)',
        ])
    score = extract_first_number(score)

    cuisine = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"分类")]',
        '.category',
        '.breadcrumb',
        '.shop-tag',
    ])
    if not cuisine:
        cuisine = find_html_by_patterns(html, [
            r'分类[:：]?\s*([^<\n\r]+)',
            r'"categoryName"\s*:\s*"(.*?)"',
            r'"category"\s*:\s*"(.*?)"',
        ])

    district = extract_district(address)
    business_area = extract_business_area(address, html)
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
        '更新时间': now_time
    }

    if not data.get('餐厅名称') and not data.get('餐厅地址'):
        return None

    return data


def parse_shop_detail_with_new_tab(browser, url):
    """
    每个线程自己开一个标签页，避免多个线程抢同一个page对象
    """
    tab = None
    try:
        tab = browser.new_tab()
        data = parse_shop_detail(tab, url)
        return url, data
    except Exception as e:
        logger.error(f'采集失败: {url} | 错误: {e}')
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
    browser = get_page()

    logger.info('打开大众点评上海美食页')
    browser.get(start_url)
    time.sleep(PAGE_LOAD_WAIT)

    logger.info(f'当前页面标题: {browser.title}')
    logger.info(f'当前页面URL: {browser.url}')

    shop_links = collect_shop_links(browser, max_scroll=MAX_SCROLL)
    logger.info(f'最终采集到店铺链接数: {len(shop_links)}')

    if not shop_links:
        logger.warning('没有采集到任何店铺链接，请检查页面结构或是否被限制访问。')
        return

    seen_urls = load_seen_urls()
    logger.info(f'历史已抓取链接数: {len(seen_urls)}')

    # 先去重，再打乱
    candidate_links = [link for link in shop_links if link not in seen_urls]
    random.shuffle(candidate_links)

    if not candidate_links:
        logger.warning('没有可采集的新店铺链接。')
        return

    success_count = 0
    batch_rows = []
    batch_seen = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        submitted = 0

        # 先提交一批任务
        while submitted < min(len(candidate_links), TARGET_COUNT * 2, MAX_WORKERS * 3):
            url = candidate_links[submitted]
            future = executor.submit(parse_shop_detail_with_new_tab, browser, url)
            future_map[future] = url
            submitted += 1

        while future_map and success_count < TARGET_COUNT:
            for future in as_completed(list(future_map.keys())):
                url = future_map.pop(future)

                try:
                    _, data = future.result()
                except Exception as e:
                    logger.error(f'任务执行异常: {url} | {e}')
                    data = None

                if data:
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
                        data.get('更新时间', '')
                    ])
                    batch_seen.append(url)
                    success_count += 1
                    logger.info(f'成功采集第 {success_count} 家: {url}')

                    # 每5条批量写一次
                    if len(batch_rows) >= 5:
                        recorder.add_data(batch_rows)

                        # 每次写入CSV后，立即按“餐厅唯一标识”去重
                        deduplicate_csv_by_shop_id(EXISTING_CSV_FILE)

                        append_seen_urls(batch_seen)
                        seen_urls.update(batch_seen)
                        batch_rows.clear()
                        batch_seen.clear()

                # 继续补充新任务
                if submitted < len(candidate_links) and success_count < TARGET_COUNT:
                    new_url = candidate_links[submitted]
                    future_new = executor.submit(parse_shop_detail_with_new_tab, browser, new_url)
                    future_map[future_new] = new_url
                    submitted += 1

                if success_count >= TARGET_COUNT:
                    break

    # 收尾写入
    if batch_rows:
        recorder.add_data(batch_rows)
        deduplicate_csv_by_shop_id(EXISTING_CSV_FILE)
        append_seen_urls(batch_seen)

    logger.info(f'采集结束，本次成功采集 {success_count} 家餐饮店铺')
    logger.info(f'数据已写入文件: {EXISTING_CSV_FILE}')


if __name__ == '__main__':
    main()