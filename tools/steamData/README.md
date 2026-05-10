# Steam游戏数据抓取工具

## 功能说明

从 Steam 商店自动抓取游戏信息并保存到 Excel，默认采用 **Steam Store 公开 JSON API**（`appdetails` + `appreviews` 摘要），在数据不全或对特殊页面时再 **回退并合并 HTML 解析**，比纯爬虫更抗页面改版。

支持能力：
- ✅ 游戏名称、国区价格（`cc`/`l` 可配置）、是否免费
- ✅ 评测摘要（Steam 评价词或大致好评占比）
- ✅ 类型标签（来自 API 的 genres，至多 2 个）
- ✅ 是否支持中文界面语言
- ✅ 封面图下载并嵌入 Excel（与主程序**同一套**重试与 Session）
- ✅ 直连虚拟网卡加速器或手动 HTTP 代理（`config.PROXIES`）

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

# 仅打开终端配置（与 merge 工具类似：改完即写入 JSON）
python launcher.py config
python main.py config
python config_repl.py

# 或双击 steamData_config.bat
```

## 终端配置（类 merge 工具）

除直接改 `config.py` 外，可用**交互式终端**修改网络、API、Excel 等；每次有效修改会**重置 HTTP Session** 并写入同目录下的 **`steamdata_config.json`**（已加入 `.gitignore`，不参与版本库）。启动时自动合并该 JSON 覆盖默认值。

**进入方式（任选其一）：**

| 方式 | 说明 |
|------|------|
| 主程序内输入 `config` / `cfg` / `settings` | 不退出抓取流程，配完返回 URL 输入 |
| `python launcher.py config`（或 `--config` / `-c`） | 经启动器检查环境与依赖后进入 |
| `python main.py config`（或 `--config` / `-c`） | 直接进入配置，不跑抓取横幅循环 |
| `python config_repl.py` | 同上 |
| 双击 `steamData_config.bat` | 调用 `launcher.py config` |

**常用命令（完整列表在配置里输入 `help`）：**

- `ll` / `now`：打印当前可持久化项
- `reload`：从磁盘重新加载 JSON
- `reset`：删除 `steamdata_config.json` 并恢复代码默认值（需确认 `y`）
- `strategy proxy_first|direct_first|proxy_only|direct_only`
- `proxy off` 或 `proxy http://127.0.0.1:7890`
- `connect` / `read`（秒）、`retries`、`delay`、`verify on|off`
- `api on|off`、`lang`、`cc`
- `excel <文件名>`、`cookie default|off|...`、`reqto`、`rowh`、`imgcol`

**持久化键名（与 JSON 字段一致）：**  
`CONNECTION_STRATEGY`, `PROXIES`, `CONNECT_TIMEOUT`, `READ_TIMEOUT`, `VERIFY_SSL`, `USE_STORE_API`, `STEAM_API_LANGUAGE`, `STEAM_API_CC`, `MAX_RETRIES`, `RETRY_DELAY`, `REQUEST_TIMEOUT`, `EXCEL_FILENAME`, `STORE_COUNTRY_COOKIE`, `DEFAULT_ROW_HEIGHT`, `IMAGE_COLUMN_WIDTH`

> **注意**：在主会话中修改 `excel` 后，当前已打开的 `ExcelHandler` 仍指向旧路径；**建议改完配置后退出并重新启动主程序**，或仅在进入抓取前完成 Excel 文件名调整。

## 使用说明

1. **输入Steam游戏URL**
   ```
   请输入Steam游戏URL (q退出 help帮助 config配置): 
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
  | 列A | 列B | 列C | 列D | 列E | 列F | 列G | 列H |
  |-----|-----|-----|-----|-----|-----|-----|-----|
  | 封面图片 | 游戏名 | 价格 | 好评率 | 标签1 | 标签2 | 商店链接 | 语言 |

## 核心特性

### 1. 稳定性与容错

- ✅ **重试机制**: 请求失败按配置指数退避重试（默认 `MAX_RETRIES` 见 `config.py` / 终端 `retries`）
- ✅ **双通道数据**: API 优先，缺字段时再拉 HTML 补缺
- ✅ **连接复用**: `requests.Session` 进程内复用，减少握手开销
- ✅ **图片容错**: 封面下载失败不影响文字写入
- ✅ **调试日志**: 设置环境变量 `STEAMDATA_LOG=DEBUG` 可查看详细请求日志

### 2. 反爬虫对抗

- ✅ **伪装请求头**: 完整的User-Agent、Accept等Headers
- ✅ **SSL处理**: 自动处理SSL证书验证问题

### 3. 文件管理

- ✅ **绝对路径**: 基于脚本目录的绝对路径，避免环境问题
- ✅ **文件占用检查**: 检测Excel是否被打开，提示用户关闭

## 注意事项

1. **首次运行**需要联网安装依赖库
2. **Excel文件被打开时**无法保存，请先关闭Excel
3. **网络连接**：默认 **`proxy_first`**（先尝试系统/环境代理与本机 **7890** 等 Clash 端口，再直连）；仅 UU 虚拟网卡、无 HTTP 代理时用 **`direct_first`**
4. **封面图片** A 列嵌入游戏封面图片，自动调整大小保持一致
5. **手动代理**：终端 `proxy` 或 `config.PROXIES`
6. **关闭 API**: 终端 `api off` 或 `USE_STORE_API = False`（纯 HTML）

## 连接策略（`config.py`）

| 配置项 | 含义 |
|--------|------|
| `CONNECTION_STRATEGY` | `proxy_first`（默认） / `direct_first` / `proxy_only` / `direct_only` |
| `CONNECT_TIMEOUT` / `READ_TIMEOUT` | 连接与读取超时拆分 |
| `VERIFY_SSL` | 默认 `False`；走部分代理时需保持 False |

`proxy_only` 且未配置也未探测到代理时，会**立即报错提示**，避免误以为在爬数据。

## 常见问题

### Q: 提示缺少依赖库怎么办？
A: 运行 `pip install -r requirements.txt` 安装所有依赖

### Q: Excel文件保存失败？
A: 检查Excel文件是否被其他程序打开，关闭后重试

### Q: 连接 Steam 超时、`RemoteDisconnected`？

1. **Clash / V2 等**：确认 HTTP 端口（如 **7890**）已开；程序默认 **proxy_first** 会自动走本机代理。
2. 仍失败：在 `config.py` 设置 `PROXIES`。
3. **只有 UU、无 HTTP 代理**：`CONNECTION_STRATEGY = "direct_first"`。
4. 增大 `READ_TIMEOUT`。详见上文「连接策略」表。

### Q: 价格/语言不是国区？
A: 检查 `config.py` 中 `STEAM_API_CC`、`STEAM_API_LANGUAGE` 与 `STORE_COUNTRY_COOKIE`；必要时更换代理节点。

### Q: 某些游戏信息抓取不完整？
A: Steam页面结构可能变化，程序会尽量提取可用信息

### Q: 如何修改保存位置？
A: 终端配置里执行 `excel 新文件名.xlsx`，或编辑 `config.py` 中的 `EXCEL_FILENAME`；**改后建议重启主程序**以便 Excel 模块使用新路径。

## 项目结构

```
tools/steamData/
├── steamData.bat       # 启动脚本
├── steamData_config.bat # 仅打开终端配置
├── launcher.py         # 启动器（虚拟环境 + 依赖）；`config` 参数进配置 REPL
├── main.py             # 交互主程序；`config` 参数或循环内 `config` 进配置 REPL
├── config_repl.py      # 终端配置（写入 steamdata_config.json）
├── settings_store.py   # JSON 持久化与 `PERSIST_KEYS`
├── store_api.py        # Steam Store JSON API（appdetails / 评测摘要）
├── scraper.py          # HTML 解析与 API 结果合并
├── excel_handler.py    # Excel 与内嵌封面
├── config.py           # 请求头、API 开关、代理、超时
├── utils.py            # Session、重试、代理探测、URL 校验
├── test_connection.py  # 网络连通性诊断
├── check_uu.py         # 虚拟网卡 / DNS 简单检测
├── requirements.txt
└── README.md
```

## 技术实现

- **数据**: Store `appdetails` + `appreviews?filter=summary`，必要时 BeautifulSoup 补全
- **网络**: 多策略连接（`proxy_first` 等）+ Session；分拆连接/读超时；各策略内重试
- **Excel**: openpyxl + Pillow；表头样式使用 `Font`/`Alignment`
- **日志**: 标准 `logging`，`STEAMDATA_LOG` 控制级别

### v1.7.0 (2026-05-10)
- ✨ **终端配置**：`config_repl` + `steamdata_config.json`（行为对齐 merge 的 JSON 覆盖）
- ✨ `launcher.py` / `main.py` 支持 `config`、`--config`、`-c`；主循环内 `config` / `cfg` / `settings`
- ✨ `steamData_config.bat`；`.gitignore` 与仓库根目录说明同步忽略用户 JSON

### v1.6.0 (2026-05-10)
- 🔧 **修复国内长期连接失败**：默认代理优先（含本机 7890 等端口），不再在探测到代理后仍强制直连
- 🔧 连接/读取超时拆分；`trust_env=False` 与显式代理链避免混乱
- 🔧 请求头去掉 `br` 编码，减少解码异常

### v1.5.0 (2026-05-10)
- ✨ 默认启用 Store JSON API + HTML 补缺合并
- ✨ 进程内 HTTP Session 复用；封面下载与页面请求策略统一
- ✨ Excel 表头样式修复；封面下载走 `download_bytes`
- 📝 更新配置项说明（`USE_STORE_API`、`STEAM_API_*`）

### v1.4.0 (2026-04-26)
- 🎯 改回图片嵌入模式，在Excel中直接显示游戏封面图片
- ✨ 图片完全贴合单元格尺寸（300x100像素）
- ✨ 固定列宽42字符（300像素），行高75pt（100像素）
- ✨ 所有单元格文字垂直居中对齐

### v1.3.0 (2026-04-25)
- 🎯 改为链接模式，保存图片URL而非嵌入图片
- ✨ 精简代码，删除图片处理相关逻辑
- ✨ 优化表格布局，增加更多列
- ✨ 更新文档说明

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
