# RLEazyTool

一些简易的便用小工具集合，提升日常开发效率。

## 📢 最新更新

- ✨ **新增**: Steam游戏数据抓取工具 (tools/steamData)
- 🔧 **steamData**: Store JSON API 优先 + HTML 补缺；HTTP Session 复用；详见子目录 README
- 🔧 **Merge 工具**: 重构为分层架构（解析 / 引擎 / 报表 / REPL），详见 [tools/merge/README.md](tools/merge/README.md)
- 🔧 **优化**: 添加虚拟环境支持 (.venv)
- 📝 **文档**: 完善使用指南和快速开始文档
- 🎯 **改进**: 优化网络请求、代理支持和错误处理

## 依赖与环境说明

### Python 版本
- Python 3.6 及以上（推荐 3.10+；当前 merge 工具在 3.10+ 下开发与测试）
- Windows 系统（部分功能依赖 Windows API）

### 虚拟环境（推荐）

项目已配置虚拟环境 `.venv`，使用虚拟环境可以：
- ✅ 隔离项目依赖，避免冲突
- ✅ 无需管理员权限安装包
- ✅ 方便分享和复现环境

**快速激活虚拟环境**：
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

详细虚拟环境设置指南请查看：[VENV_GUIDE.md](VENV_GUIDE.md)

### 核心库
- **merge 工具**: 无需第三方库，全部标准库实现
- **steamData 工具**: requests, beautifulsoup4, openpyxl, Pillow, urllib3

## 目录结构

```
RLEazyTool/
├── .venv/                      # Python 虚拟环境（已忽略）
├── tools/
│   ├── merge/                  # 代码合并工具 → 完整说明见 README.md
│   │   ├── README.md           # merge 使用与架构说明
│   │   ├── main.py             # 入口
│   │   ├── repl.py             # 交互主循环
│   │   ├── input_parser.py     # 指令解析
│   │   ├── command_handlers.py # mod / exc
│   │   ├── merge_engine.py     # 扫描与合并（无控制台输出）
│   │   ├── cs_analyzer.py      # C# 粗统计
│   │   ├── merge_report.py     # 终端汇总与写盘
│   │   ├── storage.py          # merge_config.json 读写
│   │   ├── models.py           # 配置与选项模型
│   │   ├── path_tools.py       # 路径、桌面、模糊匹配
│   │   ├── merge.bat
│   │   ├── merge_config.json   # 用户配置（通常被 .gitignore）
│   │   ├── test_merge_logic.py
│   │   └── test_path_utils.py
│   └── steamData/              # Steam 游戏数据抓取工具
│       ├── steamData.bat
│       ├── launcher.py
│       ├── main.py
│       ├── store_api.py        # Store JSON API
│       ├── scraper.py
│       ├── excel_handler.py
│       ├── config.py
│       ├── utils.py
│       ├── test_connection.py
│       ├── requirements.txt
│       └── README.md
├── .gitignore
├── README.md
└── VENV_GUIDE.md               # 虚拟环境设置指南
```

## 工具说明

### 1. merge —— 多类型代码合并工具

将指定目录下选定后缀的文件合并为一个文本文件，默认输出到桌面，并附带统计（含 `.cs` 时粗粒度 C# 结构统计）。

**典型使用场景：**
- 将大量源码合并为单文件，便于交给大模型分析或生成文档。
- 快速打包分享、归档与查阅。

#### 快速开始

1. 进入 `tools/merge/`，双击 **`merge.bat`**，或执行：`py main.py`
2. 按提示切换目录（绝对路径、`\\` 相对路径、历史记录 `1`–`9` 等），**回车**执行合并。
3. 桌面上生成：`<目录名>_MergedFiles_<时间戳>.txt`

若在 Windows 默认控制台遇到 emoji 编码报错，可先设置：`PYTHONIOENCODING=utf-8`。

**更完整的指令表、模块说明与测试方式**见：📖 **[tools/merge/README.md](tools/merge/README.md)**

#### 指令摘要

| 类别 | 指令 |
|------|------|
| 基础 | `help`、`q`、`m`、`1`–`9`、`ll`、`r`、回车合并 |
| 范围 | `this` — 切换「仅当前目录」/「含子文件夹」 |
| 路径 | 绝对路径；`\\` 或 `/` 开头的相对路径（支持末级文件夹模糊匹配） |
| 类型组 | `mod a` / `mod u` / `mod ll` / `mod ll now` / `mod d` |
| 排除 | `exc a` / `exc u` / `exc q` / `exc ll` / `exc d` / `exc case` / 单独 `exc`（恢复上次成功合并时的排除组） |

#### 配置文件 `merge_config.json`

记录历史路径（最多 9 条）、类型组、当前 mod、排除组、是否包含子目录、上次成功合并时的 mod/排除组等；通常已被 `.gitignore` 忽略。结构示例：

```json
{
  "history": ["D:/project/src"],
  "type_groups": {
    "default": [".cs"],
    "web": [".cs", ".tsx"]
  },
  "current_type_group": "default",
  "last_success_type_group": "default",
  "exclude_groups": {},
  "current_exclude_group": null,
  "last_success_exclude_group": null,
  "merge_subfolders": true
}
```

#### 统计说明

合并结果文件头部与控制台会输出各类型文件数、行数；对 `.cs` 还会输出类/结构体/枚举/接口及方法、字段等**粗粒度**统计（基于正则，复杂语法可能有偏差，仅供参考）。

#### 性能说明

当前为整体读入后再写出，体量极大时内存占用会升高，可分批目录或使用「仅本层」模式（`this`）控制范围。

单元测试：`tools/merge/test_merge_logic.py`、`test_path_utils.py`。

---

### 2. steamData —— Steam 游戏数据抓取工具

从商店页抓取信息并写入 `steam_games.xlsx`；**默认走 Steam Store 公开 JSON API**，不足时自动用 HTML 解析补齐。网络与 Excel 等可通过 **终端配置**（`steamdata_config.json`，类 merge 工具）调整，详见 [tools/steamData/README.md](tools/steamData/README.md)。

**功能概要：**
- 名称、国区价格/免费、`appreviews` 评测摘要、类型标签、中文支持、封面内嵌 Excel
- `requests.Session` 复用、可配置重试与 `STEAMDATA_LOG=DEBUG`
- 直连（虚拟网卡加速）、自动探测本机代理，或终端 `proxy` / `config.PROXIES` 手动代理
- **终端配置**：`python launcher.py config`、主界面输入 `config`、或双击 `steamData_config.bat`

#### 使用方法

**方法一：双击运行（推荐）**
```bash
cd tools\steamData
双击 steamData.bat
# 仅调网络/代理/Excel 等：双击 steamData_config.bat
```

**方法二：命令行运行**
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
cd tools\steamData
pip install -r requirements.txt

# 运行启动器
python launcher.py

# 或仅打开终端配置（写入 steamdata_config.json）
python launcher.py config

# 或直接运行主程序
python main.py
```

**输入示例：**
```
请输入Steam游戏URL: https://store.steampowered.com/app/1091500/
```

#### 输出文件

- **文件名**: `steam_games.xlsx`
- **位置**: `tools/steamData/` 目录
- **格式**:
  | 列A | 列B | 列C | 列D | 列E | 列F | 列G | 列H |
  |-----|-----|-----|-----|-----|-----|-----|-----|
  | 封面图 | 游戏名 | 价格 | 好评率 | 标签1 | 标签2 | 商店链接 | 语言 |

#### 核心特性

**稳定性与容错**
- 多策略连接：**默认先走本机 HTTP 代理**（系统代理 / 环境变量 / 7890 等常见端口），再直连；仅虚拟网卡可改用 `direct_first`
- 单次策略内失败自动重试（指数退避）
- API + HTML 双通道，页面改版时较易恢复

**反爬虫对抗**
- 完整的浏览器请求头伪装
- SSL证书验证问题自动处理

**文件管理**
- 基于脚本目录的绝对路径
- Excel文件占用检测，提示用户关闭

#### 文档

- 完整说明: [tools/steamData/README.md](tools/steamData/README.md)

## 贡献与反馈

如有建议或问题，欢迎 issue 或 PR。
如有新平台适配、单元测试补充、性能优化建议，欢迎贡献！

## 📚 相关文档

- [虚拟环境设置指南](VENV_GUIDE.md) - 详细的虚拟环境配置说明
- [merge 工具说明](tools/merge/README.md) - 代码合并工具（指令、架构、测试）
- [steamData 工具说明](tools/steamData/README.md) - Steam 数据抓取（API + Excel）
