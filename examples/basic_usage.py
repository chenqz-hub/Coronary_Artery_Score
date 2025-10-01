"""
基本使用示例

演示如何使用冠脉病变严重程度评分系统。
"""

from coronary_score import (
    PatientData, 
    Lesion, 
    SyntaxCalculator, 
    CadRadsCalculator, 
    GensiniCalculator
)
from coronary_score.models.patient import Gender, VesselType, StenosisLocation


def example_1_basic_usage():
    """示例1: 基本使用"""
    print("=== 示例1: 基本使用 ===")
    
    # 创建患者数据
    patient = PatientData(
        patient_id="P001",
        age=65,
        gender=Gender.MALE,
        diabetes=True,
        hypertension=True
    )
    
    # 添加病变
    lesion = Lesion(
        vessel=VesselType.LAD,
        stenosis_percent=75.0,
        location=StenosisLocation.PROXIMAL
    )
    patient.add_lesion(lesion)
    
    # 计算SYNTAX评分
    syntax_calc = SyntaxCalculator()
    syntax_result = syntax_calc.calculate(patient)
    
    print(f"患者ID: {patient.patient_id}")
    print(f"SYNTAX评分: {syntax_result['total_score']}")
    print(f"风险分层: {syntax_result['risk_category']}")
    print()


def example_2_multiple_calculators():
    """示例2: 使用多个计算器"""
    print("=== 示例2: 使用多个计算器 ===")
    
    # 创建复杂病例
    patient = PatientData(
        patient_id="P002",
        age=58,
        gender=Gender.FEMALE,
        diabetes=False,
        hypertension=True,
        ejection_fraction=60.0
    )
    
    # 添加多个病变
    lesions = [
        Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL,
            is_bifurcation=True,
            is_calcified=True
        ),
        Lesion(
            vessel=VesselType.LCX,
            stenosis_percent=70.0,
            location=StenosisLocation.PROXIMAL,
            length_mm=20.0
        ),
        Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=60.0,
            location=StenosisLocation.MID
        )
    ]
    
    for lesion in lesions:
        patient.add_lesion(lesion)
    
    # 使用所有计算器
    syntax_calc = SyntaxCalculator()
    cadrads_calc = CadRadsCalculator()
    gensini_calc = GensiniCalculator()
    
    syntax_result = syntax_calc.calculate(patient)
    cadrads_result = cadrads_calc.calculate(patient)
    gensini_result = gensini_calc.calculate(patient)
    
    print(f"患者ID: {patient.patient_id}")
    print(f"病变数量: {len(patient.lesions)}")
    print()
    
    print("SYNTAX评分:")
    print(f"  总分: {syntax_result['total_score']}")
    print(f"  风险分层: {syntax_result['risk_category']}")
    print()
    
    print("CAD-RADS评分:")
    print(f"  总体等级: {cadrads_result['overall_grade']}")
    print(f"  最大狭窄: {cadrads_result['max_stenosis']}%")
    print(f"  主要病变血管: {cadrads_result['dominant_vessel']}")
    print()
    
    print("Gensini评分:")
    print(f"  总分: {gensini_result['total_score']}")
    print(f"  严重程度: {gensini_result['severity_grade']}")
    print()


def example_3_detailed_reports():
    """示例3: 获取详细报告"""
    print("=== 示例3: 获取详细报告 ===")
    
    # 创建高风险患者
    patient = PatientData(
        patient_id="P003",
        age=72,
        gender=Gender.MALE,
        diabetes=True,
        hypertension=True,
        ejection_fraction=40.0,
        creatinine_mg_dl=2.1
    )
    
    # 左主干病变
    lm_lesion = Lesion(
        vessel=VesselType.LM,
        stenosis_percent=80.0,
        location=StenosisLocation.PROXIMAL,
        is_bifurcation=True
    )
    
    # LAD慢性完全闭塞
    lad_cto = Lesion(
        vessel=VesselType.LAD,
        stenosis_percent=100.0,
        location=StenosisLocation.MID,
        is_cto=True
    )
    
    patient.add_lesion(lm_lesion)
    patient.add_lesion(lad_cto)
    
    # 获取SYNTAX详细报告
    syntax_calc = SyntaxCalculator()
    syntax_report = syntax_calc.get_detailed_report(patient)
    
    print(f"患者ID: {patient.patient_id}")
    print(f"年龄: {patient.age}岁")
    print(f"合并症: 糖尿病={patient.diabetes}, 高血压={patient.hypertension}")
    print(f"射血分数: {patient.ejection_fraction}%")
    print()
    
    print("SYNTAX详细报告:")
    scores = syntax_report['scores']
    print(f"  解剖学评分: {scores['anatomical_score']}")
    print(f"  临床评分: {scores['clinical_score']}")
    print(f"  SYNTAX II评分: {scores['syntax_ii_score']}")
    print(f"  风险分层: {scores['risk_category']}")
    print()
    
    print("病变详情:")
    for detail in syntax_report['lesion_details']:
        print(f"  病变{detail['lesion_index']}: {detail['vessel']} "
              f"{detail['stenosis_percent']}% "
              f"(基础分:{detail['base_score']}, "
              f"复杂性分:{detail['complexity_score']}, "
              f"总分:{detail['total_contribution']})")
    
    print()
    print(f"治疗建议: {syntax_report['recommendation']}")
    print()


def example_4_special_cases():
    """示例4: 特殊病例"""
    print("=== 示例4: 特殊病例 ===")
    
    # 年轻女性患者
    young_female = PatientData(
        patient_id="P004",
        age=35,
        gender=Gender.FEMALE,
        diabetes=False,
        hypertension=False,
        family_history=True  # 家族史阳性
    )
    
    # 单支重度病变
    severe_lesion = Lesion(
        vessel=VesselType.LAD,
        stenosis_percent=95.0,
        location=StenosisLocation.PROXIMAL,
        thrombus_present=True  # 存在血栓
    )
    young_female.add_lesion(severe_lesion)
    
    # 计算评分
    syntax_calc = SyntaxCalculator()
    cadrads_calc = CadRadsCalculator()
    
    syntax_result = syntax_calc.calculate(young_female)
    cadrads_result = cadrads_calc.calculate(young_female)
    
    print("年轻女性急性冠脉综合征:")
    print(f"  年龄: {young_female.age}岁")
    print(f"  性别: {young_female.gender.value}")
    print(f"  家族史: {'阳性' if young_female.family_history else '阴性'}")
    print()
    
    print("评分结果:")
    print(f"  SYNTAX评分: {syntax_result['total_score']} ({syntax_result['risk_category']})")
    print(f"  CAD-RADS评分: {cadrads_result['overall_grade']}")
    print()
    
    print("特殊考虑:")
    print("  - 年轻女性冠心病需要排除非典型病因")
    print("  - 血栓病变提示急性事件，需要紧急处理")
    print("  - 单支病变但位于LAD近段，预后影响较大")
    print()


def example_5_comparison():
    """示例5: 评分系统比较"""
    print("=== 示例5: 评分系统比较 ===")
    
    # 创建标准病例用于比较
    patient = PatientData(
        patient_id="COMP001",
        age=64,
        gender=Gender.MALE,
        diabetes=True
    )
    
    # 多支病变
    lesions = [
        Lesion(vessel=VesselType.LAD, stenosis_percent=80.0, location=StenosisLocation.PROXIMAL),
        Lesion(vessel=VesselType.LCX, stenosis_percent=70.0, location=StenosisLocation.PROXIMAL),
        Lesion(vessel=VesselType.RCA, stenosis_percent=90.0, location=StenosisLocation.PROXIMAL)
    ]
    
    for lesion in lesions:
        patient.add_lesion(lesion)
    
    # 计算所有评分
    syntax_calc = SyntaxCalculator()
    cadrads_calc = CadRadsCalculator()
    gensini_calc = GensiniCalculator()
    
    syntax_result = syntax_calc.calculate(patient)
    cadrads_result = cadrads_calc.calculate(patient)
    gensini_result = gensini_calc.calculate(patient)
    
    print("三支病变患者评分比较:")
    print()
    
    print("SYNTAX评分:")
    print(f"  侧重点: 介入治疗复杂性")
    print(f"  评分: {syntax_result['total_score']}")
    print(f"  风险: {syntax_result['risk_category']}")
    print(f"  适用: PCI vs CABG决策")
    print()
    
    print("CAD-RADS评分:")
    print(f"  侧重点: CT影像标准化报告")
    print(f"  等级: {cadrads_result['overall_grade']}")
    print(f"  建议: {cadrads_result['recommendation']}")
    print(f"  适用: 影像学诊断和随访")
    print()
    
    print("Gensini评分:")
    print(f"  侧重点: 解剖严重程度量化")
    print(f"  评分: {gensini_result['total_score']}")
    print(f"  严重程度: {gensini_result['severity_grade']}")
    print(f"  适用: 预后评估和风险分层")
    print()


def main():
    """运行所有示例"""
    print("冠脉病变严重程度评分系统 - 使用示例")
    print("=" * 50)
    print()
    
    example_1_basic_usage()
    example_2_multiple_calculators()
    example_3_detailed_reports()
    example_4_special_cases()
    example_5_comparison()
    
    print("示例演示完成!")


if __name__ == "__main__":
    main()