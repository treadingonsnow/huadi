# Scrapy 中间件
# 功能：
# - RandomUserAgentMiddleware    随机User-Agent轮换（维护UA列表，每次请求随机选择）
# - ProxyMiddleware              代理IP中间件（从代理池获取IP，失败自动切换）
# - RetryMiddleware              自定义重试中间件（针对反爬响应码重试，最多3次）
# - SeleniumMiddleware           Selenium中间件（处理需要JS渲染的动态页面）


from fake_useragent import UserAgent

class RandomUserAgentMiddleware:
    def __init__(self):
        self.ua = UserAgent()

    def process_request(self, request, spider):
        # 每次请求随机更换User-Agent，降低被封概率
        request.headers["User-Agent"] = self.ua.random
