"""
工具模块 - 重试机制、代理检测、路径管理等通用功能
"""
import os
import time
import logging
import winreg
import socket
from functools import wraps

import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

from config import MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT, HEADERS, PROXIES, STORE_COUNTRY_COOKIE

# 屏蔽SSL警告
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_system_proxy():
    """自动检测 Windows 系统代理设置"""
    try:
        registry_path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            proxy_enable, _ = winreg.QueryValueEx(key, 'ProxyEnable')
            if proxy_enable:
                proxy_server, _ = winreg.QueryValueEx(key, 'ProxyServer')
                if '=' in proxy_server:
                    proxies = {}
                    for part in proxy_server.split(';'):
                        if '=' in part:
                            protocol, address = part.split('=', 1)
                            proxies[protocol] = f'http://{address}'
                    if proxies:
                        logger.info(f"✅ 检测到系统代理")
                        return proxies
                else:
                    proxies = {
                        'http': f'http://{proxy_server}',
                        'https': f'http://{proxy_server}'
                    }
                    logger.info(f"✅ 检测到系统代理")
                    return proxies
    except Exception:
        pass
    
    # 检测常见加速器端口
    common_ports = [7890, 7891, 10809, 10810, 1080, 1081, 1082, 57000, 57001, 57002, 8080, 8081, 9999, 10000]
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                proxies = {'http': f'http://127.0.0.1:{port}', 'https': f'http://127.0.0.1:{port}'}
                logger.info(f"✅ 检测到本地代理端口 {port}")
                return proxies
        except Exception:
            pass
    
    # 检查环境变量
    http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
    if http_proxy or https_proxy:
        logger.info(f"✅ 从环境变量检测到代理")
        return {'http': http_proxy or https_proxy, 'https': https_proxy or http_proxy}
    
    return None


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """重试装饰器 - 使用指数退避策略"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout, 
                       requests.exceptions.ConnectionError,
                       requests.exceptions.RequestException) as e:
                    last_exception = e
                    # 指数退避：第1次3秒，第2次6秒，第3次12秒...
                    wait_time = delay * (2 ** (attempt - 1))
                    logger.warning(f"⚠️ 第{attempt}次尝试失败: {str(e)[:80]}")
                    if attempt < max_retries:
                        logger.info(f"⏳ 等待{wait_time}秒后重试...")
                        time.sleep(wait_time)
            logger.error(f"❌ 已重试{max_retries}次，全部失败")
            raise last_exception
        return wrapper
    return decorator


def send_request(url, timeout=REQUEST_TIMEOUT):
    """发送HTTP GET请求，支持虚拟网卡模式（UU加速器等）"""
    # 如果手动配置了PROXIES，使用配置的代理
    if PROXIES:
        active_proxies = PROXIES
        logger.info(f"✅ 使用手动配置的代理")
    else:
        # 否则尝试自动检测系统代理
        detected_proxy = get_system_proxy()
        if detected_proxy:
            logger.info(f"⚠️ 检测到系统代理端口，但将优先使用虚拟网卡直连")
            logger.info(f"💡 如果直连失败，请在config.py中手动配置正确的代理")
        # 对于虚拟网卡模式的加速器（如UU），不应该使用HTTP代理
        # 直接设置为None，让系统路由自动处理
        active_proxies = None
    
    @retry_on_failure()
    def _request():
        # 创建Session以复用连接
        session = requests.Session()
        
        # 配置连接池参数
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,  # 我们已经自己实现了重试
            pool_block=False
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        kwargs = {
            'headers': HEADERS,
            'timeout': timeout,
            'verify': False,
        }
        # 只有当明确配置了代理时才使用
        if active_proxies:
            kwargs['proxies'] = active_proxies
            logger.debug(f"使用HTTP代理: {active_proxies}")
        else:
            logger.debug("使用直连（虚拟网卡模式）")
        
        if STORE_COUNTRY_COOKIE:
            kwargs['headers'] = HEADERS.copy()
            kwargs['headers']['Cookie'] = STORE_COUNTRY_COOKIE
        
        import time
        start_time = time.time()
        logger.info(f"🌐 正在连接: {url}")
        try:
            response = session.get(url, **kwargs)
            elapsed = time.time() - start_time
            response.raise_for_status()
            logger.info(f"✅ 连接成功 ({elapsed:.1f}秒)，状态码: {response.status_code}")
            return response
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ 连接失败 (耗时{elapsed:.1f}秒): {str(e)[:100]}")
            raise
        finally:
            session.close()  # 关闭session
    
    return _request()


def get_script_directory():
    """获取脚本所在目录的绝对路径"""
    return os.path.dirname(os.path.abspath(__file__))


def get_excel_path():
    """获取Excel文件的完整路径"""
    from config import EXCEL_FILENAME
    return os.path.join(get_script_directory(), EXCEL_FILENAME)


def is_file_open(filepath):
    """检查文件是否被其他程序打开"""
    try:
        with open(filepath, 'r+b'):
            return False
    except IOError:
        return True
    except FileNotFoundError:
        return False


def validate_steam_url(url):
    """验证Steam商店URL格式"""
    from config import STEAM_STORE_URL_PATTERN
    if not url or not url.startswith('http'):
        return False
    if STEAM_STORE_URL_PATTERN not in url:
        return False
    import re
    return bool(re.search(r'/app/\d+/', url))


def clean_steam_url(url):
    """清理Steam URL，移除追踪参数和多余字符"""
    import re
    match = re.search(r'(https?://store\.steampowered\.com/app/\d+/)', url)
    if match:
        return match.group(1)
    url = url.split('?')[0]
    url = url.rstrip('/')
    if url.endswith('/_'):
        url = url[:-2]
    return url.rstrip('/') + '/'
