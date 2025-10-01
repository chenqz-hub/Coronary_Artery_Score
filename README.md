# 冠脉病变严重程度评分系统

## 项目简介

冠脉病变严重程度评分系统是一个专业的医疗软件工具，用于计算和评估冠状动脉病变的严重程度。本系统实现了多种国际通用的冠脉评分标准，包括SYNTAX评分、CAD-RADS评分、Gensini评分等，为临床医生提供客观、准确的病变严重程度评估。

**🔒 隐私保护**: 本项目的 `data/` 文件夹已设置为Git排除，确保患者数据不会被意外提交到版本控制系统中，保护医疗数据隐私和安全。

## 功能特点

- **多种评分系统支持**：SYNTAX评分、CAD-RADS评分、Gensini评分等
- **数据验证**：完整的输入数据验证和错误处理
- **标准化接口**：清晰的API设计，易于集成到现有医疗系统
- **完整测试覆盖**：全面的单元测试和集成测试
- **详细文档**：完整的API文档和使用指南

## 安装指南

### 系统要求

- Python 3.8+
- 操作系统：Windows/Linux/macOS

### 安装步骤

1. 克隆项目仓库：
```bash
git clone https://github.com/your-username/coronary-artery-score.git
cd coronary-artery-score
```

2. 创建虚拟环境：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 安装项目：
```bash
pip install -e .
```

## 快速开始

```python
from coronary_score import SyntaxCalculator, PatientData

# 创建患者数据
patient_data = PatientData(
    age=65,
    gender='male',
    diabetes=True,
    hypertension=True,
    lesions=[
        {
            'vessel': 'LAD',
            'stenosis_percent': 75,
            'location': 'proximal',
            'length': 15
        }
    ]
)

# 计算SYNTAX评分
calculator = SyntaxCalculator()
score = calculator.calculate(patient_data)
print(f"SYNTAX Score: {score}")
```

## 项目结构

```
coronary-artery-score/
├── src/
│   └── coronary_score/
│       ├── __init__.py
│       ├── models/          # 数据模型
│       ├── calculators/     # 评分计算器
│       └── utils/           # 工具函数
├── tests/                   # 测试用例
├── docs/                    # 文档
├── examples/                # 示例代码
├── data/                    # 测试数据
├── requirements.txt         # 项目依赖
├── setup.py                 # 安装配置
└── README.md               # 项目说明
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_syntax_calculator.py

# 生成测试覆盖率报告
pytest --cov=coronary_score --cov-report=html
```

### 代码规范

本项目遵循PEP 8代码规范，使用以下工具进行代码质量检查：

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

## 贡献指南

欢迎提交问题和改进建议！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者：[您的姓名]
- 邮箱：[您的邮箱]
- 项目链接：[项目GitHub链接]

## 免责声明

本软件仅用于学习和研究目的，不能替代专业医疗建议。在临床应用中使用本软件的结果时，请务必咨询专业医师。