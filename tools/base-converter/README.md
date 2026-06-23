# base-converter — 计组计算题可视化工具

面向《计算机组成与结构》计算题复习的可视化学习工具，覆盖复习大纲中第二章的核心计算内容：

- 十进制 ↔ 二进制 ↔ 十六进制转换（整数 / 小数）
- 机器码：原码、反码、补码、移码、双符号位变形补码
- 定点补码加减法 + 溢出判断
- 浮点数加减法（对阶、尾数运算、规格化、舍入、判溢出）

## 快速开始

```bash
cd tools/base-converter
# 首次运行会自动创建 .venv 并安装依赖；也可手动执行：
# setup.bat
base-converter.bat
```

启动后浏览器自动打开 `http://127.0.0.1:8766/`。

## 手动启动

```bash
cd tools/base-converter
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8766
```

浏览器访问 `http://127.0.0.1:8766/`。

## 项目结构

```
tools/base-converter/
├── backend/
│   ├── domain/            # 纯函数核心业务逻辑
│   │   ├── base_conversion.py
│   │   ├── machine_number.py
│   │   ├── fixed_point.py
│   │   └── floating_point.py
│   ├── application/       # 用例编排
│   ├── api/               # FastAPI 路由
│   └── main.py
├── frontend/              # 单页 Web 可视化界面
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/                 # pytest 单元测试 + API 测试
├── requirements.txt
├── setup.bat
└── base-converter.bat
```

## 运行测试

```bash
cd tools/base-converter
.venv\Scripts\python.exe -m pytest tests -v
```

## 使用说明

1. 在顶部标签页选择要练习的模块。
2. 填写参数后点击按钮，结果与完整步骤直接显示。
3. 位图区域用不同颜色区分符号位、数值位、阶码、尾数。

## 注意事项

- 浮点模块默认采用教材约定：**阶码为双符号位补码，尾数为单符号位补码**。
- 小数转换按指定精度截断，无法精确表示时会给出提示。
