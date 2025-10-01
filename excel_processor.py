"""
通用Excel冠脉评分处理工具
支持处理任何符合格式要求的Excel文件
"""

import pandas as pd
import json
import argparse
from pathlib import Path
import sys


class CoronaryScoreCalculator:
    """冠脉评分计算器"""
    
    def __init__(self):
        self.vessel_weights = {
            'LM': 5.0,   # 左主干
            'LAD': 3.5,  # 左前降支近段
            'LCX': 3.5,  # 左回旋支近段
            'RCA': 3.5,  # 右冠脉近段
            'OM': 1.0,   # 钝缘支
            'D': 1.0,    # 对角支
            'PDA': 1.0,  # 后降支
            'PLV': 0.5   # 左室后支
        }
    
    def calculate_syntax_score(self, patient):
        """计算SYNTAX评分"""
        total_score = 0
        lesion_details = []
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            
            if stenosis < 50:
                continue  # SYNTAX只计算≥50%的病变
            
            # 获取血管权重
            vessel = lesion['vessel']
            base_weight = self.vessel_weights.get(vessel, 1.0)
            
            # 根据位置调整权重
            location = lesion.get('location', 'proximal')
            if location == 'mid':
                base_weight *= 0.7
            elif location == 'distal':
                base_weight *= 0.4
            
            # 狭窄程度系数
            if stenosis >= 99:
                stenosis_factor = 5.0  # 完全闭塞
            elif stenosis >= 90:
                stenosis_factor = 2.0
            elif stenosis >= 70:
                stenosis_factor = 1.5
            else:
                stenosis_factor = 1.0
            
            # 基础评分
            base_score = base_weight * stenosis_factor
            
            # 复杂性评分
            complexity_score = 0
            if lesion.get('is_bifurcation', False):
                complexity_score += 1.0
            if lesion.get('is_calcified', False):
                complexity_score += 2.0
            if lesion.get('is_cto', False):
                complexity_score += 5.0
            if lesion.get('is_ostial', False):
                complexity_score += 0.5
            if lesion.get('is_tortuous', False):
                complexity_score += 1.0
            if lesion.get('thrombus_present', False):
                complexity_score += 1.0
            
            # 弥漫性病变(长度>20mm)
            length = lesion.get('length_mm', 0)
            if length > 20:
                complexity_score += 1.0
            
            lesion_score = base_score + complexity_score
            total_score += lesion_score
            
            lesion_details.append({
                'vessel': vessel,
                'stenosis_percent': stenosis,
                'base_score': round(base_score, 2),
                'complexity_score': round(complexity_score, 2),
                'total_contribution': round(lesion_score, 2)
            })
        
        # 风险分层
        if total_score <= 22:
            risk_category = 'low'
            risk_desc = '低风险 - 适合PCI治疗'
        elif total_score <= 32:
            risk_category = 'intermediate'
            risk_desc = '中等风险 - PCI和CABG均可考虑'
        else:
            risk_category = 'high'
            risk_desc = '高风险 - 优先考虑CABG治疗'
        
        return {
            'total_score': round(total_score, 1),
            'risk_category': risk_category,
            'risk_description': risk_desc,
            'lesion_details': lesion_details
        }
    
    def calculate_cadrads_score(self, patient):
        """计算CAD-RADS评分"""
        max_grade = 0
        vessel_grades = {}
        max_stenosis = 0
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            vessel = lesion['vessel']
            
            # 确定等级
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
            max_stenosis = max(max_stenosis, stenosis)
            
            # 记录各血管最高等级
            if vessel not in vessel_grades:
                vessel_grades[vessel] = grade
            else:
                vessel_grades[vessel] = max(vessel_grades[vessel], grade)
        
        # 等级描述和建议
        grade_descriptions = {
            0: ("无冠脉病变", "无需特殊处理"),
            1: ("轻微病变", "生活方式干预，控制危险因素"),
            2: ("轻度病变", "药物治疗，控制危险因素"),
            3: ("中度病变", "考虑功能学检查评估心肌缺血"),
            4: ("重度病变", "建议血管造影，考虑血运重建"),
            5: ("完全闭塞", "建议血管造影，考虑血运重建")
        }
        
        description, recommendation = grade_descriptions.get(max_grade, ("请咨询医师", "请咨询医师"))
        
        return {
            'overall_grade': max_grade,
            'max_stenosis': max_stenosis,
            'vessel_grades': vessel_grades,
            'description': description,
            'recommendation': recommendation
        }
    
    def calculate_gensini_score(self, patient):
        """计算Gensini评分"""
        total_score = 0
        vessel_scores = {}
        
        # Gensini权重系数
        gensini_weights = {
            'LM': 5.0,
            'LAD': 2.5,
            'LCX': 2.5,
            'RCA': 1.0,
            'OM': 1.0,
            'D': 1.0,
            'PDA': 1.0,
            'PLV': 0.5
        }
        
        # 狭窄程度评分
        stenosis_scores = {
            (0, 25): 1,
            (25, 50): 2,
            (50, 75): 4,
            (75, 90): 8,
            (90, 99): 16,
            (99, 100): 32
        }
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            vessel = lesion['vessel']
            
            # 获取狭窄程度评分
            stenosis_score = 0
            for (min_s, max_s), score in stenosis_scores.items():
                if min_s < stenosis <= max_s:
                    stenosis_score = score
                    break
            
            # 获取血管权重
            vessel_weight = gensini_weights.get(vessel, 1.0)
            
            # 根据位置调整
            location = lesion.get('location', 'proximal')
            if location == 'mid':
                vessel_weight *= 0.8
            elif location == 'distal':
                vessel_weight *= 0.5
            
            lesion_score = stenosis_score * vessel_weight
            total_score += lesion_score
            
            if vessel not in vessel_scores:
                vessel_scores[vessel] = 0
            vessel_scores[vessel] += lesion_score
        
        # 严重程度分级
        if total_score == 0:
            severity_grade = 'normal'
            severity_desc = '无病变'
        elif total_score <= 20:
            severity_grade = 'mild'
            severity_desc = '轻度病变'
        elif total_score <= 40:
            severity_grade = 'moderate'
            severity_desc = '中度病变'
        elif total_score <= 80:
            severity_grade = 'severe'
            severity_desc = '重度病变'
        else:
            severity_grade = 'critical'
            severity_desc = '极重度病变'
        
        return {
            'total_score': round(total_score, 1),
            'vessel_scores': vessel_scores,
            'severity_grade': severity_grade,
            'severity_description': severity_desc
        }


def read_excel_file(excel_path):
    """读取Excel文件并转换为标准格式"""
    
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"文件不存在: {excel_path}")
    
    # 获取所有工作表名称
    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names
    
    patients_data = []
    
    if 'patients' in sheet_names and 'lesions' in sheet_names:
        # 双表格式
        patients_df = pd.read_excel(excel_path, sheet_name='patients')
        lesions_df = pd.read_excel(excel_path, sheet_name='lesions')
        
        for _, patient_row in patients_df.iterrows():
            patient_data = extract_patient_info(patient_row)
            
            # 获取该患者的病变
            patient_lesions = lesions_df[lesions_df['patient_id'] == patient_row['patient_id']]
            lesions = []
            
            for _, lesion_row in patient_lesions.iterrows():
                lesion_data = extract_lesion_info(lesion_row)
                lesions.append(lesion_data)
            
            patient_data['lesions'] = lesions
            patients_data.append(patient_data)
    
    else:
        # 单表格式 - 尝试第一个工作表
        df = pd.read_excel(excel_path, sheet_name=0)
        
        # 按patient_id分组
        if 'patient_id' in df.columns:
            for patient_id, group in df.groupby('patient_id'):
                # 使用第一行作为患者信息
                patient_row = group.iloc[0]
                patient_data = extract_patient_info(patient_row)
                
                # 所有行作为病变信息
                lesions = []
                for _, lesion_row in group.iterrows():
                    lesion_data = extract_lesion_info(lesion_row)
                    lesions.append(lesion_data)
                
                patient_data['lesions'] = lesions
                patients_data.append(patient_data)
        else:
            # 每行一个患者
            for _, row in df.iterrows():
                patient_data = extract_patient_info(row)
                lesion_data = extract_lesion_info(row)
                patient_data['lesions'] = [lesion_data] if lesion_data['stenosis_percent'] > 0 else []
                patients_data.append(patient_data)
    
    return patients_data


def extract_patient_info(row):
    """提取患者基本信息"""
    patient_data = {}
    
    # 必需字段
    patient_data['patient_id'] = str(row.get('patient_id', 'Unknown'))
    patient_data['age'] = int(row['age']) if not pd.isna(row.get('age')) else 65
    patient_data['gender'] = str(row.get('gender', 'male')).lower()
    
    # 可选字段
    optional_fields = [
        'diabetes', 'hypertension', 'hyperlipidemia', 'smoking', 'family_history'
    ]
    
    for field in optional_fields:
        if field in row and not pd.isna(row[field]):
            patient_data[field] = bool(row[field])
    
    # 数值字段
    numeric_fields = ['ejection_fraction', 'creatinine_mg_dl', 'ldl_cholesterol']
    
    for field in numeric_fields:
        if field in row and not pd.isna(row[field]):
            patient_data[field] = float(row[field])
    
    return patient_data


def extract_lesion_info(row):
    """提取病变信息"""
    lesion_data = {}
    
    # 必需字段
    lesion_data['vessel'] = str(row.get('vessel', 'LAD')).upper()
    lesion_data['stenosis_percent'] = float(row.get('stenosis_percent', 0))
    lesion_data['location'] = str(row.get('location', 'proximal')).lower()
    
    # 可选字段
    optional_fields = [
        'is_bifurcation', 'is_calcified', 'is_ostial', 'is_tortuous', 
        'is_cto', 'thrombus_present'
    ]
    
    for field in optional_fields:
        if field in row and not pd.isna(row[field]):
            lesion_data[field] = bool(row[field])
    
    # 数值字段
    if 'length_mm' in row and not pd.isna(row['length_mm']):
        lesion_data['length_mm'] = float(row['length_mm'])
    
    return lesion_data


def process_excel_file(excel_path, output_path=None):
    """处理Excel文件并计算评分"""
    
    print(f"🏥 冠脉病变严重程度评分系统")
    print(f"📊 处理文件: {excel_path}")
    print("=" * 80)
    print()
    
    try:
        # 读取Excel文件
        patients = read_excel_file(excel_path)
        print(f"✓ 成功导入 {len(patients)} 名患者的数据")
        print()
        
        # 初始化计算器
        calculator = CoronaryScoreCalculator()
        
        # 存储所有结果
        all_results = []
        
        # 处理每个患者
        for i, patient in enumerate(patients, 1):
            print(f"患者 {i}: {patient['patient_id']}")
            print("-" * 50)
            
            # 基本信息
            print(f"基本信息: {patient['age']}岁 {patient['gender']}")
            
            clinical_info = []
            if patient.get('diabetes'):
                clinical_info.append('糖尿病')
            if patient.get('hypertension'):
                clinical_info.append('高血压')
            if patient.get('hyperlipidemia'):
                clinical_info.append('高脂血症')
            if patient.get('smoking'):
                clinical_info.append('吸烟')
            
            if clinical_info:
                print(f"合并症: {', '.join(clinical_info)}")
            
            if 'ejection_fraction' in patient:
                print(f"射血分数: {patient['ejection_fraction']}%")
            
            print(f"病变数量: {len(patient['lesions'])}")
            print()
            
            # 病变详情
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
                    if lesion.get('thrombus_present'):
                        features.append("血栓")
                    if lesion.get('is_ostial'):
                        features.append("开口")
                    if lesion.get('is_tortuous'):
                        features.append("迂曲")
                    
                    feature_str = f" ({', '.join(features)})" if features else ""
                    length_str = f" {lesion.get('length_mm', '')}mm" if lesion.get('length_mm') else ""
                    
                    print(f"  {j}. {lesion['vessel']} {lesion['stenosis_percent']}% "
                          f"({lesion['location']}){length_str}{feature_str}")
                print()
            
            # 计算各种评分
            syntax_result = calculator.calculate_syntax_score(patient)
            cadrads_result = calculator.calculate_cadrads_score(patient)
            gensini_result = calculator.calculate_gensini_score(patient)
            
            print("📊 评分结果:")
            print(f"SYNTAX评分: {syntax_result['total_score']} ({syntax_result['risk_category']})")
            print(f"  → {syntax_result['risk_description']}")
            
            print(f"CAD-RADS评分: {cadrads_result['overall_grade']}级 - {cadrads_result['description']}")
            print(f"  → {cadrads_result['recommendation']}")
            
            print(f"Gensini评分: {gensini_result['total_score']} ({gensini_result['severity_grade']})")
            print(f"  → {gensini_result['severity_description']}")
            
            # 综合建议
            print()
            print("🎯 综合评估:")
            if syntax_result['risk_category'] == 'high' or cadrads_result['overall_grade'] >= 4:
                print("  ⚠️  高风险病例，建议心脏团队讨论治疗策略")
            elif gensini_result['severity_grade'] in ['severe', 'critical']:
                print("  ⚠️  病变较重，需要积极治疗和密切随访")
            else:
                print("  ✓ 可考虑药物治疗或微创介入治疗")
            
            # 保存结果
            patient_result = {
                'patient_info': patient,
                'syntax_score': syntax_result,
                'cadrads_score': cadrads_result,
                'gensini_score': gensini_result
            }
            all_results.append(patient_result)
            
            print()
            print("=" * 80)
            print()
        
        # 导出结果
        if output_path:
            output_file = Path(output_path)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
            print(f"✓ 结果已保存到: {output_path}")
        
        print("✅ 所有患者处理完成！")
        return True
        
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='冠脉病变严重程度评分 - Excel处理工具')
    parser.add_argument('input_file', help='输入的Excel文件路径')
    parser.add_argument('-o', '--output', help='输出JSON结果文件路径')
    
    args = parser.parse_args()
    
    if not Path(args.input_file).exists():
        print(f"❌ 文件不存在: {args.input_file}")
        return
    
    # 处理文件
    success = process_excel_file(args.input_file, args.output)
    
    if success:
        print("\n🎉 处理成功！")
    else:
        print("\n❌ 处理失败！")


if __name__ == "__main__":
    # 如果没有命令行参数，使用示例文件
    if len(sys.argv) == 1:
        # 使用示例文件演示
        example_file = "data/sample_patients.xlsx"
        if Path(example_file).exists():
            print("使用示例文件演示...")
            process_excel_file(example_file, "data/results.json")
        else:
            print("示例文件不存在，请先运行 excel_demo.py 创建示例文件")
    else:
        main()