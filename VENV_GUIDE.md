# 虚拟环境设置指南

## 📋 什么是虚拟环境？

虚拟环境是一个独立的Python环境，可以为每个项目隔离依赖包，避免不同项目之间的依赖冲突。

## 🚀 快速设置（已完成）

项目根目录已创建 `.venv` 虚拟环境，你只需要：

### Windows系统

1. **激活虚拟环境**：
   ```bash
   # 在项目根目录运行
   .venv\Scripts\activate
   ```

2. **merge 工具**：日常使用仅需标准库；若需 **`.gitignore` 兼容**，请安装可选依赖：

   ```bash
   pip install -r tools/merge/requirements.txt
   ```

   若日后为其它子项目安装包：
   ```bash
   .venv\Scripts\activate
   pip install <包名>
   ```

3. **运行 merge（示例）**：
   ```bash
   cd tools\merge
   py main.py
   ```

4. **退出虚拟环境**：
   ```bash
   deactivate
   ```

### 使用批处理文件（merge）

在 `tools\merge\` 下双击 **`merge.bat`**，或在项目根目录激活 `.venv` 后运行 `py tools\merge\main.py`。

## 🔧 手动创建虚拟环境（如需重新创建）

如果虚拟环境损坏或需要重新创建：

### 1. 删除旧环境
```bash
# Windows
rmdir /s .venv

# Linux/Mac
rm -rf .venv
```

### 2. 创建新环境
```bash
# 使用Python 3.10+（推荐）
python -m venv .venv
```

### 3. 激活环境
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 4. 验证环境
```bash
# 查看Python路径（应该指向.venv目录）
where python    # Windows
which python    # Linux/Mac

# 查看pip路径
where pip       # Windows
which pip       # Linux/Mac
```

### 5. （可选）为子项目安装第三方依赖

当前仓库中的 **merge** 核心功能仅使用标准库；启用 `exc gitignore on` 前需 `pip install -r tools/merge/requirements.txt`（`pathspec`）。其它子工具若需第三方库，在已激活的 `.venv` 中安装即可。

## 📦 依赖管理

### 查看所有已安装的包
```bash
pip list
```

### 导出当前环境的依赖
```bash
pip freeze > requirements.txt
```

### 从requirements.txt安装
```bash
pip install -r requirements.txt
```

## ❓ 常见问题

### Q1: 如何确认虚拟环境已激活？

**Windows**: 命令行前会显示 `(.venv)`
```
(.venv) D:\WorkTool\RLEazyTool>
```

**检查Python路径**:
```bash
where python
# 应该显示: D:\WorkTool\RLEazyTool\.venv\Scripts\python.exe
```

### Q2: 虚拟环境和系统Python有什么区别？

| 特性 | 虚拟环境 | 系统Python |
|------|---------|-----------|
| 依赖隔离 | ✅ 独立 | ❌ 全局共享 |
| 权限要求 | ✅ 无需管理员 | ⚠️ 可能需要 |
| 版本冲突 | ✅ 不会冲突 | ❌ 可能冲突 |
| 清理方便 | ✅ 删除文件夹即可 | ⚠️ 需要逐个卸载 |

### Q3: 为什么推荐使用虚拟环境？

1. **依赖隔离**: 不同项目可以使用不同版本的库
2. **避免冲突**: 不会影响系统Python或其他项目
3. **便于分享**: 通过requirements.txt轻松复现环境
4. **干净卸载**: 删除.venv文件夹即可完全清除

### Q4: IDE如何配置虚拟环境？

**VS Code**:
1. 按 `Ctrl+Shift+P`
2. 输入 "Python: Select Interpreter"
3. 选择 `.venv\Scripts\python.exe`

**PyCharm**:
1. File → Settings → Project → Python Interpreter
2. 点击齿轮图标 → Add
3. 选择 "Existing Environment"
4. 浏览到 `.venv\Scripts\python.exe`

### Q5: 虚拟环境占用多少空间？

通常 50-200MB，取决于安装的包数量。本项目约 100MB。

## 🎯 最佳实践

1. ✅ **始终使用虚拟环境**进行项目开发
2. ✅ **定期更新**依赖包（注意兼容性）
3. ✅ **提交** requirements.txt 到版本控制
4. ❌ **不要提交** .venv 文件夹到Git（已在.gitignore中）
5. ✅ **为每个项目**创建独立的虚拟环境

## 📝 项目特定的虚拟环境说明

本项目的虚拟环境位于：
```
D:\WorkTool\RLEazyTool\.venv\
```

当前子工具 **merge** 默认可纯标准库运行；`.gitignore` 为可选能力。其它脚本如需第三方库，请在本目录激活 `.venv` 后自行 `pip install`。

## 🔍 验证安装（可选）

```bash
.venv\Scripts\activate
cd tools\merge
py test_merge_logic.py
py test_path_utils.py
```

若测试通过，说明 Python 与路径正常。

---

**提示**: 首次使用后，建议将虚拟环境路径添加到IDE配置中，以获得更好的开发体验。
