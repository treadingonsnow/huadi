import json
import re
from urllib.parse import quote

import scrapy


class XiaohongshuSpider(scrapy.Spider):
    name = "xiaohongshu_spider"
    allowed_domains = ["xiaohongshu.com", "www.xiaohongshu.com"]
    keyword = "上海餐饮"
    max_count = 20

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "DOWNLOAD_DELAY": 2,
        "RETRY_TIMES": 2,
    }

    def start_requests(self):
        search_url = (
            "https://www.xiaohongshu.com/search_result"
            f"?keyword={quote(self.keyword)}&source=web_profile_page"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.xiaohongshu.com/",
        }
        yield scrapy.Request(
            url=search_url,
            headers=headers,
            callback=self.parse_search,
        )

    def parse_search(self, response):
        self.logger.info(f"SEARCH URL: {response.url}")
        self.logger.info(f"SEARCH STATUS: {response.status}")
        self.logger.info(f"SEARCH TITLE: {response.xpath('//title/text()').get()}")

        if self._is_blocked(response):
            self.logger.warning("搜索页疑似被拦截或跳转到登录/风控页")
            return

        hrefs = response.xpath("//a[contains(@href, '/explore/')]/@href").getall()
        hrefs += response.xpath("//a[contains(@href, '/discovery/item/')]/@href").getall()

        # 去重并限制数量
        seen = set()
        note_urls = []
        for href in hrefs:
            full_url = response.urljoin(href)
            if full_url not in seen:
                seen.add(full_url)
                note_urls.append(full_url)
            if len(note_urls) >= self.max_count:
                break

        self.logger.info(f"提取到笔记链接数量: {len(note_urls)}")

        for url in note_urls:
            yield scrapy.Request(
                url=url,
                headers={"Referer": response.url},
                callback=self.parse_note,
            )

    def parse_note(self, response):
        self.logger.info(f"NOTE URL: {response.url}")
        self.logger.info(f"NOTE STATUS: {response.status}")

        if self._is_blocked(response):
            self.logger.warning(f"详情页被拦截: {response.url}")
            return

        page_text = response.text

        # 尝试从页面脚本中抓 JSON
        data = self._extract_embedded_json(page_text)

        if not data:
            self.logger.warning(f"未能从详情页提取嵌入式 JSON: {response.url}")
            return

        nickname = self.find_want(data, "nickname")
        title = self.find_want(data, "title")
        desc = self.find_want(data, "desc")
        comment_count = self.find_want(data, "comment_count")
        liked_count = self.find_want(data, "liked_count")
        poi_name, poi_address, poi_rating, poi_avg_price = self.extract_poi_info(data)

        item = {
            "keyword": self.keyword,
            "source_url": response.url,
            "博主昵称": nickname,
            "笔记标题": title,
            "笔记详情": desc,
            "评论数": comment_count,
            "点赞数": liked_count,
            "店铺名称": poi_name,
            "店铺地址": poi_address,
            "店铺评分": poi_rating,
            "人均价格": poi_avg_price,
        }

        # 至少有标题或正文时再输出
        if item["笔记标题"] or item["笔记详情"]:
            yield item
        else:
            self.logger.warning(f"页面解析成功但未拿到核心字段: {response.url}")

    def _is_blocked(self, response):
        text = response.text.lower()
        title = response.xpath("//title/text()").get(default="")
        blocked_keywords = [
            "登录",
            "验证码",
            "安全验证",
            "请求异常",
            "访问受限",
            "please login",
        ]
        if response.status in [301, 302, 403, 429]:
            return True
        if any(k.lower() in text for k in blocked_keywords):
            return True
        if any(k in title for k in ["登录", "验证", "异常"]):
            return True
        return False

    def _extract_embedded_json(self, html):
        """
        尝试从页面 script 中提取 JSON。
        小红书页面结构会变，这里做几个宽松匹配。
        """
        patterns = [
            r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;</script>",
            r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
            r"__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
            r"window\.__INITIAL_SSR_STATE__\s*=\s*(\{.*?\})\s*;",
        ]

        for pattern in patterns:
            m = re.search(pattern, html, re.S)
            if m:
                raw = m.group(1)
                try:
                    return json.loads(raw)
                except Exception:
                    continue

        # 兜底：尝试抓取所有 script[type='application/json']
        json_scripts = re.findall(
            r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
            html,
            re.S,
        )
        for raw in json_scripts:
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, (dict, list)):
                    return data
            except Exception:
                continue

        return None

    def find_want(self, data, target_key):
        """
        递归查找目标字段值。
        这是沿用你原脚本的核心思路。
        """
        if isinstance(data, dict):
            for key, val in data.items():
                if key == target_key:
                    return val
                ret = self.find_want(val, target_key)
                if ret is not None:
                    return ret
        elif isinstance(data, list):
            for item in data:
                ret = self.find_want(item, target_key)
                if ret is not None:
                    return ret
        return None

    def extract_poi_info(self, data):
        """
        从数据中提取 POI（地点）相关信息。
        这部分逻辑也沿用你原脚本。
        """
        poi = self.find_want(data, "poi")
        if not poi or not isinstance(poi, dict):
            return None, None, None, None

        name = poi.get("title")
        address = poi.get("address")
        rating = poi.get("rating")
        avg_price = poi.get("avg_price")
        return name, address, rating, avg_price