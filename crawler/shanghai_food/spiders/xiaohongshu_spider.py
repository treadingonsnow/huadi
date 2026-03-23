import os
import time
from loguru import logger
from DrissionPage import ChromiumPage
from DataRecorder import Recorder


def create_csv(keyword):
    """创建/复用CSV记录器（追加模式，保留历史数据）"""
    filename = f'{keyword.strip()}.csv'
    # 核心修改1：删除清空旧文件的逻辑，不再删除历史文件
    # 移除原有的 os.remove 相关代码

    # 判断文件是否存在，不存在则新建，存在则直接复用
    if not os.path.exists(filename):
        logger.info(f'创建新CSV文件: {filename}')
        recorder = Recorder(filename)
        recorder.set.show_msg(False)
    else:
        logger.info(f'复用已有CSV文件: {filename}，新数据将追加到文件末尾')
        recorder = Recorder(filename)
        recorder.set.show_msg(False)
    return recorder


def add_utf8_bom(filename):
    """给csv文件添加BOM，解决Excel乱码（兼容追加模式）"""
    if not os.path.exists(filename):
        logger.warning(f'文件 {filename} 不存在，跳过BOM添加')
        return

    with open(filename, 'r+b') as f:
        content = f.read()
        # 核心修改2：判断是否已有BOM，避免重复添加导致乱码
        if content.startswith(b'\xef\xbb\xbf'):
            logger.info(f'文件 {filename} 已包含BOM，无需重复添加')
            return
        f.seek(0)
        f.write(b'\xef\xbb\xbf' + content)
        f.truncate()  # 截断多余内容


def find_want(data, target_key):
    """递归查找目标字段值"""
    if isinstance(data, dict):
        for key, val in data.items():
            if key == target_key:
                return val
            ret = find_want(val, target_key)
            if ret:
                return ret
    elif isinstance(data, list):
        for item in data:
            ret = find_want(item, target_key)
            if ret:
                return ret
    else:
        return None


def extract_poi_info(data):
    """从数据中提取POI（地点）相关信息"""
    poi = find_want(data, 'poi')
    if not poi:
        return None, None, None, None
    name = poi.get('title') if isinstance(poi, dict) else None
    address = poi.get('address') if isinstance(poi, dict) else None
    rating = poi.get('rating') if isinstance(poi, dict) else None
    avg_price = poi.get('avg_price') if isinstance(poi, dict) else None
    return name, address, rating, avg_price


def handler(page, keyword):
    """处理单个关键词的爬取"""
    recorder = create_csv(keyword)
    page.listen.start('web/v1/feed')
    page.get(f'https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_profile_page')
    page.wait.load_start()

    s = set()
    logger.info(f'开始爬取【{keyword}】相关数据...')

    data_count = 0
    max_count = 20
    error_count = 0
    scroll_interval = 5

    while data_count < max_count:
        try:
            cards = page.eles('xpath://*[@id="global"]/div[2]/div[2]/div/div/div[3]/div[1]/section')
            for card in cards:
                if data_count >= max_count:
                    break

                index = card.attr('data-index')
                if index in s:
                    continue
                s.add(index)

                logger.info(f'正在处理卡片索引 {index}，当前成功采集 {data_count} 条...')

                try:
                    img_elem = card.ele('xpath:./div/a[2]/img', timeout=3)
                    img_elem.click(by_js=True)
                except Exception:
                    card.click(by_js=True)

                res = page.listen.wait(count=1, timeout=3, fit_count=True)
                if not res:
                    logger.warning(f'卡片 {index} 未捕获到数据接口，跳过')
                    continue

                data = res.response.body
                if not data:
                    logger.warning(f'卡片 {index} 接口返回数据为空，跳过')
                    continue

                nickname = find_want(data, 'nickname')
                title = find_want(data, 'title')
                desc = find_want(data, 'desc')
                comment_count = find_want(data, 'comment_count')
                liked_count = find_want(data, 'liked_count')
                poi_name, poi_address, poi_rating, poi_avg_price = extract_poi_info(data)

                row_data = {
                    '博主昵称': nickname,
                    '笔记标题': title,
                    '笔记详情': desc,
                    '评论数': comment_count,
                    '点赞数': liked_count,
                    '店铺名称': poi_name,
                    '店铺地址': poi_address,
                    '店铺评分': poi_rating,
                    '人均价格': poi_avg_price,
                }
                recorder.add_data(row_data)
                recorder.record()  # DataRecorder 的 record() 方法默认是追加写入
                data_count += 1
                logger.info(f'成功采集第 {data_count} 条数据（卡片索引 {index}）')

                try:
                    close_btn = page.ele('xpath:/html/body/div[5]/div[2]/div', timeout=2)
                    if close_btn:
                        close_btn.click()
                except Exception:
                    pass
                page.wait.load_start()

                if data_count % scroll_interval == 0:
                    logger.info('页面滚动以加载更多内容...')
                    page.scroll.down(1000)
                    page.wait.load_start()

        except Exception as e:
            logger.warning(f'外层循环异常: {e}')
            error_count += 1
            if error_count > max_count:
                logger.error(f'错误次数超过 {max_count}，停止采集！')
                break
            continue

    # 爬完自动添加BOM，解决乱码（已兼容追加模式）
    filename = f'{keyword.strip()}.csv'
    add_utf8_bom(filename)
    logger.info(f'已自动修复文件编码，Excel打开不再乱码：{filename}')

    if data_count >= max_count:
        logger.info(f'已成功采集 {data_count} 条数据，【{keyword}】爬取完成！')
    else:
        logger.info(f'【{keyword}】采集未完成，共采集到 {data_count} 条数据')


def main():
    page = ChromiumPage()
    page.get('https://www.xiaohongshu.com/explore')
    input('请扫码登录，登录成功后按回车继续（如已登录请直接回车）')
    keyword = '上海餐饮'
    handler(page, keyword)


if __name__ == '__main__':
    main()