
# RLEazyTool

一些简易的便用小工具集合，提升日常开发效率。

## 目录结构

```
RLEazyTool/
├── tools/
│   └── merge_cs/
│       ├── merge_cs.py
│       ├── merge_cs.bat
│       └── merge_config.json
├── .gitignore
└── README.md
```

## 工具说明

### 1. merge_cs —— C# 代码合并工具

用于将指定目录下所有 `.cs` 文件合并为一个文本文件，便于代码查阅、归档或分享。

#### 使用方法

1. 进入 `tools/merge_cs/` 目录，双击 `merge_cs.bat`，或在命令行中运行：
   ```
   py merge_cs.py
   ```
2. 按照提示输入要合并的 C# 代码目录路径（支持绝对路径、相对路径、模糊匹配）。
3. 回车即可在桌面生成合并后的 txt 文件，文件名格式为：`<目录名>_MergedCsCode_<时间戳>.txt`。

#### 常用指令

- 输入 `ll`：列出当前路径下的所有文件夹
- 输入 `q`：退出程序
- 输入绝对路径或 `\相对路径`：切换当前目录（支持模糊匹配）
- 直接回车：执行合并操作

#### 配置文件

- `merge_config.json`：自动记录上次操作的目录，程序自动读取和更新。该文件已被 `.gitignore` 忽略，不会提交到 git。

#### 依赖环境

- Python 3.x
- Windows 系统（依赖 winreg 获取桌面路径）

## 贡献与反馈

如有建议或问题，欢迎 issue 或 PR。
