"""
配置模块 - 管理请求头、常量等配置信息
"""

# 请求头配置，模拟真实浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Cookie配置（可选）- 用于设置Steam区域为简体中文
# 如果需要强制显示CN区域，可以添加Cookie
STORE_COUNTRY_COOKIE = 'birthtime=0; lastagecheckage=1-January-1990; mature_content=1; wants_mature_content=1; Steam_Language=schinese; steamCountry=CN'
# STORE_COUNTRY_COOKIE = None

# 网络请求配置
REQUEST_TIMEOUT = 30  # 超时时间（秒）- Steam访问较慢，增加到30秒
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 3  # 重试间隔（秒）

# 代理配置（可选）
# 如果手动配置代理，取消注释并设置；否则将自动检测系统代理
# PROXIES = {
#     'http': 'http://127.0.0.1:7890',
#     'https': 'http://127.0.0.1:7890',
# }
PROXIES = None  # 默认自动检测系统代理

# Excel文件配置
EXCEL_FILENAME = 'steam_games.xlsx'
DEFAULT_ROW_HEIGHT = 20  # 默认行高
IMAGE_COLUMN_WIDTH = 40  # 图片列宽度

# Steam URL模式
STEAM_STORE_URL_PATTERN = 'store.steampowered.com/app/'
