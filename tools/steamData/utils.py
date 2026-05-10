"""
工具模块 - 重试机制、代理检测、路径管理等通用功能
"""
from __future__ import annotations

import logging
import os
import re
import socket
import time
import warnings
from functools import wraps

import requests
import requests.adapters
from urllib3.exceptions import InsecureRequestWarning

from config import (
    HEADERS,
    MAX_RETRIES,
    PROXIES,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    STORE_COUNTRY_COOKIE,
)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
_lvl = os.environ.get("STEAMDATA_LOG", "INFO").upper()
logging.getLogger().setLevel(getattr(logging, _lvl, logging.INFO))
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_http_session: requests.Session | None = None


def _active_proxies() -> dict[str, str] | None:
    if PROXIES:
        logger.info("使用手动配置的代理（config.PROXIES）")
        return PROXIES
    detected = get_system_proxy()
    if detected:
        logger.info("检测到系统/环境代理，当前仍默认直连（虚拟网卡模式）")
        logger.info("若直连失败，请在 config.py 中设置 PROXIES")
    return None


def _build_session() -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
        max_retries=0,
        pool_block=False,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    if STORE_COUNTRY_COOKIE:
        session.headers["Cookie"] = STORE_COUNTRY_COOKIE
    return session


def get_http_session() -> requests.Session:
    """进程内复用的 Session（连接池、Cookie、默认头）。"""
    global _http_session
    if _http_session is None:
        _http_session = _build_session()
    return _http_session


def get_system_proxy():
    """自动检测 Windows 系统代理设置"""
    import winreg

    try:
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if proxy_enable:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                if "=" in proxy_server:
                    proxies = {}
                    for part in proxy_server.split(";"):
                        if "=" in part:
                            protocol, address = part.split("=", 1)
                            proxies[protocol] = f"http://{address}"
                    if proxies:
                        logger.info("检测到系统代理（多协议）")
                        return proxies
                proxies = {
                    "http": f"http://{proxy_server}",
                    "https": f"http://{proxy_server}",
                }
                logger.info("检测到系统代理")
                return proxies
    except Exception:
        pass

    common_ports = [
        7890,
        7891,
        10809,
        10810,
        1080,
        1081,
        1082,
        57000,
        57001,
        57002,
        8080,
        8081,
        9999,
        10000,
    ]
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                proxies = {
                    "http": f"http://127.0.0.1:{port}",
                    "https": f"http://127.0.0.1:{port}",
                }
                logger.info(f"检测到本地代理端口 {port}")
                return proxies
        except Exception:
            pass

    http_proxy = os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    if http_proxy or https_proxy:
        logger.info("从环境变量检测到代理")
        return {
            "http": http_proxy or https_proxy,
            "https": https_proxy or http_proxy,
        }

    return None


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """重试装饰器 - 指数退避"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException,
                ) as e:
                    last_exception = e
                    wait_time = delay * (2 ** (attempt - 1))
                    logger.warning(f"第{attempt}次尝试失败: {str(e)[:80]}")
                    if attempt < max_retries:
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
            logger.error(f"已重试 {max_retries} 次，全部失败")
            if last_exception:
                raise last_exception
            raise RuntimeError("retry: no exception captured")

        return wrapper

    return decorator


def send_request(url: str, timeout: float = REQUEST_TIMEOUT) -> requests.Response:
    """GET 请求（复用 Session、重试、与主程序相同的 TLS/代理策略）。"""
    active_proxies = _active_proxies()
    session = get_http_session()

    @retry_on_failure()
    def _do_get() -> requests.Response:
        kwargs: dict = {"timeout": timeout, "verify": False}
        if active_proxies:
            kwargs["proxies"] = active_proxies
        logger.info(f"正在连接: {url}")
        start = time.time()
        try:
            response = session.get(url, **kwargs)
            elapsed = time.time() - start
            response.raise_for_status()
            logger.info(
                f"连接成功 ({elapsed:.1f}s)，状态码: {response.status_code}"
            )
            return response
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"连接失败 (耗时 {elapsed:.1f}s): {str(e)[:120]}")
            raise

    return _do_get()


def download_bytes(url: str, timeout: float = REQUEST_TIMEOUT) -> bytes | None:
    """下载二进制（封面图等），失败返回 None。"""
    try:
        r = send_request(url, timeout=timeout)
        return r.content
    except Exception as e:
        logger.error(f"下载二进制失败: {e}")
        return None


def get_script_directory() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_excel_path() -> str:
    from config import EXCEL_FILENAME

    return os.path.join(get_script_directory(), EXCEL_FILENAME)


def is_file_open(filepath: str) -> bool:
    try:
        with open(filepath, "r+b"):
            return False
    except OSError:
        return True
    except FileNotFoundError:
        return False


def validate_steam_url(url: str) -> bool:
    from config import STEAM_STORE_URL_PATTERN

    if not url or not url.startswith("http"):
        return False
    if STEAM_STORE_URL_PATTERN not in url:
        return False
    return bool(re.search(r"/app/\d+/", url))


def clean_steam_url(url: str) -> str:
    match = re.search(r"(https?://store\.steampowered\.com/app/\d+/)", url)
    if match:
        return match.group(1)
    url = url.split("?")[0]
    url = url.rstrip("/")
    if url.endswith("/_"):
        url = url[:-2]
    return url.rstrip("/") + "/"
