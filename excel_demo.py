"""
Excel数据评分演示脚本 - 简化版本
"""

import pandas as pd
import json
from pathlib import Path


def create_sample_excel():
    """创建示例Excel文件"""
    # 患者数据
    patients_data = {
        'patient_id': ['P001', 'P002', 'P003'],
        'age': [65, 58, 72],
        'gender': ['male', 'female', 'male'],
        'diabetes': [True, False, True],
        'hypertension': [True, False, True], 
        'ejection_fraction': [55.0, 60.0, 35.0],
        'creatinine_mg_dl': [1.2, 0.9, 2.1]
    }

    # 病变数据
    lesions_data = {
        'patient_id': ['P001', 'P001', 'P002', 'P003', 'P003', 'P003'],
        'vessel': ['LAD', 'RCA', 'LCX', 'LM', 'LAD', 'RCA'],
        'stenosis_percent': [75.0, 60.0, 85.0, 80.0, 100.0, 90.0],
        'location': ['proximal', 'mid', 'proximal', 'proximal', 'mid', 'proximal'],
        'is_bifurcation': [True, False, True, True, False, False],
        'is_calcified': [True, False, False, True, True, True],
        'is_cto': [False, False, False, False, True, False]
    }

    # 创建Excel文件
    excel_path = Path('data/sample_patients.xlsx')
    excel_path.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        pd.DataFrame(patients_data).to_excel(writer, sheet_name='patients', index=False)
        pd.DataFrame(lesions_data).to_excel(writer, sheet_name='lesions', index=False)
    
    return excel_path


def excel_to_json(excel_path):
    """将Excel数据转换为JSON格式"""
    
    # 读取Excel文件
    patients_df = pd.read_excel(excel_path, sheet_name='patients')
    lesions_df = pd.read_excel(excel_path, sheet_name='lesions')
    
    # 转换为JSON结构
    patients_json = []
    
    for _, patient_row in patients_df.iterrows():
        # 获取患者基本信息
        patient_data = {
            'patient_id': patient_row['patient_id'],
            'age': int(patient_row['age']),
            'gender': patient_row['gender'],
            'diabetes': bool(patient_row['diabetes']),
            'hypertension': bool(patient_row['hypertension']),
        }
        
        if not pd.isna(patient_row.get('ejection_fraction')):
            patient_data['ejection_fraction'] = float(patient_row['ejection_fraction'])
        
        if not pd.isna(patient_row.get('creatinine_mg_dl')):
            patient_data['creatinine_mg_dl'] = float(patient_row['creatinine_mg_dl'])
        
        # 获取该患者的病变
        patient_lesions = lesions_df[lesions_df['patient_id'] == patient_row['patient_id']]
        lesions = []
        
        for _, lesion_row in patient_lesions.iterrows():
            lesion_data = {
                'vessel': lesion_row['vessel'],
                'stenosis_percent': float(lesion_row['stenosis_percent']),
                'location': lesion_row['location'],
                'is_bifurcation': bool(lesion_row.get('is_bifurcation', False)),
                'is_calcified': bool(lesion_row.get('is_calcified', False)),
                'is_cto': bool(lesion_row.get('is_cto', False)),
            }
            lesions.append(lesion_data)
        
        patient_data['lesions'] = lesions
        patients_json.append(patient_data)
    
    return patients_json


def calculate_syntax_score(patient):
    """简化的SYNTAX评分计算"""
    total_score = 0
    
    for lesion in patient.get('lesions', []):
        # 基础分数（根据血管和狭窄程度）
        vessel = lesion['vessel']
        stenosis = lesion['stenosis_percent']
        
        if stenosis < 50:
            continue  # SYNTAX只计算≥50%的病变
        
        # 血管权重
        vessel_weights = {
            'LM': 5.0,   # 左主干
            'LAD': 3.5,  # 左前降支
            'LCX': 3.5,  # 左回旋支  
            'RCA': 3.5   # 右冠脉
        }
        
        base_weight = vessel_weights.get(vessel, 1.0)
        
        # 狭窄程度系数
        if stenosis >= 99:
            stenosis_factor = 5.0  # 完全闭塞
        elif stenosis >= 90:
            stenosis_factor = 2.0
        elif stenosis >= 70:
            stenosis_factor = 1.5
        else:
            stenosis_factor = 1.0
        
        lesion_score = base_weight * stenosis_factor
        
        # 复杂性加分
        if lesion.get('is_bifurcation'):
            lesion_score += 1.0
        if lesion.get('is_calcified'):
            lesion_score += 2.0
        if lesion.get('is_cto'):
            lesion_score += 5.0
        
        total_score += lesion_score
    
    # 风险分层
    if total_score <= 22:
        risk_category = 'low'
    elif total_score <= 32:
        risk_category = 'intermediate'
    else:
        risk_category = 'high'
    
    return {
        'total_score': round(total_score, 1),
        'risk_category': risk_category
    }


def calculate_cadrads_score(patient):
    """简化的CAD-RADS评分计算"""
    max_grade = 0
    
    for lesion in patient.get('lesions', []):
        stenosis = lesion['stenosis_percent']
        
        if stenosis == 0:
            grade = 0
        elif stenosis <= 24:
            grade = 1
        elif stenosis <= 49:
            grade = 2
        elif stenosis <= 69:
            grade = 3
        elif stenosis <= 99:
            grade = 4
        else:
            grade = 5
        
        max_grade = max(max_grade, grade)
    
    return {
        'overall_grade': max_grade,
        'max_stenosis': max([l['stenosis_percent'] for l in patient.get('lesions', [])], default=0)
    }


def process_excel_file(excel_path):
    """处理Excel文件并计算评分"""
    
    print(f"正在处理Excel文件: {excel_path}")
    print("=" * 60)
    print()
    
    try:
        # 转换Excel为JSON格式
        patients = excel_to_json(excel_path)
        
        print(f"✓ 成功导入 {len(patients)} 名患者的数据")
        print()
        
        # 对每个患者计算评分
        for i, patient in enumerate(patients, 1):
            print(f"患者 {i}: {patient['patient_id']}")
            print("-" * 40)
            print(f"基本信息: {patient['age']}岁 {patient['gender']}")
            print(f"糖尿病: {'是' if patient['diabetes'] else '否'}, "
                  f"高血压: {'是' if patient['hypertension'] else '否'}")
            
            if 'ejection_fraction' in patient:
                print(f"射血分数: {patient['ejection_fraction']}%")
            
            print(f"病变数量: {len(patient['lesions'])}")
            print()
            
            # 显示病变详情
            if patient['lesions']:
                print("病变详情:")
                for j, lesion in enumerate(patient['lesions'], 1):
                    features = []
                    if lesion.get('is_bifurcation'):
                        features.append("分叉")
                    if lesion.get('is_calcified'):
                        features.append("钙化")
                    if lesion.get('is_cto'):
                        features.append("CTO")
                    
                    feature_str = f" ({', '.join(features)})" if features else ""
                    print(f"  {j}. {lesion['vessel']} {lesion['stenosis_percent']}% "
                          f"({lesion['location']}){feature_str}")
                print()
            
            # 计算SYNTAX评分
            syntax_result = calculate_syntax_score(patient)
            print(f"SYNTAX评分: {syntax_result['total_score']} "
                  f"({syntax_result['risk_category']}风险)")
            
            if syntax_result['risk_category'] == 'low':
                print("  → 建议: 适合PCI治疗")
            elif syntax_result['risk_category'] == 'intermediate':
                print("  → 建议: PCI和CABG均可考虑，建议心脏团队讨论")
            else:
                print("  → 建议: 优先考虑CABG治疗")
            
            # 计算CAD-RADS评分
            cadrads_result = calculate_cadrads_score(patient)
            print(f"CAD-RADS评分: {cadrads_result['overall_grade']}级 "
                  f"(最大狭窄: {cadrads_result['max_stenosis']}%)")
            
            grade_descriptions = {
                0: "无冠脉病变",
                1: "轻微病变，生活方式干预",
                2: "轻度病变，药物治疗",
                3: "中度病变，考虑功能学检查",
                4: "重度病变，建议血管造影",
                5: "完全闭塞，建议血管造影"
            }
            
            print(f"  → 建议: {grade_descriptions.get(cadrads_result['overall_grade'], '请咨询医师')}")
            
            print()
            print("=" * 60)
            print()
    
    except Exception as e:
        print(f"处理Excel文件时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """主函数"""
    print("🏥 冠脉病变严重程度评分系统")
    print("📊 Excel文件处理演示")
    print("=" * 60)
    print()
    
    # 创建示例Excel文件
    print("1. 创建示例Excel文件...")
    excel_file = create_sample_excel()
    print(f"   ✓ 已创建: {excel_file}")
    print()
    
    # 处理Excel文件
    print("2. 处理Excel数据并计算评分...")
    success = process_excel_file(excel_file)
    
    if success:
        print("✅ Excel文件处理完成！")
        print()
        print("📋 如何使用您自己的Excel文件:")
        print("1. 参考生成的 'data/sample_patients.xlsx' 格式")
        print("2. 确保包含两个工作表:")
        print("   - 'patients': 患者基本信息")
        print("   - 'lesions': 病变详细信息")
        print("3. 必需字段:")
        print("   患者表: patient_id, age, gender, diabetes, hypertension")
        print("   病变表: patient_id, vessel, stenosis_percent, location")
        print("4. 修改本脚本中的文件路径，处理您的数据")
        print()
        print("🎯 支持的评分系统:")
        print("   - SYNTAX评分: 评估介入治疗复杂性")
        print("   - CAD-RADS评分: 冠脉CT标准化报告")
        print("   - Gensini评分: 量化病变严重程度")
    else:
        print("❌ Excel文件处理失败")


if __name__ == "__main__":
    main()