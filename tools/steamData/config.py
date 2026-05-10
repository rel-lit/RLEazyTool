"""
配置模块 - 管理请求头、常量等配置信息
"""

# 请求头配置，模拟真实浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    # 不显式要求 br，避免少数环境缺少 brotli 解码失败
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Cookie（可选）- 区域与语言偏好；写入 Session 默认头
STORE_COUNTRY_COOKIE = (
    "birthtime=0; lastagecheckage=1-January-1990; mature_content=1; "
    "wants_mature_content=1; Steam_Language=schinese; steamCountry=CN"
)
# STORE_COUNTRY_COOKIE = None  # 若无需强制国区可关闭

# Store API（优先于 HTML 解析，更抗页面改版）
USE_STORE_API = True
STEAM_API_LANGUAGE = "schinese"
STEAM_API_CC = "cn"

# 网络请求配置（每个「连接策略」内会重试）
REQUEST_TIMEOUT = 90  # 兼容旧逻辑：未使用元组超时时作为总秒数
MAX_RETRIES = 4
RETRY_DELAY = 4

# 代理：手动指定则优先级最高；未指定时由 utils 按策略自动探测（系统代理 / 环境变量 / 常见端口）
# PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXIES = None

# 连接策略（解决「有 Clash 却仍直连被墙」问题）
# - proxy_first:  手动代理 → 系统代理 → 环境变量 → 常见本机端口 → 直连（依次尝试，国内常用）
# - direct_first: 先直连（适合只开 UU 虚拟网卡、没有 HTTP 代理时），再尝试上述代理
# - proxy_only:   仅使用探测到的代理，失败不降级直连（便于排错）
# - direct_only:  始终直连
CONNECTION_STRATEGY = "proxy_first"

# 超时：分离「建立连接」与「读响应」，避免长时间卡在握手
CONNECT_TIMEOUT = 15
READ_TIMEOUT = 75

# TLS：部分网络环境需关闭校验（与现有行为一致）；若你可正常验证证书可改为 True
VERIFY_SSL = False

# Excel文件配置
EXCEL_FILENAME = 'steam_games.xlsx'
DEFAULT_ROW_HEIGHT = 20  # 默认行高
IMAGE_COLUMN_WIDTH = 40  # 图片列宽度

# Steam URL模式
STEAM_STORE_URL_PATTERN = 'store.steampowered.com/app/'


def refresh_config_from_disk() -> None:
    """从 steamdata_config.json 重新加载（终端执行 reload 时调用）。"""
    from settings_store import load_and_apply

    load_and_apply()


# 启动时合并用户 JSON（若存在）
refresh_config_from_disk()
