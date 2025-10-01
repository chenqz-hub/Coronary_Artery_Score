"""
创建单表格式Excel模板
一行代表一个患者，包含基本信息和主要病变信息
"""

import pandas as pd
from pathlib import Path

def create_single_sheet_template():
    """创建单工作表格式的Excel模板"""
    
    # 单表格式数据 - 每行一个患者
    data = {
        # 患者基本信息 (必需)
        'patient_id': ['P001', 'P002', 'P003', 'P004'],
        'age': [65, 58, 72, 45],
        'gender': ['male', 'female', 'male', 'male'],
        
        # 临床信息 (可选)
        'diabetes': [True, False, True, False],
        'hypertension': [True, False, True, True],
        'hyperlipidemia': [False, True, True, False],
        'smoking': [False, True, True, False],
        'ejection_fraction': [55.0, 60.0, 35.0, 65.0],
        'creatinine_mg_dl': [1.2, 0.9, 2.1, 1.0],
        
        # 主要病变信息 (必需)
        'vessel': ['LAD', 'LCX', 'LM', 'RCA'],
        'stenosis_percent': [75.0, 85.0, 80.0, 60.0],
        'location': ['proximal', 'proximal', 'proximal', 'mid'],
        
        # 病变特征 (可选)
        'length_mm': [15.0, 20.0, 12.0, 8.0],
        'is_bifurcation': [True, True, True, False],
        'is_calcified': [True, False, True, False],
        'is_ostial': [False, False, False, False],
        'is_tortuous': [False, True, False, False],
        'is_cto': [False, False, False, False],
        'thrombus_present': [False, False, False, False],
        
        # 备注信息 (可选)
        'notes': ['LAD近段分叉钙化病变', 'LCX近段迂曲病变', '左主干分叉钙化病变', 'RCA中段病变']
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为Excel文件
    output_path = Path('data/single_sheet_template.xlsx')
    output_path.parent.mkdir(exist_ok=True)
    
    df.to_excel(output_path, index=False, sheet_name='patients')
    
    return output_path, df

def main():
    print("📋 创建单表格式Excel模板")
    print("=" * 50)
    
    output_path, df = create_single_sheet_template()
    
    print(f"✓ 模板已创建: {output_path}")
    print(f"✓ 包含 {len(df)} 个示例患者")
    print()
    
    print("📊 模板预览:")
    print(df.to_string())
    print()
    
    print("📝 字段说明:")
    print("必需字段:")
    print("  - patient_id: 患者ID") 
    print("  - age: 年龄")
    print("  - gender: 性别 (male/female)")
    print("  - vessel: 主要病变血管 (LM/LAD/LCX/RCA/OM/D/PDA)")
    print("  - stenosis_percent: 狭窄百分比 (0-100)")
    print("  - location: 病变位置 (proximal/mid/distal)")
    print()
    print("可选字段:")
    print("  - diabetes, hypertension: 合并症 (TRUE/FALSE)")
    print("  - ejection_fraction: 射血分数 (%)")
    print("  - is_bifurcation, is_calcified: 病变特征 (TRUE/FALSE)")
    print("  - length_mm: 病变长度 (mm)")
    print()

if __name__ == "__main__":
    main()