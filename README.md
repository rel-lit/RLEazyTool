# RLEazyTool

一些简易的便用小工具集合，提升日常开发效率。

## 📢 最新更新

- ✨ **新增**: Steam游戏数据抓取工具 (tools/steamData)
- 🔧 **优化**: 添加虚拟环境支持 (.venv)
- 📝 **文档**: 完善使用指南和快速开始文档

## 依赖与环境说明

### Python 版本
- Python 3.6 及以上（推荐 3.10+）
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
- **merge工具**: 无需第三方库，全部标准库实现
- **steamData工具**: requests, beautifulsoup4, openpyxl, Pillow, urllib3

## 目录结构

```
RLEazyTool/
├── .venv/                      # Python虚拟环境（已忽略）
├── tools/
│   ├── merge/                  # 代码合并工具
│   │   ├── main.py
│   │   ├── config_manager.py
│   │   ├── path_utils.py
│   │   ├── merge_logic.py
│   │   ├── utils.py
│   │   ├── cli.py
│   │   ├── __init__.py
│   │   ├── merge.bat
│   │   ├── merge_config.json
│   │   ├── test_merge_logic.py
│   │   └── test_path_utils.py
│   └── steamData/              # Steam游戏数据抓取工具
│       ├── launcher.py         # 启动器
│       ├── main.py
│       ├── scraper.py
│       ├── excel_handler.py
│       ├── config.py
│       ├── utils.py
│       ├── test.py
│       ├── run.bat
│       ├── requirements.txt
│       └── README.md
├── .gitignore
├── README.md
└── VENV_GUIDE.md               # 虚拟环境设置指南
```

## 工具说明

### 1. merge —— 多类型代码合并工具

用于将指定目录下所有指定类型（如 `.cs`、`.txt` 等）文件合并为一个文本文件，便于代码查阅、归档或分享。

**典型使用场景：**
- 将大量 C# 源码或其它类型文件合并为单个文件，方便上传给 Web AI（如大模型代码分析、自动文档生成等）。
- 快速打包项目代码，一键分享给同事或好友，无需逐个文件整理。
- 归档、备份、代码查阅等其它批量处理场景。

#### 使用方法

1. 进入 `tools/merge/` 目录，双击 `merge.bat`，或在命令行中运行：
   ```
   py main.py
   ```
   > Linux/Mac 下请用 `python3 main.py`，桌面路径自动适配。
2. 按照提示输入要合并的代码目录路径（支持绝对路径、相对路径、模糊匹配）。
3. 回车即可在桌面生成合并后的 txt 文件，文件名格式为：`<目录名>_MergedFiles_<时间戳>.txt`。

#### 常用指令

- 输入 `help`：显示所有指令及说明
- 输入 `m`：显示历史记忆的路径列表（最多9条）
- 输入 `1-9`：直接切换到对应历史路径
- 输入 `ll`：列出当前路径下的所有文件夹
- 输入 `q`：退出程序
- 输入 `r`：进入持续合并模式（每次回车合并，q 退出循环）
- 输入绝对路径或 `\相对路径`：切换当前目录（支持模糊匹配，未找到时自动修正为最相近文件夹）
- 直接回车：执行合并操作

- `mod a <组名> <.cs> <.txt> ...`：新增类型组
- `mod u <组名>`：切换当前类型组
- `mod ll`：列出所有类型组
- `mod d <组名>`：删除类型组（默认组不可删）
- `mod ll now`：显示当前类型组

- `exc a <组名> <词1> <词2> ...`：新增排除组（默认区分大小写）
- `exc d <组名>`：删除排除组
- `exc u <组名>`：切换当前排除组（仅此时启用）
- `exc q`：退出排除模式
- `exc ll`：列出所有排除组
- `exc case <组名> <on|off>`：设置组是否区分大小写
- `exc`：启用上次合并成功时的排除组

#### 类型组与多类型合并

- 支持自定义类型组，合并时可选择不同类型组（如只合并 .cs，或同时合并 .cs/.txt/.json 等）。
- 类型组相关指令：
  - `mod a <组名> <.cs> <.txt> ...`：新增类型组
  - `mod u <组名>`：切换当前类型组
  - `mod ll`：列出所有类型组
  - `mod d <组名>`：删除类型组（默认组不可删）
  - `mod ll now`：显示当前类型组

#### 路径切换与模糊匹配

- 支持输入绝对路径或 `\相对路径` 切换目录。
- 支持模糊匹配最后一级文件夹名，未找到时自动修正为最相近的文件夹。
- 多次路径切换有趣味提示。

#### 配置文件

- `merge_config.json`：自动记录最近9次合并成功的目录、类型组、当前类型组等信息，程序自动读取和更新。该文件已被 `.gitignore` 忽略，不会提交到 git。
- 配置结构示例：
  ```json
  {
    "history": ["D:/xxx", ...],
    "type_groups": {"default": [".cs"], "all": [".cs", ".txt"]},
    "current_type_group": "default",
    "last_success_type_group": "default"
  }
  ```

#### 统计信息

合并完成后，工具会自动统计并输出如下信息（在合并结果文件头部和控制台均可见）：

- 合并的各类型文件总数
- 合并后的总行数
- 类（class）数、结构体（struct）数、枚举（enum）数、接口（interface）数
- 变量/字段/属性数、方法数
- 平均类长度、最大/最小类长度、平均每类方法/字段数、枚举成员数、结构体字段数、接口方法数等
- 读取失败文件数

> ⚠️ 统计 C# 结构信息基于正则表达式，仅供参考。极端复杂/嵌套/特殊语法下可能有误判，建议人工复核。

#### 性能说明

- 当前实现为全量内存合并，极大目录下可能内存占用较高。建议分批处理或流式合并。
- 单元测试见 test_merge_logic.py、test_path_utils.py。

---

### 2. steamData —— Steam游戏数据抓取工具

从Steam商店页面自动抓取游戏信息并保存到Excel文件，支持图片嵌入。

**功能特性：**
- ✅ 游戏名称、价格、好评率提取
- ✅ 封面图片下载并嵌入Excel
- ✅ 游戏标签和支持语言识别
- ✅ 自动重试机制和异常处理
- ✅ 文件占用检测

**典型使用场景：**
- 批量收集Steam游戏信息建立数据库
- 跟踪游戏价格变化
- 分析游戏评测和标签数据
- 制作个人游戏收藏清单

#### 使用方法

**方法一：使用批处理文件（推荐）**
```bash
cd tools\steamData
双击 run.bat
```

**方法二：命令行运行**
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
cd tools\steamData
pip install -r requirements.txt

# 运行程序
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
  | 列A | 列B | 列C | 列D | 列E | 列F |
  |-----|-----|-----|-----|-----|-----|
  | 封面图 | 游戏名称 | 价格 | 好评率 | 标签 | 语言 |

#### 核心特性

**稳定性与容错**
- 网络请求超时自动重试3次，每次间隔2秒
- 图片下载失败不影响文字信息保存
- HTML结构变化时不会崩溃，打印错误日志

**反爬虫对抗**
- 完整的浏览器请求头伪装
- SSL证书验证问题自动处理

**文件管理**
- 基于脚本目录的绝对路径
- Excel文件占用检测，提示用户关闭

#### 文档

- 📖 完整文档: [tools/steamData/README.md](tools/steamData/README.md)
- 🚀 快速开始: [tools/steamData/QUICKSTART.md](tools/steamData/QUICKSTART.md)

## 贡献与反馈

如有建议或问题，欢迎 issue 或 PR。
如有新平台适配、单元测试补充、性能优化建议，欢迎贡献！

## 📚 相关文档

- [虚拟环境设置指南](VENV_GUIDE.md) - 详细的虚拟环境配置说明
- [merge工具文档](tools/merge/) - 代码合并工具详细说明
- [steamData工具文档](tools/steamData/README.md) - Steam数据抓取工具详细说明
- [steamData快速开始](tools/steamData/QUICKSTART.md) - 5分钟上手指南
