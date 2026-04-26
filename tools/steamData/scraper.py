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
        """提取基础版游戏价格信息"""
        try:
            # 检查是否免费
            if soup.find('div', string=re.compile("免费开玩|Free to Play")):
                return '免费'
            
            # 优先查找购买区域的基础价格（标准版）
            # Steam页面中，基础版价格通常在 game_area_purchase 区域内
            purchase_section = soup.find('div', id='game_area_purchase')
            if purchase_section:
                # 查找第一个购买选项（通常是基础版）
                first_purchase = purchase_section.find('div', class_='game_purchase_action')
                if first_purchase:
                    # 尝试获取折扣后的价格
                    discount_price = first_purchase.find('div', class_='discount_final_price')
                    if discount_price:
                        price_text = discount_price.get_text(strip=True)
                        logger.debug(f"提取到基础版折扣价格: {price_text}")
                        return price_text
                    
                    # 如果没有折扣，获取正常价格
                    normal_price = first_purchase.find('div', class_='game_purchase_price')
                    if normal_price:
                        price_text = normal_price.get_text(strip=True)
                        logger.debug(f"提取到基础版价格: {price_text}")
                        return price_text
            
            # 备用方案：直接查找页面上的第一个价格（可能是基础版）
            price_block = soup.find('div', class_='game_purchase_price')
            if price_block:
                price_text = price_block.get_text(strip=True)
                logger.debug(f"备用方案提取到价格: {price_text}")
                return price_text
            
            # 另一种价格格式（折扣后价格）
            discount_price = soup.find('div', class_='discount_final_price')
            if discount_price:
                price_text = discount_price.get_text(strip=True)
                logger.debug(f"备用方案提取到折扣价格: {price_text}")
                return price_text
                
        except Exception as e:
            logger.warning(f"提取价格失败: {str(e)}")
        return '未知'
    
    def _extract_review(self, soup):
        """提取好评率/评测信息"""
        try:
            import re
                
            # 方法1: 查找用户评测区域的详细统计（优先，因为这里通常有百分比）
            user_reviews = soup.find('div', id='userReviews')
            if user_reviews:
                review_text = user_reviews.get_text()
                # 尝试匹配百分比模式，如 "80% of the 1,234 user reviews..."
                match = re.search(r'(\d+)%.*?(?:positive|好评)', review_text, re.IGNORECASE)
                if match:
                    percentage = match.group(1)
                    logger.debug(f"从用户评测区提取到百分比: {percentage}%")
                    return f"{percentage}%"
                # 或者匹配 "特别好评" 等文本
                positive_match = re.search(r'(特别好评|好评如潮|褒贬不一|差评如潮|多半好评|多半差评)', review_text)
                if positive_match:
                    logger.debug(f"从用户评测区提取到评价: {positive_match.group(1)}")
                    return positive_match.group(1)
                
            # 方法2: 查找游戏评测摘要（常见位置，但可能没有百分比）
            review_elem = soup.find('span', class_='game_review_summary')
            if review_elem:
                text = review_elem.get_text(strip=True)
                logger.debug(f"找到评测摘要: {text}")
                # 尝试提取百分比数字 (例如: "80%", "95%")
                match = re.search(r'(\d+)%', text)
                if match:
                    percentage = match.group(1)
                    logger.debug(f"从评测摘要提取到百分比: {percentage}%")
                    return f"{percentage}%"
                # 如果没有百分比，返回原文（如"特别好评"、"好评如潮"等）
                if text:
                    logger.debug(f"从评测摘要提取到评价: {text}")
                    return text
                
            # 方法3: 查找任何包含百分比和positive/review的文本
            percent_tags = soup.find_all(string=re.compile(r'\d+%.*(?:positive|review|好评|评测)', re.IGNORECASE))
            for tag in percent_tags:
                text = tag.parent.get_text(strip=True)
                match = re.search(r'(\d+)%', text)
                if match:
                    percentage = match.group(1)
                    logger.debug(f"从其他位置提取到百分比: {percentage}%")
                    return f"{match.group(1)}%"
                
            # 方法4: 全局搜索页面中的评测相关信息
            page_text = soup.get_text()
            # 匹配常见的评测格式
            patterns = [
                r'(\d+)%\s*of\s*(?:the\s*)?[\d,]+\s*user\s*reviews',  # 80% of the 1,234 user reviews
                r'(\d+)%.*?(?:positive|好评)',  # 80% positive
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    if match.group(1).isdigit():
                        logger.debug(f"从页面全文提取到百分比: {match.group(1)}%")
                        return f"{match.group(1)}%"
                
            # 方法5: 最后尝试匹配中文评测总结
            chinese_patterns = [
                r'(特别好评|好评如潮|褒贬不一|差评如潮|多半好评|多半差评)',
            ]
            for pattern in chinese_patterns:
                match = re.search(pattern, page_text)
                if match:
                    logger.debug(f"从页面全文提取到评价: {match.group(1)}")
                    return match.group(1)
                
            return '暂无评测'
                    
        except Exception as e:
            logger.warning(f"提取评测信息失败: {str(e)}", exc_info=True)
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
            logger.debug("开始提取语言信息...")
            
            # 方法1: 查找语言区域（旧版Steam页面）
            lang_div = soup.find('div', class_='game_language_options')
            if lang_div:
                logger.debug("找到 game_language_options div")
                lang_text = lang_div.get_text()
                logger.debug(f"语言区域文本长度: {len(lang_text)} 字符")
                # 检查是否包含中文
                if '简体中文' in lang_text or '繁体中文' in lang_text or 'Simplified Chinese' in lang_text or 'Traditional Chinese' in lang_text:
                    logger.debug("检测到中文支持")
                    return '中文'
                else:
                    logger.debug("未检测到中文")
                    return '无中文'
            
            # 方法2: 查找新版Steam页面的语言表格
            lang_table = soup.find('table', class_='game_language_options')
            if lang_table:
                logger.debug("找到 game_language_options table")
                lang_text = lang_table.get_text()
                logger.debug(f"语言表格文本长度: {len(lang_text)} 字符")
                if '简体中文' in lang_text or '繁体中文' in lang_text or 'Simplified Chinese' in lang_text or 'Traditional Chinese' in lang_text:
                    logger.debug("检测到中文支持")
                    return '中文'
                else:
                    logger.debug("未检测到中文")
                    return '无中文'
            
            # 方法3: 通过JSON-LD或script标签查找语言信息
            scripts = soup.find_all('script', type='application/ld+json')
            logger.debug(f"找到 {len(scripts)} 个 JSON-LD script 标签")
            for script in scripts:
                if script.string:
                    import json
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            # 检查inLanguage字段
                            if 'inLanguage' in data:
                                langs = data['inLanguage']
                                logger.debug(f"JSON-LD 中的语言: {langs}")
                                if isinstance(langs, list):
                                    for lang in langs:
                                        if 'zh' in lang.lower() or 'chinese' in lang.lower():
                                            logger.debug("从 JSON-LD 检测到中文")
                                            return '中文'
                                elif isinstance(langs, str):
                                    if 'zh' in langs.lower() or 'chinese' in langs.lower():
                                        logger.debug("从 JSON-LD 检测到中文")
                                        return '中文'
                    except Exception as e:
                        logger.debug(f"解析 JSON-LD 失败: {e}")
                        pass
            
            # 方法4: 在整个页面中搜索中文关键词（备用方案）
            page_text = soup.get_text()
            logger.debug("在页面全文中搜索中文关键词...")
            if any(keyword in page_text for keyword in ['简体中文', '繁體中文', 'Simplified Chinese', 'Traditional Chinese']):
                logger.debug("从页面全文检测到中文")
                return '中文'
            
            logger.debug("未找到任何中文支持信息")
            return '无中文'
        except Exception as e:
            logger.warning(f"提取语言信息失败: {str(e)}", exc_info=True)
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
