# Steam游戏数据抓取工具

## 功能说明

从Steam商店页面自动抓取游戏信息并保存到Excel文件，支持：
- ✅ 游戏名称提取
- ✅ 封面图片下载并嵌入Excel
- ✅ 价格信息识别（免费/付费）
- ✅ 好评率/评测信息
- ✅ 游戏标签（前2个主要标签）
- ✅ 支持语言列表

## 环境要求

- Python 3.6+ (推荐 3.10+)
- Windows 系统

## 依赖库

```
requests>=2.31.0
beautifulsoup4>=4.12.0
openpyxl>=3.1.0
Pillow>=10.0.0
urllib3>=2.0.0
```

## 快速开始

### 方法一：双击运行（推荐）

双击 `steamData.bat`，程序会自动：
1. 检测Python环境
2. 检查并安装依赖库
3. 启动主程序

### 方法二：命令行运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行启动器
python launcher.py

# 或直接运行主程序
python main.py
```

## 使用说明

1. **输入Steam游戏URL**
   ```
   请输入Steam游戏URL (输入'q'退出, 'help'查看帮助): 
   ```
   
   示例URL：
   ```
   https://store.steampowered.com/app/1234567/GameName/
   ```

2. **自动抓取和保存**
   - 程序会自动获取游戏信息
   - 下载封面图片
   - 保存到 `steam_games.xlsx` 文件

3. **连续输入**
   - 可以持续输入多个游戏URL
   - 所有数据会追加到同一个Excel文件

4. **退出程序**
   - 输入 `q` 或 `quit` 退出

## 输出文件

- **文件名**: `steam_games.xlsx`
- **位置**: 与脚本同目录
- **格式**:
  | 列A | 列B | 列C | 列D | 列E | 列F |
  |-----|-----|-----|-----|-----|-----|
  | 封面图 | 游戏名称 | 价格 | 好评率 | 标签 | 语言 |

## 核心特性

### 1. 稳定性与容错

- ✅ **重试机制**: 网络请求超时自动重试3次，每次间隔2秒
- ✅ **图片容错**: 图片下载失败不影响文字信息保存
- ✅ **异常捕获**: HTML结构变化时不会崩溃，打印错误日志

### 2. 反爬虫对抗

- ✅ **伪装请求头**: 完整的User-Agent、Accept等Headers
- ✅ **SSL处理**: 自动处理SSL证书验证问题

### 3. 文件管理

- ✅ **绝对路径**: 基于脚本目录的绝对路径，避免环境问题
- ✅ **文件占用检查**: 检测Excel是否被打开，提示用户关闭

## 注意事项

1. **首次运行**需要联网安装依赖库
2. **Excel文件被打开时**无法保存，请先关闭Excel
3. **网络连接**需要能够访问Steam商店（可能需要科学上网）
4. **图片大小**会自动调整以适应Excel单元格
5. **代理配置**如需使用代理，请编辑 `config.py` 中的 PROXIES 配置

## 常见问题

### Q: 提示缺少依赖库怎么办？
A: 运行 `pip install -r requirements.txt` 安装所有依赖

### Q: Excel文件保存失败？
A: 检查Excel文件是否被其他程序打开，关闭后重试

### Q: 连接Steam超时怎么办？
A: Steam商店在中国大陆访问较慢，有以下几种解决方案：
   1. **使用科学上网**：确保可以访问Steam商店
   2. **配置代理**：编辑 `config.py`，取消PROXIES注释并配置代理地址
      ```python
      PROXIES = {
          'http': 'http://127.0.0.1:7890',
          'https': 'http://127.0.0.1:7890',
      }
      ```
   3. **增加超时时间**：在 `config.py` 中调整 REQUEST_TIMEOUT（默认30秒）

### Q: Steam显示HK/其他区域而不是CN？
A: 这是因为代理或网络环境导致Steam判断为其他地区。解决方法：
   1. **配置Cookie强制区域**：编辑 `config.py`，设置STORE_COUNTRY_COOKIE
      ```python
      STORE_COUNTRY_COOKIE = 'birthtime=0; lastagecheckage=1-January-1990; Steam_Language=schinese; steamCountry=CN'
      ```
   2. **更换代理节点**：选择中国大陆或亚洲节点
   3. **清除浏览器缓存**：如果使用浏览器测试，清除Cookie后重试

### Q: 某些游戏信息抓取不完整？
A: Steam页面结构可能变化，程序会尽量提取可用信息

### Q: 如何修改保存位置？
A: 编辑 `config.py` 中的 `EXCEL_FILENAME` 配置项

## 项目结构

```
tools/steamData/
├── steamData.bat       # 启动脚本
├── launcher.py         # 启动器（环境检测+依赖安装）
├── main.py             # 主程序入口
├── scraper.py          # 爬虫模块（数据抓取）
├── excel_handler.py    # Excel处理模块
├── config.py           # 配置模块
├── utils.py            # 工具模块
├── test.py             # 测试脚本
├── requirements.txt    # 依赖清单
└── README.md           # 说明文档
```

## 技术实现

- **网络请求**: requests库 + 重试装饰器
- **HTML解析**: BeautifulSoup4
- **Excel操作**: openpyxl + Pillow（图片处理）
- **日志记录**: logging模块

## 更新日志

### v1.2.0 (2026-04-25)
- 🎯 重命名启动脚本为 steamData.bat
- ✨ 优化图片保存逻辑，修复临时文件问题
- ✨ 改进HTML解析逻辑，参考成熟实现
- ✨ 增加代理支持和超时配置
- ✨ URL自动清理功能

### v1.1.0 (2026-04-25)
- ✨ 优化HTML解析逻辑，参考成熟实现
- ✨ 改进价格提取（支持免费游戏识别）
- ✨ 改进评测信息提取（增加备用方案）
- ✨ 改进标签提取（使用CSS选择器）
- ✨ 简化语言信息提取
- ✨ 优化图片处理流程
- ✨ 增加代理支持和超时配置
- ✨ URL自动清理功能

### v1.0.0 (2026-04-25)
- ✨ 初始版本发布
- ✨ 支持基本游戏信息抓取
- ✨ 支持图片嵌入Excel
- ✨ 完善的错误处理和重试机制

## 许可证

本项目仅供学习和个人使用。
