"""
集成测试
"""

import pytest
import json
from pathlib import Path
from coronary_score import PatientData, Lesion, SyntaxCalculator, CadRadsCalculator, GensiniCalculator
from coronary_score.models.patient import Gender, VesselType, StenosisLocation
from coronary_score.data_io import DataImporter, DataExporter, create_sample_data


class TestIntegration:
    """集成测试"""
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 1. 创建患者数据
        patient = PatientData(
            patient_id="TEST001",
            age=65,
            gender=Gender.MALE,
            diabetes=True,
            hypertension=True,
            ejection_fraction=55.0
        )
        
        # 2. 添加病变
        lesions = [
            Lesion(
                lesion_id="L001",
                vessel=VesselType.LAD,
                stenosis_percent=75.0,
                location=StenosisLocation.PROXIMAL,
                is_bifurcation=True
            ),
            Lesion(
                lesion_id="L002",
                vessel=VesselType.RCA,
                stenosis_percent=85.0,
                location=StenosisLocation.PROXIMAL,
                is_calcified=True
            )
        ]
        
        for lesion in lesions:
            patient.add_lesion(lesion)
        
        # 3. 计算所有评分
        syntax_calc = SyntaxCalculator()
        cadrads_calc = CadRadsCalculator()
        gensini_calc = GensiniCalculator()
        
        syntax_result = syntax_calc.calculate(patient)
        cadrads_result = cadrads_calc.calculate(patient)
        gensini_result = gensini_calc.calculate(patient)
        
        # 4. 验证结果
        assert syntax_result['total_score'] > 0
        assert cadrads_result['overall_grade'] > 0
        assert gensini_result['total_score'] > 0
        
        # 5. 验证一致性
        # 重度病变应该在所有评分系统中都反映出来
        assert syntax_result['risk_category'] in ['low', 'intermediate', 'high']
        assert cadrads_result['overall_grade'] >= 4  # 70%以上狭窄
        assert gensini_result['severity_grade'] in ['mild', 'moderate', 'severe', 'critical']
    
    def test_data_import_export_cycle(self, tmp_path):
        """测试数据导入导出循环"""
        # 1. 创建示例数据
        original_patients = create_sample_data()
        
        # 2. 导出到JSON
        json_file = tmp_path / "test_patients.json"
        exporter = DataExporter()
        exporter.export_to_file(original_patients, json_file)
        
        # 3. 从JSON导入
        importer = DataImporter()
        imported_patients = importer.import_from_file(json_file)
        
        # 4. 验证数据完整性
        assert len(imported_patients) == len(original_patients)
        
        for orig, imported in zip(original_patients, imported_patients):
            assert orig.patient_id == imported.patient_id
            assert orig.age == imported.age
            assert orig.gender == imported.gender
            assert len(orig.lesions) == len(imported.lesions)
    
    def test_calculator_consistency(self):
        """测试计算器一致性"""
        # 创建标准测试用例
        patient = PatientData(
            age=60,
            gender=Gender.MALE,
            diabetes=False,
            hypertension=False
        )
        
        # 左主干重度病变
        lm_lesion = Lesion(
            vessel=VesselType.LM,
            stenosis_percent=80.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lm_lesion)
        
        # 所有计算器都应该识别为高风险
        syntax_calc = SyntaxCalculator()
        cadrads_calc = CadRadsCalculator()
        gensini_calc = GensiniCalculator()
        
        syntax_result = syntax_calc.calculate(patient)
        cadrads_result = cadrads_calc.calculate(patient)
        gensini_result = gensini_calc.calculate(patient)
        
        # 左主干病变应该在所有评分中都体现出严重性
        assert syntax_result['total_score'] > 5  # 左主干权重高
        assert cadrads_result['overall_grade'] == 4  # 80%狭窄
        assert gensini_result['total_score'] > 10  # Gensini评分中左主干权重高
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 1. 无病变患者
        normal_patient = PatientData(age=50, gender=Gender.FEMALE)
        
        syntax_calc = SyntaxCalculator()
        result = syntax_calc.calculate(normal_patient)
        assert result['total_score'] == 0.0
        assert result['risk_category'] == 'low'
        
        # 2. 轻微病变患者
        mild_patient = PatientData(age=50, gender=Gender.FEMALE)
        mild_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=30.0,
            location=StenosisLocation.DISTAL
        )
        mild_patient.add_lesion(mild_lesion)
        
        # SYNTAX只计算≥50%的病变
        result = syntax_calc.calculate(mild_patient)
        assert result['total_score'] == 0.0
        
        # CAD-RADS会计算所有病变
        cadrads_calc = CadRadsCalculator()
        cadrads_result = cadrads_calc.calculate(mild_patient)
        assert cadrads_result['overall_grade'] == 2
        
        # 3. 完全闭塞患者
        cto_patient = PatientData(age=70, gender=Gender.MALE)
        cto_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=100.0,
            location=StenosisLocation.PROXIMAL,
            is_cto=True
        )
        cto_patient.add_lesion(cto_lesion)
        
        result = syntax_calc.calculate(cto_patient)
        # CTO应该有额外的复杂性评分
        assert result['total_score'] > 10
    
    def test_multi_calculator_report(self):
        """测试多计算器综合报告"""
        patient = PatientData(
            patient_id="MULTI001",
            age=68,
            gender=Gender.MALE,
            diabetes=True,
            hypertension=True,
            ejection_fraction=45.0
        )
        
        # 复杂多支病变
        lesions = [
            Lesion(
                vessel=VesselType.LAD,
                stenosis_percent=90.0,
                location=StenosisLocation.PROXIMAL,
                is_bifurcation=True,
                is_calcified=True
            ),
            Lesion(
                vessel=VesselType.LCX,
                stenosis_percent=75.0,
                location=StenosisLocation.PROXIMAL,
                length_mm=25.0
            ),
            Lesion(
                vessel=VesselType.RCA,
                stenosis_percent=100.0,
                location=StenosisLocation.MID,
                is_cto=True
            )
        ]
        
        for lesion in lesions:
            patient.add_lesion(lesion)
        
        # 生成所有评分的详细报告
        syntax_calc = SyntaxCalculator()
        cadrads_calc = CadRadsCalculator()
        gensini_calc = GensiniCalculator()
        
        syntax_report = syntax_calc.get_detailed_report(patient)
        cadrads_report = cadrads_calc.get_detailed_report(patient)
        gensini_report = gensini_calc.get_detailed_report(patient)
        
        # 验证报告完整性
        assert 'scores' in syntax_report
        assert 'lesion_details' in syntax_report
        assert 'recommendation' in syntax_report
        
        assert 'cadrads_result' in cadrads_report
        assert 'lesion_analysis' in cadrads_report
        
        assert 'gensini_result' in gensini_report
        assert 'risk_assessment' in gensini_report
        
        # 验证高复杂性病例的识别
        assert syntax_report['scores']['risk_category'] == 'high'
        assert cadrads_report['cadrads_result']['overall_grade'] >= 4
        assert gensini_report['gensini_result']['severity_grade'] in ['severe', 'critical']