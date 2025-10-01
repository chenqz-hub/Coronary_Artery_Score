# 用户指南

## 概述

冠脉病变严重程度评分系统是一个专业的医疗软件工具，用于计算和评估冠状动脉病变的严重程度。本系统实现了三种主要的国际通用评分标准：

1. **SYNTAX评分** - 评估介入治疗的复杂性
2. **CAD-RADS评分** - 冠脉CT标准化报告
3. **Gensini评分** - 量化病变的解剖严重程度

## 快速开始

### 安装

```bash
pip install coronary-artery-score
```

### 基本使用

```python
from coronary_score import PatientData, Lesion, SyntaxCalculator
from coronary_score.models.patient import Gender, VesselType, StenosisLocation

# 创建患者数据
patient = PatientData(
    age=65,
    gender=Gender.MALE,
    diabetes=True
)

# 添加病变
lesion = Lesion(
    vessel=VesselType.LAD,
    stenosis_percent=75.0,
    location=StenosisLocation.PROXIMAL
)
patient.add_lesion(lesion)

# 计算评分
calculator = SyntaxCalculator()
result = calculator.calculate(patient)

print(f"SYNTAX评分: {result['total_score']}")
```

## 详细指南

### 1. 患者数据创建

#### 基本信息

每个患者需要提供年龄和性别这两个必需信息：

```python
patient = PatientData(
    age=65,
    gender=Gender.MALE
)
```

#### 临床信息

可以添加详细的临床信息以获得更准确的评分：

```python
patient = PatientData(
    patient_id="P001",
    age=65,
    gender=Gender.MALE,
    diabetes=True,              # 糖尿病
    hypertension=True,          # 高血压
    hyperlipidemia=False,       # 高脂血症
    smoking=True,               # 吸烟史
    family_history=False,       # 冠心病家族史
    creatinine_mg_dl=1.2,      # 肌酐值
    ejection_fraction=55.0      # 射血分数
)
```

### 2. 病变数据录入

#### 基本病变

每个病变需要指定血管、狭窄程度和位置：

```python
lesion = Lesion(
    vessel=VesselType.LAD,                    # 左前降支
    stenosis_percent=75.0,                    # 75%狭窄
    location=StenosisLocation.PROXIMAL        # 近段
)
```

#### 复杂病变

可以添加更多的病变特征：

```python
complex_lesion = Lesion(
    lesion_id="L001",
    vessel=VesselType.LM,                     # 左主干
    stenosis_percent=85.0,
    location=StenosisLocation.PROXIMAL,
    length_mm=25.0,                          # 病变长度
    is_bifurcation=True,                     # 分叉病变
    is_calcified=True,                       # 钙化病变
    is_tortuous=False,                       # 迂曲病变
    is_cto=False,                           # 慢性完全闭塞
    thrombus_present=False                   # 血栓存在
)
```

#### 血管类型说明

- `VesselType.LM` - 左主干
- `VesselType.LAD` - 左前降支
- `VesselType.LCX` - 左回旋支
- `VesselType.RCA` - 右冠状动脉
- `VesselType.OM` - 钝缘支
- `VesselType.D` - 对角支

#### 位置说明

- `StenosisLocation.PROXIMAL` - 近段
- `StenosisLocation.MID` - 中段
- `StenosisLocation.DISTAL` - 远段

### 3. 评分计算

#### SYNTAX评分

SYNTAX评分主要用于评估冠脉病变介入治疗的复杂性，帮助决策PCI vs CABG：

```python
syntax_calc = SyntaxCalculator()
result = syntax_calc.calculate(patient)

print(f"解剖学评分: {result['anatomical_score']}")
print(f"临床评分: {result['clinical_score']}")
print(f"SYNTAX II评分: {result['syntax_ii_score']}")
print(f"风险分层: {result['risk_category']}")  # low/intermediate/high
```

**风险分层标准：**
- 低风险 (≤22分): 适合PCI治疗
- 中等风险 (23-32分): PCI和CABG均可考虑
- 高风险 (≥33分): 优先考虑CABG治疗

#### CAD-RADS评分

CAD-RADS用于冠脉CT的标准化报告：

```python
cadrads_calc = CadRadsCalculator()
result = cadrads_calc.calculate(patient)

print(f"总体等级: {result['overall_grade']}")     # 0-5级
print(f"最大狭窄: {result['max_stenosis']}%")
print(f"主要病变血管: {result['dominant_vessel']}")
print(f"治疗建议: {result['recommendation']}")
```

**等级说明：**
- 0级: 无冠脉病变
- 1级: 轻微病变 (1-24%狭窄)
- 2级: 轻度病变 (25-49%狭窄)  
- 3级: 中度病变 (50-69%狭窄)
- 4级: 重度病变 (70-99%狭窄)
- 5级: 完全闭塞 (100%狭窄)

#### Gensini评分

Gensini评分用于量化冠脉病变的解剖严重程度：

```python
gensini_calc = GensiniCalculator()
result = gensini_calc.calculate(patient)

print(f"总评分: {result['total_score']}")
print(f"严重程度: {result['severity_grade']}")    # normal/mild/moderate/severe/critical
print(f"各血管评分: {result['vessel_scores']}")
```

**严重程度分级：**
- normal: 无病变
- mild: 轻度 (≤20分)
- moderate: 中度 (21-40分)
- severe: 重度 (41-80分)
- critical: 极重度 (>80分)

### 4. 详细报告

#### 获取详细报告

每个计算器都可以生成详细的分析报告：

```python
# SYNTAX详细报告
syntax_report = syntax_calc.get_detailed_report(patient)
print("病变详情:")
for detail in syntax_report['lesion_details']:
    print(f"  {detail['vessel']}: {detail['stenosis_percent']}% "
          f"(总贡献: {detail['total_contribution']}分)")

print(f"治疗建议: {syntax_report['recommendation']}")
```

#### 报告内容说明

详细报告通常包含：

1. **评分结果** - 各项评分的具体数值
2. **病变分析** - 每个病变对总分的贡献
3. **风险评估** - 基于评分的风险分层
4. **治疗建议** - 个性化的治疗建议
5. **随访计划** - 后续检查和随访安排

### 5. 数据管理

#### 导入数据

支持从多种格式导入患者数据：

```python
from coronary_score.data_io import DataImporter

importer = DataImporter()

# 从JSON文件导入
patients = importer.import_from_file('patients.json')

# 从CSV文件导入
patients = importer.import_from_file('patients.csv')

# 从Excel文件导入
patients = importer.import_from_file('patients.xlsx')
```

#### 导出结果

可以将评分结果导出为多种格式：

```python
from coronary_score.data_io import DataExporter

exporter = DataExporter()

# 导出为JSON
exporter.export_to_file(patients, 'results.json')

# 导出为Excel
exporter.export_to_file(patients, 'results.xlsx')
```

#### 数据格式示例

**JSON格式：**
```json
{
  "patient_id": "P001",
  "age": 65,
  "gender": "male",
  "diabetes": true,
  "hypertension": true,
  "lesions": [
    {
      "vessel": "LAD",
      "stenosis_percent": 75.0,
      "location": "proximal",
      "is_bifurcation": true
    }
  ]
}
```

### 6. 数据验证

#### 自动验证

系统会自动验证输入数据的有效性：

```python
from coronary_score.utils.validation import validate_patient_data

is_valid, errors = validate_patient_data(patient)
if not is_valid:
    for error in errors:
        print(f"验证错误: {error}")
```

#### 常见验证问题

1. **年龄范围** - 必须在0-150岁之间
2. **狭窄百分比** - 必须在0-100%之间
3. **射血分数** - 必须在0-100%之间
4. **病变一致性** - CTO病变的狭窄程度应为99-100%

### 7. 命令行工具

#### 基本用法

```bash
# 计算所有评分
coronary-score --input data.json --calculator all --output results.json

# 只计算SYNTAX评分
coronary-score --input data.json --calculator syntax

# 创建示例数据
coronary-score --create-sample --output sample.json

# 验证数据
coronary-score --input data.json --validate
```

#### 命令行选项

- `--input, -i`: 输入数据文件
- `--output, -o`: 输出结果文件
- `--calculator, -c`: 选择计算器 (syntax/cadrads/gensini/all)
- `--create-sample`: 创建示例数据
- `--validate`: 只验证数据不计算
- `--verbose, -v`: 显示详细信息

## 临床应用指导

### 1. 使用场景

#### SYNTAX评分适用于：
- PCI vs CABG决策
- 介入治疗复杂性评估
- 多支病变治疗策略制定

#### CAD-RADS适用于：
- 冠脉CT标准化报告
- 影像学随访计划
- 进一步检查决策

#### Gensini评分适用于：
- 病变严重程度量化
- 预后评估
- 研究和流行病学调查

### 2. 结果解读

#### 综合评估

建议结合多个评分系统进行综合评估：

```python
# 计算所有评分
syntax_result = syntax_calc.calculate(patient)
cadrads_result = cadrads_calc.calculate(patient)
gensini_result = gensini_calc.calculate(patient)

# 综合判断
if syntax_result['risk_category'] == 'high':
    print("SYNTAX高风险，建议CABG治疗")
    
if cadrads_result['overall_grade'] >= 4:
    print("CAD-RADS 4-5级，需要血管造影确认")
    
if gensini_result['severity_grade'] == 'critical':
    print("Gensini极重度，预后较差")
```

#### 临床决策建议

根据评分结果提供的治疗建议仅供参考，最终治疗决策应结合：

1. 患者症状和临床表现
2. 心肌缺血的客观证据
3. 患者意愿和手术风险
4. 医疗中心的技术条件
5. 指南推荐和专家共识

### 3. 注意事项

1. **数据质量** - 确保输入数据的准确性和完整性
2. **适用范围** - 注意各评分系统的适用条件和局限性
3. **动态评估** - 病情变化时需要重新评估
4. **多学科讨论** - 复杂病例建议心脏团队讨论

## 故障排除

### 常见问题

1. **导入失败**
   - 检查文件格式是否支持
   - 确认数据字段是否完整
   - 验证数据值是否在有效范围内

2. **计算错误**
   - 确认病变数据的完整性
   - 检查血管类型和位置是否正确
   - 验证狭窄百分比是否合理

3. **结果异常**
   - 核对输入数据是否正确
   - 检查是否有数据验证警告
   - 比较不同评分系统的结果

### 技术支持

如需技术支持，请提供：

1. 错误信息和堆栈跟踪
2. 输入数据示例
3. 期望的输出结果
4. 系统环境信息

## 更新日志

### v1.0.0 (2025-10-01)

- 初始版本发布
- 实现SYNTAX、CAD-RADS、Gensini三种评分系统
- 支持JSON、CSV、Excel数据格式
- 提供命令行工具和Python API
- 完整的单元测试和文档