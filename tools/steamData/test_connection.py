"""
网络连通性测试工具 - 帮助诊断Steam访问问题
"""
import sys
import time
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

def test_connection():
    """测试各种连接方式"""
    print("=" * 60)
    print("Steam 网络连通性测试工具")
    print("=" * 60)
    print()
    
    test_urls = [
        ("Steam商店", "https://store.steampowered.com/app/1091500/"),
        ("Steam社区", "https://steamcommunity.com/"),
        ("百度（国内）", "https://www.baidu.com"),
    ]
    
    # 测试直连
    print("【测试1】直连模式（虚拟网卡加速器）")
    print("-" * 60)
    for name, url in test_urls:
        try:
            print(f"正在测试 {name}...", end=" ")
            start = time.time()
            response = requests.get(url, timeout=10, verify=False)
            elapsed = time.time() - start
            print(f"✅ 成功 ({elapsed:.2f}s) - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 失败: {str(e)[:60]}")
    print()
    
    # 测试常见代理端口
    print("【测试2】检测本地代理端口")
    print("-" * 60)
    common_ports = [7890, 7891, 10809, 10810, 1080, 8080, 8081, 57000, 57001]
    active_ports = []
    
    for port in common_ports:
        try:
            sock = __import__('socket').socket(__import__('socket').AF_INET, __import__('socket').SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"✅ 端口 {port} 正在监听")
                active_ports.append(port)
            else:
                print(f"   端口 {port} 未监听")
        except Exception as e:
            print(f"   端口 {port} 检测失败: {e}")
    print()
    
    # 测试代理连接
    if active_ports:
        print("【测试3】通过代理连接Steam")
        print("-" * 60)
        for port in active_ports[:2]:  # 只测试前2个端口
            proxy_url = f'http://127.0.0.1:{port}'
            proxies = {'http': proxy_url, 'https': proxy_url}
            print(f"\n测试代理: {proxy_url}")
            try:
                print(f"  正在测试 Steam...", end=" ")
                start = time.time()
                response = requests.get(
                    'https://store.steampowered.com/app/1091500/',
                    proxies=proxies,
                    timeout=10,
                    verify=False
                )
                elapsed = time.time() - start
                print(f"✅ 成功 ({elapsed:.2f}s) - 状态码: {response.status_code}")
            except Exception as e:
                print(f"❌ 失败: {str(e)[:60]}")
        print()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print()
    print("💡 建议:")
    print("  1. 如果直连成功 → 你的虚拟网卡加速器工作正常")
    print("  2. 如果直连失败但代理成功 → 在config.py中配置该代理端口")
    print("  3. 如果都失败 → 检查加速器是否开启，或更换节点")
    print()

if __name__ == '__main__':
    test_connection()
