# API 参考文档

## 核心类和方法

### PatientData 类

患者数据模型，用于存储患者的基本信息、临床信息和病变数据。

#### 构造函数

```python
PatientData(
    patient_id: Optional[str] = None,
    age: int,
    gender: Gender,
    diabetes: bool = False,
    hypertension: bool = False,
    hyperlipidemia: bool = False,
    smoking: bool = False,
    family_history: bool = False,
    creatinine_mg_dl: Optional[float] = None,
    ldl_cholesterol: Optional[float] = None,
    ejection_fraction: Optional[float] = None,
    lesions: List[Lesion] = [],
    examination_date: Optional[datetime] = None,
    examination_type: Optional[str] = None
)
```

#### 参数

- `patient_id`: 患者唯一标识符
- `age`: 患者年龄 (0-150)
- `gender`: 患者性别 (`Gender.MALE` 或 `Gender.FEMALE`)
- `diabetes`: 是否患有糖尿病
- `hypertension`: 是否患有高血压
- `ejection_fraction`: 左室射血分数 (0-100%)
- `lesions`: 病变列表

#### 方法

##### `add_lesion(lesion: Lesion) -> None`

添加病变到患者记录中。

```python
patient = PatientData(age=65, gender=Gender.MALE)
lesion = Lesion(vessel=VesselType.LAD, stenosis_percent=75.0, location=StenosisLocation.PROXIMAL)
patient.add_lesion(lesion)
```

##### `get_lesions_by_vessel(vessel: VesselType) -> List[Lesion]`

根据血管类型获取病变列表。

```python
lad_lesions = patient.get_lesions_by_vessel(VesselType.LAD)
```

##### `get_significant_lesions(threshold: float = 50.0) -> List[Lesion]`

获取显著狭窄的病变列表。

```python
significant_lesions = patient.get_significant_lesions(threshold=70.0)
```

### Lesion 类

病变数据模型，描述冠脉病变的详细信息。

#### 构造函数

```python
Lesion(
    lesion_id: Optional[str] = None,
    vessel: VesselType,
    segment_id: Optional[int] = None,
    stenosis_percent: float,
    location: StenosisLocation,
    length_mm: Optional[float] = None,
    morphology: Optional[LesionMorphology] = None,
    is_bifurcation: bool = False,
    is_ostial: bool = False,
    is_calcified: bool = False,
    is_tortuous: bool = False,
    is_cto: bool = False,
    thrombus_present: bool = False,
    is_treated: bool = False,
    treatment_method: Optional[str] = None
)
```

#### 参数

- `vessel`: 病变血管 (`VesselType` 枚举)
- `stenosis_percent`: 狭窄百分比 (0-100)
- `location`: 病变位置 (`StenosisLocation` 枚举)
- `is_bifurcation`: 是否为分叉病变
- `is_calcified`: 是否为钙化病变
- `is_cto`: 是否为慢性完全闭塞

### 枚举类型

#### VesselType

血管类型枚举：

- `LAD`: 左前降支
- `LCX`: 左回旋支  
- `RCA`: 右冠状动脉
- `LM`: 左主干
- `OM`: 钝缘支
- `D`: 对角支
- `PDA`: 后降支
- `PLV`: 左室后支

#### StenosisLocation

狭窄位置枚举：

- `PROXIMAL`: 近端
- `MID`: 中段
- `DISTAL`: 远端

#### Gender

性别枚举：

- `MALE`: 男性
- `FEMALE`: 女性

## 计算器类

### SyntaxCalculator

SYNTAX评分计算器，用于评估冠脉病变的介入治疗复杂性。

#### 方法

##### `calculate(patient_data: PatientData) -> Dict[str, float]`

计算SYNTAX评分。

```python
calculator = SyntaxCalculator()
result = calculator.calculate(patient_data)
```

**返回值：**
```python
{
    'total_score': float,           # 总评分
    'anatomical_score': float,     # 解剖学评分  
    'clinical_score': float,       # 临床评分
    'syntax_ii_score': float,      # SYNTAX II评分
    'risk_category': str          # 风险分层 ('low', 'intermediate', 'high')
}
```

##### `get_detailed_report(patient_data: PatientData) -> Dict`

获取详细的SYNTAX评分报告。

```python
report = calculator.get_detailed_report(patient_data)
```

**返回值包含：**
- `scores`: 评分结果
- `lesion_details`: 每个病变的详细分析
- `recommendation`: 治疗建议

### CadRadsCalculator  

CAD-RADS评分计算器，用于冠脉CT的标准化报告。

#### 方法

##### `calculate(patient_data: PatientData) -> Dict[str, any]`

计算CAD-RADS评分。

```python
calculator = CadRadsCalculator()
result = calculator.calculate(patient_data)
```

**返回值：**
```python
{
    'overall_grade': int,           # 总体等级 (0-5)
    'max_stenosis': float,         # 最大狭窄百分比
    'vessel_grades': Dict[str, int], # 各血管等级
    'dominant_vessel': str,        # 主要病变血管
    'recommendation': str,         # 治疗建议
    'follow_up': str              # 随访建议
}
```

##### `get_detailed_report(patient_data: PatientData) -> Dict`

获取详细的CAD-RADS报告。

### GensiniCalculator

Gensini评分计算器，用于量化冠脉病变的解剖严重程度。

#### 方法

##### `calculate(patient_data: PatientData) -> Dict[str, float]`

计算Gensini评分。

```python
calculator = GensiniCalculator()
result = calculator.calculate(patient_data)
```

**返回值：**
```python
{
    'total_score': float,              # 总评分
    'vessel_scores': Dict[str, float], # 各血管评分
    'lesion_contributions': List[Dict], # 各病变贡献
    'severity_grade': str             # 严重程度分级
}
```

##### `get_detailed_report(patient_data: PatientData) -> Dict`

获取详细的Gensini评分报告。

## 数据导入导出

### DataImporter

数据导入器，支持从JSON、CSV、Excel文件导入患者数据。

#### 方法

##### `import_from_file(file_path: Union[str, Path]) -> List[PatientData]`

从文件导入患者数据。

```python
importer = DataImporter()
patients = importer.import_from_file('patients.json')
```

支持的格式：
- JSON (.json)
- CSV (.csv)  
- Excel (.xlsx, .xls)

### DataExporter

数据导出器，将患者数据导出到文件。

#### 方法

##### `export_to_file(patients: List[PatientData], file_path: Union[str, Path], format_type: Optional[str] = None)`

导出患者数据到文件。

```python
exporter = DataExporter()
exporter.export_to_file(patients, 'results.json')
```

## 工具函数

### 数据验证

#### `validate_patient_data(patient_data: PatientData) -> Tuple[bool, List[str]]`

验证患者数据的完整性和合理性。

```python
from coronary_score.utils.validation import validate_patient_data

is_valid, errors = validate_patient_data(patient)
if not is_valid:
    for error in errors:
        print(f"验证错误: {error}")
```

#### `validate_lesion_data(lesion: Lesion) -> List[str]`

验证单个病变数据。

```python
from coronary_score.utils.validation import validate_lesion_data

errors = validate_lesion_data(lesion)
```

### 血管节段信息

#### `VESSEL_SEGMENTS`

包含所有血管节段定义的字典。

```python
from coronary_score.utils.vessel_segments import VESSEL_SEGMENTS

# 获取LAD近段信息
lad_proximal = VESSEL_SEGMENTS[6]  # segment_id = 6
```

## 异常处理

### ValidationError

数据验证异常，当输入数据不符合要求时抛出。

```python
from coronary_score.utils.validation import ValidationError

try:
    # 数据处理代码
    pass
except ValidationError as e:
    print(f"数据验证失败: {e}")
```

### DataImportError

数据导入异常，当文件导入失败时抛出。

```python
from coronary_score.data_io import DataImportError

try:
    patients = importer.import_from_file('invalid_file.json')
except DataImportError as e:
    print(f"导入失败: {e}")
```

## 完整示例

```python
from coronary_score import (
    PatientData, Lesion, SyntaxCalculator, 
    Gender, VesselType, StenosisLocation
)

# 创建患者
patient = PatientData(
    patient_id="P001",
    age=65,
    gender=Gender.MALE,
    diabetes=True,
    hypertension=True,
    ejection_fraction=55.0
)

# 添加病变
lesion = Lesion(
    vessel=VesselType.LAD,
    stenosis_percent=75.0,
    location=StenosisLocation.PROXIMAL,
    is_bifurcation=True
)
patient.add_lesion(lesion)

# 计算评分
calculator = SyntaxCalculator()
result = calculator.calculate(patient)

print(f"SYNTAX评分: {result['total_score']}")
print(f"风险分层: {result['risk_category']}")

# 获取详细报告
report = calculator.get_detailed_report(patient)
print(f"治疗建议: {report['recommendation']}")
```