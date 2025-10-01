"""
测试CAD-RADS评分计算器
"""

import pytest
from coronary_score.models.patient import (
    PatientData, Lesion, Gender, VesselType, StenosisLocation
)
from coronary_score.calculators.cad_rads_calculator import CadRadsCalculator


class TestCadRadsCalculator:
    """测试CAD-RADS评分计算器"""
    
    def setup_method(self):
        """测试准备"""
        self.calculator = CadRadsCalculator()
    
    def test_empty_lesions(self):
        """测试无病变患者"""
        patient = PatientData(age=65, gender=Gender.MALE)
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 0
        assert result['max_stenosis'] == 0
        assert result['vessel_grades'] == {}
        assert result['dominant_vessel'] is None
    
    def test_stenosis_to_grade_conversion(self):
        """测试狭窄程度到等级的转换"""
        assert self.calculator._stenosis_to_grade(0) == 0
        assert self.calculator._stenosis_to_grade(10) == 1
        assert self.calculator._stenosis_to_grade(30) == 2
        assert self.calculator._stenosis_to_grade(60) == 3
        assert self.calculator._stenosis_to_grade(80) == 4
        assert self.calculator._stenosis_to_grade(100) == 5
    
    def test_grade_1_lesion(self):
        """测试1级病变(1-24%狭窄)"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=15.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 1
        assert result['max_stenosis'] == 15.0
        assert result['vessel_grades']['LAD'] == 1
    
    def test_grade_2_lesion(self):
        """测试2级病变(25-49%狭窄)"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=35.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 2
        assert result['max_stenosis'] == 35.0
        assert result['vessel_grades']['RCA'] == 2
    
    def test_grade_3_lesion(self):
        """测试3级病变(50-69%狭窄)"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.LCX,
            stenosis_percent=60.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 3
        assert result['max_stenosis'] == 60.0
        assert result['vessel_grades']['LCX'] == 3
    
    def test_grade_4_lesion(self):
        """测试4级病变(70-99%狭窄)"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 4
        assert result['max_stenosis'] == 85.0
        assert result['vessel_grades']['LAD'] == 4
    
    def test_grade_5_lesion(self):
        """测试5级病变(100%狭窄)"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=100.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        result = self.calculator.calculate(patient)
        
        assert result['overall_grade'] == 5
        assert result['max_stenosis'] == 100.0
        assert result['vessel_grades']['RCA'] == 5
    
    def test_multiple_vessels_different_grades(self):
        """测试多血管不同等级病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # LAD轻度病变
        lad_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=30.0,
            location=StenosisLocation.PROXIMAL
        )
        
        # RCA重度病变
        rca_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL
        )
        
        # LCX中度病变
        lcx_lesion = Lesion(
            vessel=VesselType.LCX,
            stenosis_percent=55.0,
            location=StenosisLocation.PROXIMAL
        )
        
        patient.add_lesion(lad_lesion)
        patient.add_lesion(rca_lesion)
        patient.add_lesion(lcx_lesion)
        
        result = self.calculator.calculate(patient)
        
        # 总体等级应该是最高的等级
        assert result['overall_grade'] == 4  # RCA的4级
        assert result['max_stenosis'] == 85.0
        assert result['vessel_grades']['LAD'] == 2
        assert result['vessel_grades']['RCA'] == 4
        assert result['vessel_grades']['LCX'] == 3
    
    def test_same_vessel_multiple_lesions(self):
        """测试同一血管多个病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # LAD近段中度狭窄
        lad_proximal = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=60.0,
            location=StenosisLocation.PROXIMAL
        )
        
        # LAD中段重度狭窄
        lad_mid = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=80.0,
            location=StenosisLocation.MID
        )
        
        patient.add_lesion(lad_proximal)
        patient.add_lesion(lad_mid)
        
        result = self.calculator.calculate(patient)
        
        # 应该取最高等级
        assert result['overall_grade'] == 4  # 80%狭窄对应4级
        assert result['vessel_grades']['LAD'] == 4
    
    def test_dominant_vessel_identification(self):
        """测试主要病变血管识别"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # 左主干重度病变(权重最高)
        lm_lesion = Lesion(
            vessel=VesselType.LM,
            stenosis_percent=70.0,
            location=StenosisLocation.PROXIMAL
        )
        
        # LAD更重的病变
        lad_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=90.0,
            location=StenosisLocation.PROXIMAL
        )
        
        patient.add_lesion(lm_lesion)
        patient.add_lesion(lad_lesion)
        
        result = self.calculator.calculate(patient)
        
        # 左主干权重高，应该是主要病变血管
        assert result['dominant_vessel'] == 'LM'
    
    def test_recommendations(self):
        """测试治疗建议"""
        # 测试不同等级的建议
        assert "无冠脉病变" in self.calculator._get_recommendation(0)
        assert "生活方式干预" in self.calculator._get_recommendation(1)
        assert "药物治疗" in self.calculator._get_recommendation(2)
        assert "功能学检查" in self.calculator._get_recommendation(3)
        assert "血管造影" in self.calculator._get_recommendation(4)
        assert "血管造影" in self.calculator._get_recommendation(5)
    
    def test_follow_up_recommendations(self):
        """测试随访建议"""
        # 测试不同等级的随访建议
        assert "5-10年" in self.calculator._get_follow_up_recommendation(0)
        assert "3-5年" in self.calculator._get_follow_up_recommendation(1)
        assert "2-3年" in self.calculator._get_follow_up_recommendation(2)
        assert "1-2年" in self.calculator._get_follow_up_recommendation(3)
        assert "血运重建" in self.calculator._get_follow_up_recommendation(4)
        assert "血运重建" in self.calculator._get_follow_up_recommendation(5)
    
    def test_detailed_report(self):
        """测试详细报告"""
        patient = PatientData(
            age=70,
            gender=Gender.MALE,
            diabetes=True,
            hypertension=True
        )
        
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        report = self.calculator.get_detailed_report(patient)
        
        assert 'cadrads_result' in report
        assert 'lesion_analysis' in report
        assert 'risk_assessment' in report
        assert 'clinical_significance' in report
        assert 'quality_measures' in report
        
        # 验证病变分析
        lesion_analysis = report['lesion_analysis']
        assert len(lesion_analysis) == 1
        assert lesion_analysis[0]['vessel'] == 'LAD'
        assert lesion_analysis[0]['grade'] == 4
    
    def test_risk_assessment(self):
        """测试风险评估"""
        # 高龄男性糖尿病患者
        patient = PatientData(
            age=75,
            gender=Gender.MALE,
            diabetes=True,
            hypertension=True
        )
        
        # 重度病变
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL
        )
        patient.add_lesion(lesion)
        
        risk_level = self.calculator._assess_risk_level(4, patient)
        
        # 应该是高风险
        assert risk_level == "high"
    
    def test_clinical_significance(self):
        """测试临床意义"""
        significance = self.calculator._get_clinical_significance(4)
        assert "心肌缺血" in significance
        assert "血运重建" in significance