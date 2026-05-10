"""
终端交互配置（风格接近 merge 工具）：修改网络/API/Excel 等并写入 steamdata_config.json。
"""

from __future__ import annotations

import importlib
import shlex

import config
import settings_store
from settings_store import CONFIG_PATH, PERSIST_KEYS
from utils import reset_http_session


def _persist() -> None:
    reset_http_session()
    if settings_store.save_to_disk():
        print(f"✅ 已保存: {CONFIG_PATH}")
    else:
        print("❌ 保存失败，请检查目录权限")


def _print_help() -> None:
    print(
        """
【steamData 终端配置】命令一览（修改后自动 save + 重置连接）
  help              本帮助
  q / quit          退出
  ll / now          列出当前可持久化项
  reload            从磁盘重新加载 JSON（放弃未保存的内存修改若已写入）
  reset             删除 steamdata_config.json，恢复代码默认值（需确认 y）

连接与网络
  strategy <proxy_first|direct_first|proxy_only|direct_only>
  proxy off                    清除手动代理
  proxy <url>                  例: proxy http://127.0.0.1:7890
  connect <秒>                 CONNECT_TIMEOUT
  read <秒>                   READ_TIMEOUT
  retries <n>                  MAX_RETRIES
  delay <秒>                   RETRY_DELAY
  verify on|off                VERIFY_SSL

Store API / 区域
  api on|off                   USE_STORE_API
  lang <字符串>                STEAM_API_LANGUAGE（如 schinese）
  cc <字符串>                  STEAM_API_CC（如 cn）

其它
  excel <文件名>               EXCEL_FILENAME
  cookie default|off           default=内置国区 Cookie；off=清空
  reqto <秒>                   REQUEST_TIMEOUT（兼容部分逻辑）
  rowh <像素>                  DEFAULT_ROW_HEIGHT
  imgcol <字符宽>             IMAGE_COLUMN_WIDTH

文件: {}
""".strip().format(CONFIG_PATH)
    )


def _print_state() -> None:
    print(f"\n─── 当前配置（可持久化项）─── 文件: {CONFIG_PATH}\n")
    for k in sorted(PERSIST_KEYS):
        if not hasattr(config, k):
            continue
        v = getattr(config, k)
        if k == "PROXIES" and v:
            print(f"  {k}: {v}")
        elif k == "STORE_COUNTRY_COOKIE" and v:
            short = (v[:60] + "…") if len(str(v)) > 60 else v
            print(f"  {k}: {short}")
        else:
            print(f"  {k}: {v!r}")
    print()


def _set_cookie_mode(arg: str) -> None:
    a = arg.lower()
    if a == "default":
        config.STORE_COUNTRY_COOKIE = (
            "birthtime=0; lastagecheckage=1-January-1990; mature_content=1; "
            "wants_mature_content=1; Steam_Language=schinese; steamCountry=CN"
        )
    elif a == "off":
        config.STORE_COUNTRY_COOKIE = None
    else:
        config.STORE_COUNTRY_COOKIE = arg
    print(f"✅ STORE_COUNTRY_COOKIE 已更新")
    _persist()


def run_config_repl() -> None:
    print("=" * 56)
    print("  steamData — 终端配置（输入 help 查看指令）")
    print("=" * 56)
    _print_state()
    while True:
        try:
            line = input("⚙ config> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出配置。")
            return
        if not line:
            continue
        parts = shlex.split(line)
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("q", "quit", "exit"):
            print("已退出配置。")
            return
        if cmd in ("help", "?"):
            _print_help()
            continue
        if cmd in ("ll", "now", "list"):
            _print_state()
            continue
        if cmd == "reload":
            config.refresh_config_from_disk()
            reset_http_session()
            print("✅ 已从磁盘重载 config")
            _print_state()
            continue
        if cmd == "reset":
            cfm = input("确认删除用户配置文件并恢复默认? [y/N]: ").strip().lower()
            if cfm == "y":
                settings_store.delete_user_file()
                importlib.reload(config)
                reset_http_session()
                print("✅ 已删除用户配置并重载模块（内存已恢复默认）")
            continue

        try:
            if cmd == "strategy" and len(args) == 1:
                allowed = frozenset(
                    {"proxy_first", "direct_first", "proxy_only", "direct_only"}
                )
                if args[0].lower() not in allowed:
                    print(f"❌ strategy 必须是: {', '.join(sorted(allowed))}")
                    continue
                config.CONNECTION_STRATEGY = args[0].lower()
            elif cmd == "proxy":
                if not args or args[0].lower() == "off":
                    config.PROXIES = None
                else:
                    u = args[0]
                    config.PROXIES = {"http": u, "https": u}
            elif cmd == "connect" and len(args) == 1:
                config.CONNECT_TIMEOUT = int(args[0])
            elif cmd == "read" and len(args) == 1:
                config.READ_TIMEOUT = int(args[0])
            elif cmd == "retries" and len(args) == 1:
                config.MAX_RETRIES = int(args[0])
            elif cmd == "delay" and len(args) == 1:
                config.RETRY_DELAY = int(args[0])
            elif cmd == "verify" and len(args) == 1:
                config.VERIFY_SSL = args[0].lower() in ("1", "true", "on", "yes")
            elif cmd == "api" and len(args) == 1:
                config.USE_STORE_API = args[0].lower() in ("1", "true", "on", "yes")
            elif cmd == "lang" and len(args) == 1:
                config.STEAM_API_LANGUAGE = args[0]
            elif cmd == "cc" and len(args) == 1:
                config.STEAM_API_CC = args[0]
            elif cmd == "excel" and len(args) == 1:
                config.EXCEL_FILENAME = args[0]
            elif cmd == "cookie" and len(args) >= 1:
                raw = " ".join(args)
                _set_cookie_mode(raw)
                continue
            elif cmd == "reqto" and len(args) == 1:
                config.REQUEST_TIMEOUT = int(args[0])
            elif cmd == "rowh" and len(args) == 1:
                config.DEFAULT_ROW_HEIGHT = int(args[0])
            elif cmd == "imgcol" and len(args) == 1:
                config.IMAGE_COLUMN_WIDTH = int(args[0])
            else:
                print("❌ 未知命令或参数，输入 help")
                continue
            print("✅ 已更新内存中的配置")
            _persist()
            continue
        except ValueError as e:
            print(f"❌ 数值无效: {e}")


def main() -> None:
    run_config_repl()


if __name__ == "__main__":
    main()
