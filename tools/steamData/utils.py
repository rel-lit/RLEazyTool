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
    """重试装饰器"""
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
                    logger.warning(f"第{attempt}次尝试失败: {str(e)[:80]}")
                    if attempt < max_retries:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def send_request(url, timeout=REQUEST_TIMEOUT):
    """发送HTTP GET请求，支持虚拟网卡模式"""
    active_proxies = PROXIES if PROXIES else get_system_proxy()
    
    # 检测是否为虚拟网卡模式
    use_virtual_nic = False
    if active_proxies:
        try:
            test_response = requests.get('https://www.baidu.com', proxies=active_proxies, timeout=5, verify=False)
            if test_response.status_code != 200:
                use_virtual_nic = True
                logger.info("⚠️ HTTP代理不可用，切换到虚拟网卡模式")
        except Exception:
            use_virtual_nic = True
            logger.info("⚠️ HTTP代理连接失败，切换到虚拟网卡模式")
    
    @retry_on_failure()
    def _request():
        kwargs = {
            'headers': HEADERS,
            'timeout': timeout,
            'verify': False,
        }
        if not use_virtual_nic:
            kwargs['proxies'] = active_proxies
        
        if STORE_COUNTRY_COOKIE:
            kwargs['headers'] = HEADERS.copy()
            kwargs['headers']['Cookie'] = STORE_COUNTRY_COOKIE
        
        response = requests.get(url, **kwargs)
        response.raise_for_status()
        return response
    
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
