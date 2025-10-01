"""
测试SYNTAX评分计算器
"""

import pytest
from coronary_score.models.patient import (
    PatientData, Lesion, Gender, VesselType, StenosisLocation
)
from coronary_score.calculators.syntax_calculator import SyntaxCalculator


class TestSyntaxCalculator:
    """测试SYNTAX评分计算器"""
    
    def setup_method(self):
        """测试准备"""
        self.calculator = SyntaxCalculator()
    
    def test_empty_lesions(self):
        """测试无病变患者"""
        patient = PatientData(age=65, gender=Gender.MALE)
        result = self.calculator.calculate(patient)
        
        assert result['total_score'] == 0.0
        assert result['anatomical_score'] == 0.0
        assert result['risk_category'] == 'low'
    
    def test_single_simple_lesion(self):
        """测试单个简单病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # LAD近段75%狭窄
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        # LAD近段权重3.5 * 狭窄系数1.5 = 5.25
        expected_score = 3.5 * 1.5
        assert result['total_score'] == expected_score
        assert result['risk_category'] == 'low'  # <22分
    
    def test_left_main_lesion(self):
        """测试左主干病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # 左主干80%狭窄
        lesion = Lesion(
            vessel=VesselType.LM,
            stenosis_percent=80.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        # 左主干权重5.0 * 狭窄系数1.5 = 7.5
        expected_score = 5.0 * 1.5
        assert result['total_score'] == expected_score
        assert result['risk_category'] == 'low'
    
    def test_complete_occlusion(self):
        """测试完全闭塞"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # RCA完全闭塞
        lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=100.0,
            location=StenosisLocation.PROXIMAL,
            is_cto=True
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        # RCA近段权重3.5 * 闭塞系数5.0 + CTO复杂性5.0 = 22.5
        expected_score = 3.5 * 5.0 + 5.0
        assert result['total_score'] == expected_score
        assert result['risk_category'] == 'intermediate'  # 22-32分
    
    def test_bifurcation_lesion(self):
        """测试分叉病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # LAD近段分叉病变
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL,
            is_bifurcation=True
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        # LAD近段权重3.5 * 狭窄系数2.0 + 分叉复杂性1.0 = 8.0
        expected_score = 3.5 * 2.0 + 1.0
        assert result['total_score'] == expected_score
        assert result['risk_category'] == 'low'
    
    def test_multiple_lesions(self):
        """测试多个病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # LAD近段75%狭窄
        lad_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        
        # LCX近段90%狭窄，钙化
        lcx_lesion = Lesion(
            vessel=VesselType.LCX,
            stenosis_percent=90.0,
            location=StenosisLocation.PROXIMAL,
            is_calcified=True
        )
        
        # RCA中段60%狭窄
        rca_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=60.0,
            location=StenosisLocation.MID
        )
        
        patient.add_lesion(lad_lesion)
        patient.add_lesion(lcx_lesion)
        patient.add_lesion(rca_lesion)
        
        result = self.calculator.calculate(patient)
        
        # LAD: 3.5 * 1.5 = 5.25
        # LCX: 3.5 * 2.0 + 2.0(钙化) = 9.0
        # RCA: 1.0 * 1.0 = 1.0
        # 总计: 15.25
        expected_score = 5.25 + 9.0 + 1.0
        assert result['total_score'] == expected_score
        assert result['risk_category'] == 'low'
    
    def test_high_risk_case(self):
        """测试高风险病例"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # 左主干分叉病变
        lm_lesion = Lesion(
            vessel=VesselType.LM,
            stenosis_percent=80.0,
            location=StenosisLocation.PROXIMAL,
            is_bifurcation=True
        )
        
        # LAD中段CTO
        lad_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=100.0,
            location=StenosisLocation.MID,
            is_cto=True
        )
        
        # LCX近段复杂病变
        lcx_lesion = Lesion(
            vessel=VesselType.LCX,
            stenosis_percent=95.0,
            location=StenosisLocation.PROXIMAL,
            is_calcified=True,
            is_tortuous=True,
            length_mm=30.0  # 弥漫性病变
        )
        
        patient.add_lesion(lm_lesion)
        patient.add_lesion(lad_lesion)
        patient.add_lesion(lcx_lesion)
        
        result = self.calculator.calculate(patient)
        
        # 应该是高风险评分 (>32分)
        assert result['total_score'] > 32
        assert result['risk_category'] == 'high'
    
    def test_clinical_score_calculation(self):
        """测试临床评分计算"""
        # 高龄女性糖尿病患者
        patient = PatientData(
            age=75,
            gender=Gender.FEMALE,
            diabetes=True,
            creatinine_mg_dl=2.5,
            ejection_fraction=35.0
        )
        
        # 添加简单病变用于计算
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=50.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        # 验证临床评分不为零
        assert result['clinical_score'] > 0
        
        # SYNTAX II评分应该高于解剖学评分
        assert result['syntax_ii_score'] > result['anatomical_score']
    
    def test_detailed_report(self):
        """测试详细报告"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL,
            is_bifurcation=True
        )
        patient.add_lesion(lesion)
        
        report = self.calculator.get_detailed_report(patient)
        
        assert 'scores' in report
        assert 'lesion_details' in report
        assert 'recommendation' in report
        
        # 验证病变详情
        lesion_details = report['lesion_details']
        assert len(lesion_details) == 1
        assert lesion_details[0]['vessel'] == 'LAD'
        assert lesion_details[0]['stenosis_percent'] == 75.0
        assert lesion_details[0]['base_score'] > 0
        assert lesion_details[0]['complexity_score'] > 0
    
    def test_risk_categories(self):
        """测试风险分层"""
        # 测试低风险
        assert self.calculator._get_risk_category(15.0) == 'low'
        
        # 测试中等风险
        assert self.calculator._get_risk_category(25.0) == 'intermediate'
        
        # 测试高风险
        assert self.calculator._get_risk_category(35.0) == 'high'
        
        # 边界值测试
        assert self.calculator._get_risk_category(22.0) == 'low'
        assert self.calculator._get_risk_category(22.1) == 'intermediate'
        assert self.calculator._get_risk_category(32.0) == 'intermediate'
        assert self.calculator._get_risk_category(32.1) == 'high'
    
    def test_treatment_recommendation(self):
        """测试治疗建议"""
        # 低复杂性
        recommendation = self.calculator._get_treatment_recommendation(15.0)
        assert "PCI" in recommendation
        
        # 中等复杂性
        recommendation = self.calculator._get_treatment_recommendation(25.0)
        assert "心脏团队" in recommendation
        
        # 高复杂性
        recommendation = self.calculator._get_treatment_recommendation(35.0)
        assert "CABG" in recommendation