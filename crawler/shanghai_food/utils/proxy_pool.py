# 代理IP池管理
# 功能：
# - get_proxy()          从代理池获取一个可用代理IP
# - return_proxy()       归还代理IP（标记为可用/不可用）
# - check_proxy()        检测代理IP可用性
# - refresh_pool()       刷新代理池（从代理服务商获取新IP）
# 支持：HTTP/HTTPS代理，SOCKS5代理
# 策略：失败自动切换，连续失败3次标记为不可用
