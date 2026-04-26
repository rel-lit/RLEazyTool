"""
UU加速器诊断工具 - 检查虚拟网卡是否正常工作
"""
import socket
import subprocess
import time
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

def check_virtual_nic():
    """检查虚拟网卡是否存在"""
    print("=" * 60)
    print("UU加速器虚拟网卡诊断工具")
    print("=" * 60)
    print()
    
    print("【步骤1】检查虚拟网卡...")
    print("-" * 60)
    try:
        # 运行ipconfig命令
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
        output = result.stdout
        
        # 查找常见的虚拟网卡名称
        virtual_nic_keywords = ['TAP', 'TUN', 'UU', '加速', 'Virtual', 'Adapter']
        found_vnic = False
        
        for line in output.split('\n'):
            if any(keyword.lower() in line.lower() for keyword in virtual_nic_keywords):
                print(f"✅ 发现虚拟网卡: {line.strip()}")
                found_vnic = True
        
        if not found_vnic:
            print("❌ 未发现虚拟网卡")
            print("💡 请确认UU加速器已开启并选择了Steam游戏")
        else:
            print("✅ 虚拟网卡检测通过")
    except Exception as e:
        print(f"⚠️ 检查虚拟网卡失败: {e}")
    print()
    
    print("【步骤2】检查路由表...")
    print("-" * 60)
    try:
        result = subprocess.run(['route', 'print'], capture_output=True, text=True, encoding='gbk')
        output = result.stdout
        
        # 检查是否有特殊路由
        if '0.0.0.0' in output or 'default' in output.lower():
            print("✅ 路由表正常")
        
        # 统计路由条目
        routes = [line for line in output.split('\n') if line.strip() and '0.0.0.0' in line]
        print(f"📊 默认路由数量: {len(routes)}")
    except Exception as e:
        print(f"⚠️ 检查路由表失败: {e}")
    print()
    
    print("【步骤3】测试DNS解析...")
    print("-" * 60)
    test_domains = [
        'store.steampowered.com',
        'steamcommunity.com',
        'cdn.akamai.steamstatic.com'
    ]
    
    for domain in test_domains:
        try:
            start = time.time()
            ips = socket.getaddrinfo(domain, 443)
            elapsed = time.time() - start
            if ips:
                ip = ips[0][4][0]
                print(f"✅ {domain:35s} → {ip:15s} ({elapsed:.2f}s)")
            else:
                print(f"❌ {domain:35s} → 解析失败")
        except Exception as e:
            print(f"❌ {domain:35s} → {str(e)[:40]}")
    print()
    
    print("【步骤4】测试直连Steam...")
    print("-" * 60)
    test_urls = [
        ("Steam商店", "https://store.steampowered.com/app/1091500/"),
        ("Steam CDN", "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg"),
    ]
    
    for name, url in test_urls:
        try:
            print(f"正在测试 {name}...", end=" ")
            start = time.time()
            response = requests.get(url, timeout=15, verify=False)
            elapsed = time.time() - start
            if response.status_code == 200:
                print(f"✅ 成功 ({elapsed:.1f}s) - {len(response.content)} bytes")
            else:
                print(f"⚠️ 状态码 {response.status_code} ({elapsed:.1f}s)")
        except requests.exceptions.Timeout:
            print(f"❌ 超时 (15秒)")
        except Exception as e:
            print(f"❌ 失败: {str(e)[:50]}")
    print()
    
    print("=" * 60)
    print("诊断完成！")
    print("=" * 60)
    print()
    print("💡 常见问题解决:")
    print("  1. 如果未发现虚拟网卡 → 重启UU加速器")
    print("  2. 如果DNS解析失败 → 运行 ipconfig /flushdns")
    print("  3. 如果直连超时 → 更换UU加速节点")
    print("  4. 如果都失败 → 尝试使用HTTP代理模式")
    print()

if __name__ == '__main__':
    check_virtual_nic()
