"""
快速测试脚本 - 验证模块导入和基本功能
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块是否可以正常导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    modules = [
        ('config', '配置模块'),
        ('utils', '工具模块'),
        ('scraper', '爬虫模块'),
        ('excel_handler', 'Excel处理模块'),
        ('main', '主程序模块'),
    ]
    
    failed = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {description} ({module_name}) - 导入成功")
        except ImportError as e:
            print(f"✗ {description} ({module_name}) - 导入失败: {str(e)}")
            failed.append(module_name)
    
    print()
    if failed:
        print(f"⚠️  以下模块导入失败（可能是缺少依赖库）:")
        for module in failed:
            print(f"   - {module}")
        print("\n请运行: pip install -r requirements.txt")
        return False
    else:
        print("✓ 所有模块导入成功!")
        return True


def test_config():
    """测试配置模块"""
    print("\n" + "=" * 60)
    print("测试配置模块...")
    print("=" * 60)
    
    try:
        from config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
        print(f"✓ 请求头配置: {len(HEADERS)} 个字段")
        print(f"✓ 超时时间: {REQUEST_TIMEOUT} 秒")
        print(f"✓ 最大重试次数: {MAX_RETRIES}")
        print(f"✓ 重试间隔: {RETRY_DELAY} 秒")
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {str(e)}")
        return False


def test_utils():
    """测试工具模块"""
    print("\n" + "=" * 60)
    print("测试工具模块...")
    print("=" * 60)
    
    try:
        from utils import get_script_directory, get_excel_path, validate_steam_url
        
        script_dir = get_script_directory()
        print(f"✓ 脚本目录: {script_dir}")
        
        excel_path = get_excel_path()
        print(f"✓ Excel路径: {excel_path}")
        
        # 测试URL验证
        test_urls = [
            ("https://store.steampowered.com/app/123/Game/", True),
            ("http://store.steampowered.com/app/456/Test/", True),
            ("https://example.com", False),
            ("invalid", False),
        ]
        
        all_passed = True
        for url, expected in test_urls:
            result = validate_steam_url(url)
            status = "✓" if result == expected else "✗"
            print(f"{status} URL验证: {url[:50]}... -> {result} (期望: {expected})")
            if result != expected:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ 工具模块测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\nSteam游戏数据抓取工具 - 测试套件\n")
    
    results = []
    
    # 测试导入
    results.append(("模块导入", test_imports()))
    
    # 测试配置
    try:
        results.append(("配置模块", test_config()))
    except Exception as e:
        print(f"✗ 配置模块测试异常: {str(e)}")
        results.append(("配置模块", False))
    
    # 测试工具
    try:
        results.append(("工具模块", test_utils()))
    except Exception as e:
        print(f"✗ 工具模块测试异常: {str(e)}")
        results.append(("工具模块", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 程序可以正常运行。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
