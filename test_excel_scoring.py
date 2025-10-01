"""
Excel数据评分演示脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from coronary_score.data_io import DataImporter
from coronary_score.calculators import SyntaxCalculator, CadRadsCalculator, GensiniCalculator


def process_excel_file(excel_path):
    """处理Excel文件并计算评分"""
    
    print(f"正在处理Excel文件: {excel_path}")
    print("=" * 50)
    
    try:
        # 1. 导入Excel数据
        importer = DataImporter()
        patients = importer.import_from_file(excel_path)
        
        print(f"✓ 成功导入 {len(patients)} 名患者的数据")
        print()
        
        # 2. 初始化计算器
        syntax_calc = SyntaxCalculator()
        cadrads_calc = CadRadsCalculator()
        gensini_calc = GensiniCalculator()
        
        # 3. 对每个患者计算评分
        for i, patient in enumerate(patients, 1):
            print(f"患者 {i}: {patient.patient_id or f'Patient_{i}'}")
            print("-" * 30)
            print(f"年龄: {patient.age}岁, 性别: {patient.gender.value}")
            print(f"糖尿病: {'是' if patient.diabetes else '否'}")
            print(f"高血压: {'是' if patient.hypertension else '否'}")
            if patient.ejection_fraction:
                print(f"射血分数: {patient.ejection_fraction}%")
            print(f"病变数量: {len(patient.lesions)}")
            print()
            
            # 显示病变详情
            if patient.lesions:
                print("病变详情:")
                for j, lesion in enumerate(patient.lesions, 1):
                    features = []
                    if lesion.is_bifurcation:
                        features.append("分叉")
                    if lesion.is_calcified:
                        features.append("钙化")
                    if lesion.is_cto:
                        features.append("CTO")
                    if lesion.thrombus_present:
                        features.append("血栓")
                    
                    feature_str = f" ({', '.join(features)})" if features else ""
                    print(f"  {j}. {lesion.vessel.value} {lesion.stenosis_percent}% "
                          f"({lesion.location.value}){feature_str}")
                print()
            
            # 计算SYNTAX评分
            try:
                syntax_result = syntax_calc.calculate(patient)
                print(f"SYNTAX评分: {syntax_result['total_score']:.1f} "
                      f"({syntax_result['risk_category']}风险)")
                
                if syntax_result['risk_category'] == 'low':
                    print("  → 建议: 适合PCI治疗")
                elif syntax_result['risk_category'] == 'intermediate':
                    print("  → 建议: PCI和CABG均可考虑，建议心脏团队讨论")
                else:
                    print("  → 建议: 优先考虑CABG治疗")
            except Exception as e:
                print(f"SYNTAX评分计算失败: {e}")
            
            # 计算CAD-RADS评分
            try:
                cadrads_result = cadrads_calc.calculate(patient)
                print(f"CAD-RADS评分: {cadrads_result['overall_grade']}级")
                print(f"  → 建议: {cadrads_result['recommendation']}")
            except Exception as e:
                print(f"CAD-RADS评分计算失败: {e}")
            
            # 计算Gensini评分
            try:
                gensini_result = gensini_calc.calculate(patient)
                print(f"Gensini评分: {gensini_result['total_score']:.1f} "
                      f"({gensini_result['severity_grade']})")
                
                if gensini_result['severity_grade'] in ['severe', 'critical']:
                    print("  → 注意: 病变较重，需要积极治疗")
            except Exception as e:
                print(f"Gensini评分计算失败: {e}")
            
            print()
            print("=" * 50)
            print()
    
    except Exception as e:
        print(f"处理Excel文件时发生错误: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("冠脉病变严重程度评分系统 - Excel文件处理演示")
    print("=" * 60)
    print()
    
    # 使用示例Excel文件
    excel_file = "data/excel_template.xlsx"
    
    if os.path.exists(excel_file):
        success = process_excel_file(excel_file)
        
        if success:
            print("✓ Excel文件处理完成！")
            print()
            print("📋 如何使用您自己的Excel文件:")
            print("1. 参考 'data/excel_template.xlsx' 的格式")
            print("2. 确保包含必需字段:")
            print("   - 患者信息: patient_id, age, gender 等")
            print("   - 病变信息: vessel, stenosis_percent, location 等")
            print("3. 运行脚本处理您的数据")
            print()
            print("📊 支持的Excel格式:")
            print("- 单工作表: 患者和病变信息在同一表中")
            print("- 双工作表: 'patients'表 + 'lesions'表")
        else:
            print("❌ Excel文件处理失败")
    else:
        print(f"❌ 找不到示例文件: {excel_file}")
        print("请先运行 create_excel_template.py 创建模板")


if __name__ == "__main__":
    main()