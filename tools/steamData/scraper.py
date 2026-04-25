"""
爬虫模块 - 负责从Steam商店页面抓取和解析数据
"""
import re
import logging
from bs4 import BeautifulSoup

from utils import send_request, logger

logger = logging.getLogger(__name__)


class SteamGameScraper:
    """Steam游戏数据抓取器"""
    
    def __init__(self):
        self.session = None
    
    def fetch_page(self, url):
        """
        获取Steam商店页面HTML
        
        Args:
            url: Steam商店页面URL
        
        Returns:
            str: HTML内容，失败返回None
        """
        try:
            logger.info(f"正在获取页面: {url}")
            response = send_request(url)
            response.encoding = 'utf-8'
            logger.info("页面获取成功")
            return response.text
        except Exception as e:
            logger.error(f"页面获取失败: {str(e)}")
            return None
    
    def parse_game_data(self, html, url=""):
        """
        解析游戏数据
        
        Args:
            html: HTML内容
            url: 游戏页面URL
        
        Returns:
            dict: 包含游戏信息的字典
        """
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        game_data = {
            'name': self._extract_name(soup),
            'cover_image': self._extract_cover_image(soup),
            'price': self._extract_price(soup),
            'review': self._extract_review(soup),
            'tags': self._extract_tags(soup),
            'languages': self._extract_languages(soup),
            'url': url,
        }
        
        logger.info(f"解析完成: {game_data['name']}")
        return game_data
    
    def _extract_name(self, soup):
        """提取游戏名称"""
        try:
            name_elem = soup.find('div', id='appHubAppName')
            if name_elem:
                return name_elem.get_text(strip=True)
        except Exception as e:
            logger.warning(f"提取游戏名称失败: {str(e)}")
        return '未知'
    
    def _extract_cover_image(self, soup):
        """提取封面图片URL"""
        try:
            meta_tag = soup.find('meta', property='og:image')
            if meta_tag and meta_tag.get('content'):
                return meta_tag['content']
        except Exception as e:
            logger.warning(f"提取封面图片失败: {str(e)}")
        return None
    
    def _extract_price(self, soup):
        """提取价格信息"""
        try:
            # 检查是否免费
            if soup.find('div', string=re.compile("免费开玩|Free to Play")):
                return '免费'
            
            # 尝试提取价格
            price_block = soup.find('div', class_='game_purchase_price')
            if price_block:
                return price_block.get_text(strip=True)
            
            # 另一种价格格式（折扣后价格）
            discount_price = soup.find('div', class_='discount_final_price')
            if discount_price:
                return discount_price.get_text(strip=True)
                
        except Exception as e:
            logger.warning(f"提取价格失败: {str(e)}")
        return '未知'
    
    def _extract_review(self, soup):
        """提取好评率/评测信息"""
        try:
            # 优先尝试提取百分比
            # Steam 通常显示为 "80% of the ..." 或 "特别好评 (80%)"
            review_elem = soup.find('span', class_='game_review_summary')
            if review_elem:
                text = review_elem.get_text(strip=True)
                # 尝试提取百分比数字
                import re
                match = re.search(r'(\d+)%', text)
                if match:
                    return f"{match.group(1)}%"
                return text
            
            # 备用方案
            percent_tag = soup.find(string=re.compile(r"%.*positive|positive.*%|特别好评|好评如潮", re.IGNORECASE))
            if percent_tag:
                text = percent_tag.parent.get_text(strip=True)
                match = re.search(r'(\d+)%', text)
                if match:
                    return f"{match.group(1)}%"
                return text
                
        except Exception as e:
            logger.warning(f"提取评测信息失败: {str(e)}")
        return '暂无评测'
    
    def _extract_tags(self, soup):
        """提取游戏标签（前2个），返回列表"""
        try:
            tags = []
            # 使用 CSS 选择器，排除 nofilter 类
            tag_links = soup.select('.glance_tags a:not(.nofilter)')
            for tag in tag_links[:2]:
                tag_text = tag.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            
            # 确保返回至少2个元素（不足补空）
            while len(tags) < 2:
                tags.append("")
            
            return tags
        except Exception as e:
            logger.warning(f"提取标签失败: {str(e)}")
        return ["", ""]
    
    def _extract_languages(self, soup):
        """提取支持的语言 (简化为：中文/无中文)"""
        try:
            # 查找语言区域
            lang_div = soup.find('div', class_='game_language_options')
            if lang_div:
                lang_text = lang_div.get_text(strip=True)
                # 检查是否包含中文
                if '简体中文' in lang_text or '繁体中文' in lang_text or 'Simplified Chinese' in lang_text:
                    return '中文'
                else:
                    return '无中文'
            
            return '无中文'
        except Exception as e:
            logger.warning(f"提取语言信息失败: {str(e)}")
        return '无中文'
    
    def download_image(self, image_url):
        """
        下载封面图片
        
        Args:
            image_url: 图片URL
        
        Returns:
            bytes: 图片二进制数据，失败返回None
        """
        if not image_url:
            return None
        
        try:
            logger.info(f"正在下载图片: {image_url}")
            response = send_request(image_url)
            logger.info("图片下载成功")
            return response.content
        except Exception as e:
            logger.error(f"图片下载失败: {str(e)}")
            return None
    
    def scrape(self, url):
        """
        完整的抓取流程（链接模式）
        
        Args:
            url: Steam商店页面URL
        
        Returns:
            dict: 包含游戏信息的字典，失败返回None
        """
        # 获取页面
        html = self.fetch_page(url)
        if not html:
            return None
        
        # 解析数据
        game_data = self.parse_game_data(html, url)
        if not game_data:
            return None
        
        # 链接模式：不需要下载图片，只保存 URL
        # 如果需要下载图片，取消下面的注释
        # if game_data['cover_image']:
        #     game_data['image_data'] = self.download_image(game_data['cover_image'])
        
        return game_data
