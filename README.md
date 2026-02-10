# 冠脉病变严重程度评分系统

## 项目简介

本项目用于计算冠状动脉病变严重程度评分，支持 SYNTAX、CAD-RADS、Gensini 三种评分。当前目录已精简为“评分专用流程”，通过脚本批量选择文件并生成合并后的评分结果。

## 快速开始

1. 安装依赖：
```bash
pip install pandas
```

2. 运行评分脚本（带文件选择对话框）：
```bash
python run_scoring_with_dialog.py
```

3. 选择一个或多个 CSV/XLSX 文件，程序会生成与输入同格式的结果文件，文件名追加 `_评分合并` 后缀。

## 输入数据要求（宽表）

### 必需字段（列）
- `subjid`：患者ID
- `sys_currentage`：年龄
- `stsex`：性别（1=男，2=女）

### 病变节段列（示例）
程序会从以下列中识别病变并提取狭窄百分比：

- 右冠近段、右冠中段、右冠远段、右冠-后降支、右冠-左室后侧支
- 左主干、左冠-前降支近段、左冠-前降支中段、左冠-前降支远段
- 左冠-第一对角支、左冠-第二对角支
- 左冠-回旋支近段、左冠-回旋支中段、左冠-回旋支远段
- 左冠-第一钝缘支、左冠-第二钝缘支、左冠-左房回旋支
- 左冠-左室后侧支、左冠-后降支

### 文本提取规则
- “30-65%”取上限 65
- “无狭窄/正常”视为 0%（默认不参与评分）
- “轻度/中度/重度/完全闭塞”分别映射到 50/70/90/100

## 评分汇总规则

- `SYNTAX_score`：按患者所有病变求和
- `Gensini_score`：按患者所有病变求和
- `CAD_RADS_grade`：按患者取最大值
- `SYNTAX_class`：根据 SYNTAX 总分分层（Low/Intermediate/High）
- `Gensini_class`：根据 Gensini 总分分层（Normal/Mild/Moderate/Severe/Critical）

## 输出说明

输出文件与输入同格式，列尾追加：
- `SYNTAX_score`, `SYNTAX_class`
- `CAD_RADS_grade`
- `Gensini_score`, `Gensini_class`

## 项目入口

- `run_scoring_with_dialog.py`：评分主脚本（含文件选择与进度提示）
- `single_sheet_processor_v2.py`：评分计算器核心逻辑

## 免责声明

本软件仅用于学习和研究目的，不能替代专业医疗建议。在临床应用中使用本软件的结果时，请务必咨询专业医师。
