import pandas as pd
from pathlib import Path

# 创建患者数据示例
patients_data = {
    'patient_id': ['P001', 'P002', 'P003'],
    'age': [65, 58, 72],
    'gender': ['male', 'female', 'male'],
    'diabetes': [True, False, True],
    'hypertension': [True, False, True], 
    'hyperlipidemia': [False, True, True],
    'smoking': [False, True, True],
    'ejection_fraction': [55.0, 60.0, 35.0],
    'creatinine_mg_dl': [1.2, 0.9, 2.1]
}

# 创建病变数据示例
lesions_data = {
    'patient_id': ['P001', 'P001', 'P002', 'P003', 'P003', 'P003'],
    'lesion_id': ['L001', 'L002', 'L003', 'L004', 'L005', 'L006'],
    'vessel': ['LAD', 'RCA', 'LCX', 'LM', 'LAD', 'RCA'],
    'stenosis_percent': [75.0, 60.0, 85.0, 80.0, 100.0, 90.0],
    'location': ['proximal', 'mid', 'proximal', 'proximal', 'mid', 'proximal'],
    'length_mm': [15.0, 8.0, 20.0, 12.0, 25.0, 18.0],
    'is_bifurcation': [True, False, True, True, False, False],
    'is_calcified': [True, False, False, True, True, True],
    'is_cto': [False, False, False, False, True, False],
    'thrombus_present': [False, False, False, False, False, False]
}

# 创建Excel文件
with pd.ExcelWriter('data/excel_template.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(patients_data).to_excel(writer, sheet_name='patients', index=False)
    pd.DataFrame(lesions_data).to_excel(writer, sheet_name='lesions', index=False)

print("Excel模板已创建: data/excel_template.xlsx")