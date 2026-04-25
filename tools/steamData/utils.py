"""
工具模块 - 提供重试机制、路径管理等通用功能
"""
import os
import time
import logging
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


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    重试装饰器：当函数执行失败时自动重试
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    
    Returns:
        装饰器函数
    """
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
                    logger.warning(f"第{attempt}次尝试失败: {str(e)}")
                    if attempt < max_retries:
                        logger.info(f"等待{delay}秒后重试...")
                        time.sleep(delay)
                    else:
                        logger.error(f"已达到最大重试次数({max_retries})，放弃请求")
            
            raise last_exception
        return wrapper
    return decorator


def send_request(url, timeout=REQUEST_TIMEOUT):
    """
    发送HTTP GET请求，带重试机制
    
    Args:
        url: 请求URL
        timeout: 超时时间（秒）
    
    Returns:
        requests.Response对象
    
    Raises:
        requests.exceptions.RequestException: 请求失败异常
    """
    @retry_on_failure()
    def _request():
        # 准备请求参数
        kwargs = {
            'headers': HEADERS,
            'timeout': timeout,
            'verify': False,
            'proxies': PROXIES
        }
        
        # 如果配置了Cookie，添加到请求中
        if STORE_COUNTRY_COOKIE:
            kwargs['headers'] = HEADERS.copy()
            kwargs['headers']['Cookie'] = STORE_COUNTRY_COOKIE
        
        response = requests.get(url, **kwargs)
        response.raise_for_status()
        return response
    
    return _request()


def get_script_directory():
    """
    获取脚本所在目录的绝对路径
    
    Returns:
        脚本目录的绝对路径
    """
    return os.path.dirname(os.path.abspath(__file__))


def get_excel_path():
    """
    获取Excel文件的完整路径（基于脚本目录）
    
    Returns:
        Excel文件的绝对路径
    """
    from config import EXCEL_FILENAME
    script_dir = get_script_directory()
    return os.path.join(script_dir, EXCEL_FILENAME)


def is_file_open(filepath):
    """
    检查文件是否被其他程序打开（Windows系统）
    
    Args:
        filepath: 文件路径
    
    Returns:
        bool: 文件是否被打开
    """
    try:
        # 尝试以独占模式打开文件
        with open(filepath, 'r+b'):
            return False
    except IOError:
        return True
    except FileNotFoundError:
        # 文件不存在，自然没有被打开
        return False


def validate_steam_url(url):
    """
    验证Steam商店URL格式
    
    Args:
        url: 待验证的URL
    
    Returns:
        bool: 是否为有效的Steam商店URL
    """
    from config import STEAM_STORE_URL_PATTERN
    
    # 基本检查
    if not url or not url.startswith('http'):
        return False
    
    if STEAM_STORE_URL_PATTERN not in url:
        return False
    
    # 检查是否有有效的游戏ID
    import re
    match = re.search(r'/app/(\d+)/', url)
    if not match:
        return False
    
    return True


def clean_steam_url(url):
    """
    清理Steam URL，移除末尾的多余字符
    
    Args:
        url: 原始URL
    
    Returns:
        str: 清理后的URL
    """
    # 移除末尾的 /_/ 或多余的斜杠
    cleaned = url.rstrip('/')
    if cleaned.endswith('/_'):
        cleaned = cleaned[:-2]
    cleaned = cleaned.rstrip('/') + '/'
    
    return cleaned
