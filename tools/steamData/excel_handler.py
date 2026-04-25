"""
Excel处理模块 - 负责将游戏数据保存到Excel文件，并嵌入图片
"""
import os
import io
import logging
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl import styles
from PIL import Image as PILImage

from utils import get_excel_path, is_file_open, logger
from config import DEFAULT_ROW_HEIGHT, IMAGE_COLUMN_WIDTH

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Excel文件处理器"""
    
    def __init__(self):
        self.filepath = get_excel_path()
        self.workbook = None
        self.sheet = None
    
    def _create_new_workbook(self):
        """创建新的工作簿并初始化表头"""
        self.workbook = Workbook()
        self.sheet = self.workbook.active
        self.sheet.title = 'Steam游戏数据'
        
        # 设置表头 - 按照图片格式
        headers = [
            '图片', '游戏名', '价格', '好评率', 
            '标签', '标签',  # E, F 列
            '商店链接', '语言', 
            '评分员1', '短评', '分数',  # I, J, K
            '评分员2', '短评', '分数',  # L, M, N
            '评分员3', '短评', '分数',  # O, P, Q
            '评分员4', '短评', '分数',  # R, S, T
            '平均分'  # U
        ]
        self.sheet.append(headers)
        
        # 设置列宽
        self.sheet.column_dimensions['A'].width = 15  # 图片
        self.sheet.column_dimensions['B'].width = 30  # 游戏名
        self.sheet.column_dimensions['C'].width = 10  # 价格
        self.sheet.column_dimensions['D'].width = 12  # 好评率
        self.sheet.column_dimensions['E'].width = 10  # 标签1
        self.sheet.column_dimensions['F'].width = 10  # 标签2
        self.sheet.column_dimensions['G'].width = 15  # 链接
        self.sheet.column_dimensions['H'].width = 10  # 语言
        # 评分员相关列宽
        for col in ['I', 'L', 'O', 'R']:
            self.sheet.column_dimensions[col].width = 12
        for col in ['J', 'M', 'P', 'S']:
            self.sheet.column_dimensions[col].width = 25
        for col in ['K', 'N', 'Q', 'T']:
            self.sheet.column_dimensions[col].width = 8
        self.sheet.column_dimensions['U'].width = 10  # 平均分
        
        # 设置表头样式（加粗）
        for cell in self.sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.alignment = styles.Alignment(horizontal='center', vertical='center')
        
        logger.info("创建新的Excel工作簿")
    
    def _load_existing_workbook(self):
        """加载已存在的工作簿"""
        try:
            self.workbook = load_workbook(self.filepath)
            self.sheet = self.workbook.active
            logger.info("加载现有Excel文件")
        except Exception as e:
            logger.warning(f"加载Excel文件失败，将创建新文件: {str(e)}")
            self._create_new_workbook()
    
    def _check_file_availability(self):
        """
        检查文件是否可用（未被其他程序打开）
        
        Returns:
            bool: 文件是否可用
        """
        if os.path.exists(self.filepath):
            if is_file_open(self.filepath):
                logger.error(f"Excel文件已被打开，请先关闭文件: {self.filepath}")
                return False
        return True
    
    def _add_game_row(self, game_data):
        """
        添加一行游戏数据
        
        Args:
            game_data: 游戏数据字典
        
        Returns:
            int: 新行的行号
        """
        # 处理标签，确保有两个
        tags = game_data.get('tags', [])
        tag1 = tags[0] if len(tags) > 0 else ''
        tag2 = tags[1] if len(tags) > 1 else ''
        
        row_data = [
            '',  # A: 图片占位
            game_data.get('name', '未知'),  # B: 游戏名
            game_data.get('price', '未知'),  # C: 价格
            game_data.get('review', '暂无评测'),  # D: 好评率
            tag1,  # E: 标签 1
            tag2,  # F: 标签 2
            game_data.get('url', ''),  # G: 商店链接
            game_data.get('languages', '未知'),  # H: 语言
            '', '', '',  # I, J, K: 评分员 1
            '', '', '',  # L, M, N: 评分员 2
            '', '', '',  # O, P, Q: 评分员 3
            '', '', '',  # R, S, T: 评分员 4
            ''  # U: 平均分
        ]
        
        self.sheet.append(row_data)
        row_num = self.sheet.max_row
        logger.info(f"添加游戏数据到第{row_num}行: {game_data.get('name')}")
        return row_num
    
    def _insert_image(self, image_data, row_num):
        """
        在指定行插入图片
        
        Args:
            image_data: 图片二进制数据
            row_num: 行号
        """
        if not image_data:
            logger.warning("图片数据为空，跳过图片插入")
            return
        
        temp_image_path = None
        try:
            # 创建临时文件夹
            temp_folder = os.path.join(os.path.dirname(self.filepath), 'temp_images')
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
            
            # 保存为临时文件
            temp_image_path = os.path.join(temp_folder, f"temp_{row_num}.jpg")
            with open(temp_image_path, 'wb') as f:
                f.write(image_data)
            
            # 创建openpyxl图片对象
            img = OpenpyxlImage(temp_image_path)
            
            # 调整图片大小
            img.width = 120
            img.height = 180
            
            # 添加图片到工作表
            cell_position = f'A{row_num}'
            self.sheet.add_image(img, cell_position)
            
            # 调整行高
            self.sheet.row_dimensions[row_num].height = 140
            
            logger.info(f"图片插入成功: 第{row_num}行")
            
        except Exception as e:
            logger.error(f"图片插入失败 (将跳过图片，只保存文字): {str(e)}")
            # 如果出错，立即清理临时文件
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            raise  # 重新抛出异常
    
    def save_game_data(self, game_data):
        """
        保存游戏数据到Excel
        
        Args:
            game_data: 游戏数据字典（包含image_data字段）
        
        Returns:
            bool: 是否保存成功
        """
        # 检查文件可用性
        if not self._check_file_availability():
            return False
        
        # 加载或创建工作簿
        if os.path.exists(self.filepath):
            self._load_existing_workbook()
        else:
            self._create_new_workbook()
        
        temp_image_paths = []  # 记录所有临时图片路径
        
        try:
            # 添加数据行
            row_num = self._add_game_row(game_data)
            
            # 插入图片
            if game_data.get('image_data'):
                try:
                    self._insert_image_to_sheet(game_data['image_data'], row_num, temp_image_paths)
                except Exception as e:
                    logger.warning(f"图片插入失败，将只保存文字: {str(e)}")
            
            # 保存文件（此时图片文件必须存在）
            self.workbook.save(self.filepath)
            logger.info(f"数据保存成功: {self.filepath}")
            
            # 保存成功后才清理临时文件
            for temp_path in temp_image_paths:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
            return True
            
        except Exception as e:
            logger.error(f"保存Excel文件失败: {str(e)}")
            # 出错时也要清理临时文件
            for temp_path in temp_image_paths:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            return False
    
    def _insert_image_to_sheet(self, image_data, row_num, temp_paths_list):
        """
        在指定行插入图片（内部方法）
        
        Args:
            image_data: 图片二进制数据
            row_num: 行号
            temp_paths_list: 用于记录临时文件路径的列表
        """
        if not image_data:
            return
        
        # 创建临时文件夹
        temp_folder = os.path.join(os.path.dirname(self.filepath), 'temp_images')
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        
        # 保存为临时文件
        temp_image_path = os.path.join(temp_folder, f"temp_{row_num}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)
        
        # 记录临时文件路径（稍后清理）
        temp_paths_list.append(temp_image_path)
        
        try:
            # 使用PIL读取图片获取原始尺寸
            from PIL import Image as PILImage
            pil_img = PILImage.open(temp_image_path)
            original_width, original_height = pil_img.size
            
            # 计算缩放比例，保持宽高比
            # A列宽度为40（约280像素），行高140（约187像素）
            target_width = 260  # 目标宽度（像素）
            target_height = 130  # 目标高度（像素）
            
            # 计算缩放比例
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            scale = min(width_ratio, height_ratio)  # 使用较小的比例，确保不超出
            
            # 计算最终尺寸
            final_width = int(original_width * scale)
            final_height = int(original_height * scale)
            
            # 创建openpyxl图片对象
            img = OpenpyxlImage(temp_image_path)
            img.width = final_width
            img.height = final_height
            
            # 设置图片为嵌入单元格（随单元格移动和调整大小）
            # openpyxl 中通过修改图片对象的 editAs 属性实现
            img.editAs = 'oneCell'
            
            # 添加图片到工作表
            self.sheet.add_image(img, f'A{row_num}')
            
            # 调整行高以适应图片（像素转Excel单位，1像素≈0.75 Excel单位）
            self.sheet.row_dimensions[row_num].height = final_height * 0.75 + 10  # 加10留边距
            
            logger.info(f"图片插入成功: 第{row_num}行 (尺寸: {final_width}x{final_height})")
            
        except Exception as e:
            logger.warning(f"图片处理失败，使用默认尺寸: {str(e)}")
            # 降级方案：使用固定尺寸
            img = OpenpyxlImage(temp_image_path)
            img.width = 120
            img.height = 180
            img.anchor = f'A{row_num}'
            img.editAs = 'oneCell'  # 同样设置为嵌入单元格
            self.sheet.add_image(img)
            self.sheet.row_dimensions[row_num].height = 140
    
    def get_current_row_count(self):
        """
        获取当前数据行数（不包括表头）
        
        Returns:
            int: 数据行数
        """
        if os.path.exists(self.filepath):
            try:
                wb = load_workbook(self.filepath)
                ws = wb.active
                return max(0, ws.max_row - 1)  # 减去表头
            except:
                return 0
        return 0
