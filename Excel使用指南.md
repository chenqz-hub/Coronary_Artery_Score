# 📊 冠脉评分Excel处理工具使用指南

## 🎯 功能概述

这个工具可以处理Excel文件中的冠脉病变数据，自动计算三种主要评分：

- **SYNTAX评分** - 评估介入治疗复杂性 (PCI vs CABG决策)
- **CAD-RADS评分** - 冠脉CT标准化报告 (0-5级)
- **Gensini评分** - 量化病变严重程度 (预后评估)

## 📋 Excel文件格式要求

### 方式一：双工作表格式（推荐）

**patients工作表 (患者基本信息):**
| patient_id | age | gender | diabetes | hypertension | ejection_fraction | creatinine_mg_dl |
|------------|-----|--------|----------|--------------|------------------|------------------|
| P001       | 65  | male   | TRUE     | TRUE         | 55.0             | 1.2              |
| P002       | 58  | female | FALSE    | FALSE        | 60.0             | 0.9              |

**lesions工作表 (病变详细信息):**
| patient_id | vessel | stenosis_percent | location | is_bifurcation | is_calcified | is_cto | length_mm |
|------------|--------|------------------|----------|----------------|--------------|--------|-----------|
| P001       | LAD    | 75.0            | proximal | TRUE           | TRUE         | FALSE  | 15.0      |
| P001       | RCA    | 60.0            | mid      | FALSE          | FALSE        | FALSE  | 8.0       |

### 方式二：单工作表格式

将患者信息和病变信息合并在一个工作表中，适用于简单病例。

## 🔑 必需字段

### 患者信息 (必需)
- `patient_id` - 患者ID
- `age` - 年龄
- `gender` - 性别 (male/female)

### 病变信息 (必需)
- `vessel` - 血管类型 (LM/LAD/LCX/RCA/OM/D/PDA/PLV)
- `stenosis_percent` - 狭窄百分比 (0-100)
- `location` - 位置 (proximal/mid/distal)

### 可选字段
**患者信息:**
- `diabetes` - 糖尿病 (TRUE/FALSE)
- `hypertension` - 高血压 (TRUE/FALSE)
- `hyperlipidemia` - 高脂血症 (TRUE/FALSE)
- `smoking` - 吸烟 (TRUE/FALSE)
- `ejection_fraction` - 射血分数 (%)
- `creatinine_mg_dl` - 肌酐值 (mg/dL)

**病变信息:**
- `is_bifurcation` - 分叉病变 (TRUE/FALSE)
- `is_calcified` - 钙化病变 (TRUE/FALSE)
- `is_cto` - 慢性完全闭塞 (TRUE/FALSE)
- `is_ostial` - 开口病变 (TRUE/FALSE)
- `is_tortuous` - 迂曲病变 (TRUE/FALSE)
- `thrombus_present` - 血栓存在 (TRUE/FALSE)
- `length_mm` - 病变长度 (mm)

## 🚀 使用方法

### 1. 准备Excel文件
参考 `data/sample_patients.xlsx` 模板，准备您的数据文件。

### 2. 运行处理工具

**方法一：命令行使用**
```bash
python excel_processor.py 您的文件.xlsx -o 结果.json
```

**方法二：直接运行演示**
```bash
python excel_processor.py
# 会自动处理示例文件
```

### 3. 查看结果
工具会在控制台显示详细的评分结果，包括：
- 患者基本信息和病变详情
- 三种评分的具体数值和风险分层
- 个性化的治疗建议
- 综合评估意见

## 📊 评分解读

### SYNTAX评分
- **≤22分** - 低风险，适合PCI治疗
- **23-32分** - 中等风险，PCI和CABG均可考虑
- **≥33分** - 高风险，优先考虑CABG治疗

### CAD-RADS评分
- **0级** - 无冠脉病变
- **1级** - 轻微病变 (1-24%狭窄)
- **2级** - 轻度病变 (25-49%狭窄)
- **3级** - 中度病变 (50-69%狭窄)
- **4级** - 重度病变 (70-99%狭窄)
- **5级** - 完全闭塞 (100%狭窄)

### Gensini评分
- **0分** - 无病变
- **≤20分** - 轻度病变
- **21-40分** - 中度病变
- **41-80分** - 重度病变
- **>80分** - 极重度病变

## ⚠️ 注意事项

1. **数据准确性** - 确保狭窄百分比、血管类型等关键数据的准确性
2. **临床相关性** - 评分结果仅供参考，最终治疗决策应结合临床症状和其他检查
3. **文件格式** - 支持 .xlsx 和 .xls 格式的Excel文件
4. **字段匹配** - 确保Excel中的字段名与要求的格式一致

## 🛠️ 故障排除

### 常见问题
1. **"文件不存在"** - 检查文件路径是否正确
2. **"字段缺失"** - 确保必需字段都已填写
3. **"数据格式错误"** - 检查数值字段是否为数字格式
4. **"导入失败"** - 确认Excel文件未被其他程序占用

### 数据验证
工具会自动验证数据的合理性：
- 年龄范围 (0-150岁)
- 狭窄百分比 (0-100%)
- 射血分数 (0-100%)

## 📧 技术支持

如需帮助，请提供：
1. Excel文件样例
2. 错误信息截图
3. 期望的输出结果

---

*本工具基于国际通用的冠脉评分标准开发，适用于临床研究和辅助决策。*