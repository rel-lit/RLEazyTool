"""
Steam游戏数据抓取工具 - 主程序

功能：从Steam商店页面抓取游戏信息并保存到Excel文件
"""
import sys
import logging

from scraper import SteamGameScraper
from excel_handler import ExcelHandler
from utils import validate_steam_url, clean_steam_url, logger

logger = logging.getLogger(__name__)


def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("       Steam 游戏数据抓取工具")
    print("=" * 60)
    print()


def print_instructions():
    """打印使用说明"""
    print("使用说明:")
    print("  1. 输入Steam游戏商店页面的完整URL")
    print("     例如: https://store.steampowered.com/app/1091500/")
    print("  2. 程序将自动抓取游戏信息并保存到Excel文件")
    print("  3. 输入 'q' 或 'quit' 退出程序")
    print("  4. 输入 'help' 显示此帮助信息")
    print()
    print("📌 注意:")
    print("  - 程序会自动检测加速器（支持UU、Clash等）")
    print("  - 如需手动配置代理，请编辑 config.py 文件")
    print()


def get_user_input():
    """
    获取用户输入的URL
    
    Returns:
        str: 用户输入的URL，或None表示退出
    """
    try:
        url = input("\n请输入Steam游戏URL (输入'q'退出, 'help'查看帮助): ").strip()
        
        if url.lower() in ['q', 'quit', 'exit']:
            return None
        
        if url.lower() == 'help':
            print_instructions()
            return 'HELP'
        
        return url if url else None
        
    except (KeyboardInterrupt, EOFError):
        print("\n\n检测到退出信号...")
        return None


def process_game_url(url, scraper, excel_handler):
    """
    处理单个游戏URL
    
    Args:
        url: Steam游戏URL
        scraper: 爬虫实例
        excel_handler: Excel处理器实例
    
    Returns:
        bool: 是否处理成功
    """
    # 清理URL
    original_url = url
    url = clean_steam_url(url)
    if url != original_url:
        print(f"[提示] URL已清理: {original_url} -> {url}")
    
    # 验证URL格式
    if not validate_steam_url(url):
        logger.error("无效的Steam商店URL，请检查URL格式")
        print("❌ 错误: URL格式不正确")
        print("   正确格式: https://store.steampowered.com/app/游戏ID/")
        print("   示例: https://store.steampowered.com/app/1091500/")
        return False
    
    print(f"\n{'='*60}")
    print(f"正在处理: {url}")
    print('='*60)
    
    # 抓取数据
    game_data = scraper.scrape(url)
    
    if not game_data:
        logger.error("数据抓取失败")
        print("❌ 错误: 无法获取游戏数据，请检查网络连接或URL是否正确")
        return False
    
    # 显示抓取结果
    print("\n✓ 数据抓取成功!")
    print(f"  游戏名称: {game_data.get('name', '未知')}")
    print(f"  价格: {game_data.get('price', '未知')}")
    print(f"  评测: {game_data.get('review', '暂无评测')}")
    print(f"  标签: {game_data.get('tags', '未知')}")
    print(f"  语言: {game_data.get('languages', '未知')}")
    if game_data.get('cover_image'):
        print(f"  封面图: {game_data['cover_image']}")
    
    # 保存到Excel
    print("\n正在保存数据到Excel...")
    if excel_handler.save_game_data(game_data):
        row_count = excel_handler.get_current_row_count()
        print(f"✓ 保存成功! 当前共有 {row_count} 条记录")
        print(f"  文件位置: {excel_handler.filepath}")
        return True
    else:
        print("❌ 保存失败，请检查Excel文件是否被其他程序打开")
        return False


def main():
    """主函数"""
    print_banner()
    print_instructions()
    
    # 初始化组件
    scraper = SteamGameScraper()
    excel_handler = ExcelHandler()
    
    success_count = 0
    fail_count = 0
    
    # 主循环
    while True:
        url = get_user_input()
        
        # 用户选择退出
        if url is None:
            break
        
        # 显示帮助
        if url == 'HELP':
            continue
        
        # 跳过空输入
        if not url:
            print("⚠️  请输入有效的URL")
            continue
        
        # 处理URL
        if process_game_url(url, scraper, excel_handler):
            success_count += 1
        else:
            fail_count += 1
        
        # 显示统计
        print(f"\n{'─'*60}")
        print(f"统计: 成功 {success_count} 次 | 失败 {fail_count} 次")
        print(f"{'─'*60}")
    
    # 退出提示
    print("\n" + "="*60)
    print(f"感谢使用! 本次会话共处理 {success_count + fail_count} 个游戏")
    print(f"  成功: {success_count} | 失败: {fail_count}")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}", exc_info=True)
        print(f"\n❌ 程序发生错误: {str(e)}")
        sys.exit(1)
