import os
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse

from DrissionPage import ChromiumPage, ChromiumOptions
from DataRecorder import Recorder
from loguru import logger


EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SEEN_URLS_FILE = 'seen_shop_urls.txt'
TARGET_COUNT = 20

# 目标菜系：除了火锅外的其他菜系都爬
TARGET_CUISINES = [
    '海鲜',
    '烧烤',
    '烧烤海鲜',
    '海鲜自助',
    '江浙菜',
    '川菜',
    '湘菜',
    '粤菜',
    '东北菜',
    '快餐',
    '自助餐',
    '西餐',
    '日韩料理'
]

# 创建/追加CSV文件
def create_csv(keyword: str):
    """如果文件已存在就继续追加，不覆盖旧文件"""
    filename = f'{keyword.strip() or "data"}.csv'
    file_exists = os.path.exists(filename)

    recorder = Recorder(filename)
    recorder.set.show_msg(False)

    if not file_exists:
        recorder.add_data([[
            '餐厅唯一标识',
            '餐厅名称',
            '餐厅地址',
            '联系电话',
            '营业时间',
            '人均消费',
            '综合评分',
            '评论总数',
            '菜系类型',
            '所在行政区',
            '所属商圈',
            '纬度',
            '经度',
            '最近地铁距离（米）',
            '数据来源',
            '采集时间',
            '创建时间',
            '更新时间'
        ]])
        logger.info(f'新建CSV文件: {filename}')
    else:
        logger.info(f'追加写入已有CSV文件: {filename}')

    return recorder, filename


# 加载历史已抓取店铺链接
def load_seen_urls(file_path=SEEN_URLS_FILE):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


# 追加保存已抓取的店铺链接
def append_seen_url(url, file_path=SEEN_URLS_FILE):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(url + '\n')


# 清理空白字符
def clean_text(text):
    if not text:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


# 提取第一个数字
def extract_first_number(text):
    if not text:
        return ''
    m = re.search(r'(\d+(\.\d+)?)', str(text))
    return m.group(1) if m else ''


# 提取电话
def extract_phone(text):
    if not text:
        return ''
    patterns = [
        r'(\d{3}\*{4}\d{4})',
        r'(\d{3,4}-\d{7,8})',
        r'(\d{11})',
        r'(\d{3,4}\s?\d{4}\s?\d{4})',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return clean_text(m.group(1))
    return ''


# 启动浏览器
def get_page():
    co = ChromiumOptions()
    co.set_browser_path(EDGE_PATH)
    page = ChromiumPage(addr_or_opts=co)
    return page


# 收集店铺链接
def collect_shop_links(page, max_scroll=12):
    shop_links = set()

    for i in range(max_scroll):
        logger.info(f'第 {i + 1} 次滚动采集链接')
        time.sleep(2)

        links = page.eles('tag:a')
        for a in links:
            try:
                href = a.attr('href')
                if not href:
                    continue
                if '/shop/' in href:
                    full_url = urljoin('https://www.dianping.com', href)
                    if 'dianping.com/shop/' in full_url:
                        shop_links.add(full_url.split('?')[0])
            except Exception:
                continue

        logger.info(f'当前累计店铺链接数: {len(shop_links)}')

        try:
            page.scroll.to_bottom()
        except Exception:
            pass

        time.sleep(2)

    return list(shop_links)


# 提取店铺ID
def extract_shop_id(url):
    if not url:
        return ''
    m = re.search(r'/shop/(\d+)', url)
    if m:
        return m.group(1)
    path = urlparse(url).path
    return path.rstrip('/').split('/')[-1] if path else ''


# 根据多个选择器提取文本
def find_text_by_selectors(page, selectors):
    for loc in selectors:
        try:
            ele = page.ele(loc, timeout=2)
            if ele:
                text = clean_text(ele.text)
                if text:
                    return text
        except Exception:
            continue
    return ''


# 根据多个正则表达式提取HTML中的文本
def find_html_by_patterns(html, patterns):
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            text = clean_text(m.group(1))
            if text:
                return text
    return ''


# 提取行政区
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


# 提取商圈
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


# 提取经纬度
def extract_lat_lng_from_html(html):
    patterns = [
        r'"lat"\s*:\s*"?(?P<lat>\d+\.\d+)"?.*?"lng"\s*:\s*"?(?P<lng>\d+\.\d+)"?',
        r'"latitude"\s*:\s*"?(?P<lat>\d+\.\d+)"?.*?"longitude"\s*:\s*"?(?P<lng>\d+\.\d+)"?',
        r'(?P<lat>\d{2}\.\d+)\s*,\s*(?P<lng>\d{3}\.\d+)',
    ]
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            return m.group('lat'), m.group('lng')
    return '', ''


# 提取地铁距离
def extract_subway_distance(html):
    patterns = [
        r'地铁.*?(\d+)\s*米',
        r'(\d+)\s*米.*?地铁',
        r'距离地铁.*?(\d+)\s*米',
    ]
    for p in patterns:
        m = re.search(p, html, re.S)
        if m:
            return m.group(1)
    return ''


# 解析店铺详情页
def parse_shop_detail(page, url):
    logger.info(f'进入详情页: {url}')
    page.get(url)
    time.sleep(3)

    html = page.html or ''
    page_text = clean_text(html)

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

    phone = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"电话")]',
        '.phone',
        '.tel',
    ])
    if not phone:
        phone = find_html_by_patterns(html, [
            r'电话[:：]?\s*([^<\n\r]+)',
            r'"phoneNo"\s*:\s*"(.*?)"',
            r'"phone"\s*:\s*"(.*?)"',
        ])
    phone = extract_phone(phone) or extract_phone(page_text)

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

    review_count = find_text_by_selectors(page, [
        'xpath://*[contains(text(),"评论")]',
        '.review-count',
        '.comment',
    ])
    if not review_count:
        review_count = find_html_by_patterns(html, [
            r'评论[（(]?(\d+)[）)]?',
            r'"reviewCount"\s*:\s*"?(.*?)"?(,|})',
            r'"commentCount"\s*:\s*"?(.*?)"?(,|})',
        ])
    review_count = extract_first_number(review_count)

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
    nearest_subway_distance = extract_subway_distance(html)

    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {
        '餐厅唯一标识': restaurant_id,
        '餐厅名称': name,
        '餐厅地址': address,
        '联系电话': phone,
        '营业时间': business_hours,
        '人均消费': avg_price,
        '综合评分': score,
        '评论总数': review_count,
        '菜系类型': cuisine,
        '所在行政区': district,
        '所属商圈': business_area,
        '纬度': latitude,
        '经度': longitude,
        '最近地铁距离（米）': nearest_subway_distance,
        '数据来源': 'dianping',
        '采集时间': now_time,
        '创建时间': now_time,
        '更新时间': now_time
    }
    return data


# 只保留海鲜、烧烤等目标菜系
def is_target_cuisine(data):
    target_text = ' '.join([
        str(data.get('餐厅名称', '') or ''),
        str(data.get('菜系类型', '') or ''),
        str(data.get('餐厅地址', '') or '')
    ])
    return any(keyword in target_text for keyword in TARGET_CUISINES)


def main():
    keyword = '大众点评_上海海鲜烧烤'
    start_url = 'https://www.dianping.com/shanghai/ch10/g110'

    recorder, filename = create_csv(keyword)
    page = get_page()

    logger.info('打开大众点评上海美食页')
    page.get(start_url)
    time.sleep(5)

    logger.info(f'当前页面标题: {page.title}')
    logger.info(f'当前页面URL: {page.url}')

    shop_links = collect_shop_links(page, max_scroll=12)
    logger.info(f'最终采集到店铺链接数: {len(shop_links)}')

    if not shop_links:
        logger.warning('没有采集到任何店铺链接，请检查页面结构或是否被限制访问。')
        return

    seen_urls = load_seen_urls()
    logger.info(f'历史已抓取链接数: {len(seen_urls)}')

    random.shuffle(shop_links)

    success_count = 0

    for link in shop_links:
        if success_count >= TARGET_COUNT:
            break

        if link in seen_urls:
            continue

        try:
            logger.info(f'开始采集第 {success_count + 1} 家店铺: {link}')
            data = parse_shop_detail(page, link)

            # 跳过403页面，重新爬取
            if '403 Forbidden' in data.get('餐厅名称', ''):
                logger.warning(f'店铺 {link} 显示 403 Forbidden，跳过！')
                continue

            if not data.get('餐厅名称') and not data.get('餐厅地址'):
                logger.warning(f'跳过空数据店铺: {link}')
                continue

            if not is_target_cuisine(data):
                logger.info(f'跳过非目标菜系店铺: {data.get("餐厅名称", "")} | 菜系: {data.get("菜系类型", "")}')
                continue

            recorder.add_data([[
                data.get('餐厅唯一标识', ''),
                data.get('餐厅名称', ''),
                data.get('餐厅地址', ''),
                data.get('联系电话', ''),
                data.get('营业时间', ''),
                data.get('人均消费', ''),
                data.get('综合评分', ''),
                data.get('评论总数', ''),
                data.get('菜系类型', ''),
                data.get('所在行政区', ''),
                data.get('所属商圈', ''),
                data.get('纬度', ''),
                data.get('经度', ''),
                data.get('最近地铁距离（米）', ''),
                data.get('数据来源', ''),
                data.get('采集时间', ''),
                data.get('创建时间', ''),
                data.get('更新时间', '')
            ]])

            append_seen_url(link)
            seen_urls.add(link)
            success_count += 1
            time.sleep(2)

        except Exception as e:
            logger.error(f'采集失败: {link} | 错误: {e}')
            continue

    logger.info(f'采集结束，本次成功采集 {success_count} 家海鲜烧烤店铺')
    logger.info(f'数据已写入文件: {filename}')


if __name__ == '__main__':
    main()