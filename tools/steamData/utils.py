"""
工具模块 - 多策略网络连接、路径与 URL 校验

国内访问 Steam：常见有效做法是 Clash / V2 等提供本地 HTTP 代理（如 7890），
请求必须走该代理；此前实现检测到代理却仍强制直连，会导致一直连接失败。
"""
from __future__ import annotations

import logging
import os
import re
import socket
import time
import warnings
from functools import wraps
from typing import Any

import requests
import requests.adapters
from urllib3.exceptions import InsecureRequestWarning

import config

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


def _proxies_key(proxies: dict[str, str] | None) -> str:
    if not proxies:
        return "direct"
    return "|".join(f"{k}={proxies[k]}" for k in sorted(proxies.keys()))


def _proxy_from_winregistry() -> dict[str, str] | None:
    import winreg

    try:
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if not proxy_enable:
                return None
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            if "=" in proxy_server:
                proxies: dict[str, str] = {}
                for part in proxy_server.split(";"):
                    if "=" in part:
                        protocol, address = part.split("=", 1)
                        proxies[protocol] = f"http://{address}"
                return proxies if proxies else None
            return {
                "http": f"http://{proxy_server}",
                "https": f"http://{proxy_server}",
            }
    except OSError:
        return None


def _proxy_from_env() -> dict[str, str] | None:
    http_proxy = os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    if not (http_proxy or https_proxy):
        return None
    return {
        "http": http_proxy or https_proxy,
        "https": https_proxy or http_proxy,
    }


def _proxy_from_common_ports() -> dict[str, str] | None:
    ports = (
        7890,
        7891,
        7897,
        10809,
        10808,
        10810,
        1080,
        1081,
        1082,
        57000,
        57001,
        57002,
        8080,
        8081,
        8118,
        9999,
        10000,
    )
    for port in ports:
        sock: socket.socket | None = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return {
                    "http": f"http://127.0.0.1:{port}",
                    "https": f"http://127.0.0.1:{port}",
                }
        except OSError:
            pass
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
    return None


def _iter_autodetected_proxy_sources() -> list[tuple[str, dict[str, str]]]:
    """按常见优先级排列的自动探测代理（逐项去重）。"""
    out: list[tuple[str, dict[str, str]]] = []
    seen: set[str] = set()

    def add(label: str, p: dict[str, str] | None) -> None:
        if not p:
            return
        k = _proxies_key(p)
        if k in seen:
            return
        seen.add(k)
        out.append((label, p))

    p = _proxy_from_winregistry()
    if p:
        add("Windows 系统 HTTP 代理", p)
    p = _proxy_from_env()
    if p:
        add("环境变量 http(s)_proxy", p)
    p = _proxy_from_common_ports()
    if p:
        add("本机常见代理端口 (如 Clash)", p)
    return out


def connection_strategies() -> list[tuple[str, dict[str, str] | None]]:
    """
    返回 [(说明, proxies 或 None), ...]，按顺序尝试直至成功。
    None 表示直连（不走 HTTP 代理，由系统路由/虚拟网卡接管）。
    """
    manual = config.PROXIES
    detected = _iter_autodetected_proxy_sources()
    autodetected = [x[1] for x in detected]

    direct: tuple[str, dict[str, str] | None] = ("直连 (无 HTTP 代理)", None)
    manual_t: tuple[str, dict[str, str] | None] | None = None
    if manual:
        manual_t = ("config.PROXIES 手动代理", manual)

    blocks: list[tuple[str, dict[str, str] | None]] = []

    strategy = (config.CONNECTION_STRATEGY or "proxy_first").lower()

    if strategy == "direct_only":
        return [direct]

    if strategy == "proxy_only":
        if manual_t:
            blocks.append(manual_t)
        for label, p in detected:
            blocks.append((label, p))
        if not blocks:
            raise RuntimeError(
                "CONNECTION_STRATEGY=proxy_only，但未设置 config.PROXIES，"
                "也未探测到系统/环境/本地端口代理。请填写 PROXIES 或改用 proxy_first。"
            )
        return blocks

    if strategy == "direct_first":
        blocks.append(direct)
        if manual_t:
            blocks.append(manual_t)
        for label, p in detected:
            blocks.append((label, p))
        return blocks

    # proxy_first（默认）
    if manual_t:
        blocks.append(manual_t)
    for label, p in detected:
        blocks.append((label, p))
    blocks.append(direct)
    return blocks


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
    session.headers.update(config.HEADERS)
    if config.STORE_COUNTRY_COOKIE:
        session.headers["Cookie"] = config.STORE_COUNTRY_COOKIE
    return session


def get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = _build_session()
    return _http_session


def reset_http_session() -> None:
    """代理/Cookie 等变更后丢弃旧 Session，下次请求重建。"""
    global _http_session
    if _http_session is not None:
        try:
            _http_session.close()
        except Exception:
            pass
        _http_session = None


def get_system_proxy() -> dict[str, str] | None:
    """兼容旧接口：返回第一个自动探测到的代理（可能为 None）。"""
    for _, p in _iter_autodetected_proxy_sources():
        return p
    return None


def retry_on_failure(max_retries=None, delay=None):
    """重试装饰器 - 指数退避（供其它模块可选使用）。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mr = config.MAX_RETRIES if max_retries is None else max_retries
            d = config.RETRY_DELAY if delay is None else delay
            last_exception: BaseException | None = None
            for attempt in range(1, mr + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException,
                ) as e:
                    last_exception = e
                    wait_time = d * (2 ** (attempt - 1))
                    logger.warning(f"第 {attempt} 次尝试失败: {str(e)[:80]}")
                    if attempt < mr:
                        logger.info(f"等待 {wait_time} 秒后重试…")
                        time.sleep(wait_time)
            logger.error(f"已重试 {mr} 次，全部失败")
            if last_exception:
                raise last_exception
            raise RuntimeError("retry: no exception captured")

        return wrapper

    return decorator


def _request_timeout_tuple() -> float | tuple[float, float]:
    return (float(config.CONNECT_TIMEOUT), float(config.READ_TIMEOUT))


def send_request(url: str, timeout: Any = None) -> requests.Response:
    """
    GET：在多种连接方式之间切换（代理 / 直连），每种方式内再按次重试。
    """
    if timeout is None:
        timeout = _request_timeout_tuple()
    elif isinstance(timeout, (int, float)):
        timeout = (min(15.0, float(timeout)), float(timeout))

    session = get_http_session()
    strategies = connection_strategies()
    last_error: BaseException | None = None

    for strat_label, proxies in strategies:
        pkey = _proxies_key(proxies)
        logger.info("─" * 50)
        logger.info(f"连接策略: {strat_label}  [{pkey}]")

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                start = time.time()
                kwargs = {
                    "timeout": timeout,
                    "verify": config.VERIFY_SSL,
                    "proxies": proxies,
                    "trust_env": False,
                }
                logger.info(
                    f"正在请求 (第 {attempt}/{config.MAX_RETRIES} 次): {url[:80]}…"
                )
                response = session.get(url, **kwargs)
                elapsed = time.time() - start
                response.raise_for_status()
                logger.info(
                    f"成功 ({elapsed:.1f}s) 状态 {response.status_code}，策略: {strat_label}"
                )
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{strat_label}] 第 {attempt} 次失败: {str(e)[:120]}"
                )
                if attempt < config.MAX_RETRIES:
                    wait_time = config.RETRY_DELAY * (2 ** (attempt - 1))
                    time.sleep(wait_time)
        logger.warning(f"[{strat_label}] 已用尽重试，尝试下一连接方式…")

    if last_error:
        raise last_error
    raise RuntimeError("send_request: no strategy succeeded")


def download_bytes(url: str, timeout: Any = None) -> bytes | None:
    if timeout is None:
        timeout = _request_timeout_tuple()
    try:
        r = send_request(url, timeout=timeout)
        return r.content
    except Exception as e:
        logger.error(f"下载二进制失败: {e}")
        return None


def get_script_directory() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_excel_path() -> str:
    return os.path.join(get_script_directory(), config.EXCEL_FILENAME)


def is_file_open(filepath: str) -> bool:
    try:
        with open(filepath, "r+b"):
            return False
    except OSError:
        return True
    except FileNotFoundError:
        return False


def validate_steam_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    if config.STEAM_STORE_URL_PATTERN not in url:
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
