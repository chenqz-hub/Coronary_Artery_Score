"""
测试患者数据模型
"""

import pytest
from datetime import datetime
from coronary_score.models.patient import (
    PatientData, Lesion, VesselSegment, Gender, VesselType, 
    StenosisLocation, LesionMorphology
)


class TestPatientData:
    """测试患者数据模型"""
    
    def test_create_basic_patient(self):
        """测试创建基本患者数据"""
        patient = PatientData(
            age=65,
            gender=Gender.MALE
        )
        
        assert patient.age == 65
        assert patient.gender == Gender.MALE
        assert patient.diabetes == False
        assert len(patient.lesions) == 0
    
    def test_create_patient_with_clinical_info(self):
        """测试创建包含临床信息的患者数据"""
        patient = PatientData(
            patient_id="P001",
            age=58,
            gender=Gender.FEMALE,
            diabetes=True,
            hypertension=True,
            ejection_fraction=55.0,
            creatinine_mg_dl=1.2
        )
        
        assert patient.patient_id == "P001"
        assert patient.diabetes == True
        assert patient.hypertension == True
        assert patient.ejection_fraction == 55.0
        assert patient.creatinine_mg_dl == 1.2
    
    def test_age_validation(self):
        """测试年龄验证"""
        # 正常年龄
        patient = PatientData(age=65, gender=Gender.MALE)
        assert patient.age == 65
        
        # 边界值测试
        with pytest.raises(ValueError):
            PatientData(age=-1, gender=Gender.MALE)
        
        with pytest.raises(ValueError):
            PatientData(age=151, gender=Gender.MALE)
    
    def test_ejection_fraction_validation(self):
        """测试射血分数验证"""
        # 正常射血分数
        patient = PatientData(
            age=65, 
            gender=Gender.MALE,
            ejection_fraction=60.0
        )
        assert patient.ejection_fraction == 60.0
        
        # 边界值测试
        with pytest.raises(ValueError):
            PatientData(
                age=65,
                gender=Gender.MALE,
                ejection_fraction=-1.0
            )
        
        with pytest.raises(ValueError):
            PatientData(
                age=65,
                gender=Gender.MALE,
                ejection_fraction=101.0
            )
    
    def test_add_lesion(self):
        """测试添加病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        
        patient.add_lesion(lesion)
        assert len(patient.lesions) == 1
        assert patient.lesions[0].vessel == VesselType.LAD
    
    def test_get_lesions_by_vessel(self):
        """测试按血管类型获取病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # 添加多个病变
        lad_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        
        rca_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=60.0,
            location=StenosisLocation.MID
        )
        
        patient.add_lesion(lad_lesion)
        patient.add_lesion(rca_lesion)
        
        # 获取LAD病变
        lad_lesions = patient.get_lesions_by_vessel(VesselType.LAD)
        assert len(lad_lesions) == 1
        assert lad_lesions[0].vessel == VesselType.LAD
        
        # 获取RCA病变
        rca_lesions = patient.get_lesions_by_vessel(VesselType.RCA)
        assert len(rca_lesions) == 1
        assert rca_lesions[0].vessel == VesselType.RCA
    
    def test_get_significant_lesions(self):
        """测试获取显著狭窄病变"""
        patient = PatientData(age=65, gender=Gender.MALE)
        
        # 添加不同程度的病变
        mild_lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=30.0,
            location=StenosisLocation.PROXIMAL
        )
        
        significant_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=75.0,
            location=StenosisLocation.MID
        )
        
        patient.add_lesion(mild_lesion)
        patient.add_lesion(significant_lesion)
        
        # 默认阈值(50%)
        significant_lesions = patient.get_significant_lesions()
        assert len(significant_lesions) == 1
        assert significant_lesions[0].stenosis_percent == 75.0
        
        # 自定义阈值(70%)
        severe_lesions = patient.get_significant_lesions(threshold=70.0)
        assert len(severe_lesions) == 1
        assert severe_lesions[0].stenosis_percent == 75.0


class TestLesion:
    """测试病变数据模型"""
    
    def test_create_basic_lesion(self):
        """测试创建基本病变"""
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=75.0,
            location=StenosisLocation.PROXIMAL
        )
        
        assert lesion.vessel == VesselType.LAD
        assert lesion.stenosis_percent == 75.0
        assert lesion.location == StenosisLocation.PROXIMAL
        assert lesion.is_bifurcation == False
        assert lesion.is_cto == False
    
    def test_create_complex_lesion(self):
        """测试创建复杂病变"""
        lesion = Lesion(
            lesion_id="L001",
            vessel=VesselType.LM,
            stenosis_percent=85.0,
            location=StenosisLocation.PROXIMAL,
            length_mm=25.0,
            morphology=LesionMorphology.TYPE_C,
            is_bifurcation=True,
            is_calcified=True,
            is_tortuous=True
        )
        
        assert lesion.lesion_id == "L001"
        assert lesion.vessel == VesselType.LM
        assert lesion.length_mm == 25.0
        assert lesion.morphology == LesionMorphology.TYPE_C
        assert lesion.is_bifurcation == True
        assert lesion.is_calcified == True
        assert lesion.is_tortuous == True
    
    def test_stenosis_percent_validation(self):
        """测试狭窄百分比验证"""
        # 正常狭窄百分比
        lesion = Lesion(
            vessel=VesselType.LAD,
            stenosis_percent=50.0,
            location=StenosisLocation.PROXIMAL
        )
        assert lesion.stenosis_percent == 50.0
        
        # 边界值测试
        with pytest.raises(ValueError):
            Lesion(
                vessel=VesselType.LAD,
                stenosis_percent=-1.0,
                location=StenosisLocation.PROXIMAL
            )
        
        with pytest.raises(ValueError):
            Lesion(
                vessel=VesselType.LAD,
                stenosis_percent=101.0,
                location=StenosisLocation.PROXIMAL
            )
    
    def test_cto_lesion(self):
        """测试慢性完全闭塞病变"""
        cto_lesion = Lesion(
            vessel=VesselType.RCA,
            stenosis_percent=100.0,
            location=StenosisLocation.PROXIMAL,
            is_cto=True
        )
        
        assert cto_lesion.is_cto == True
        assert cto_lesion.stenosis_percent == 100.0


class TestVesselSegment:
    """测试血管节段模型"""
    
    def test_create_vessel_segment(self):
        """测试创建血管节段"""
        segment = VesselSegment(
            segment_id=6,
            vessel_type=VesselType.LAD,
            name="LAD近段",
            multiplication_factor=2.5
        )
        
        assert segment.segment_id == 6
        assert segment.vessel_type == VesselType.LAD
        assert segment.name == "LAD近段"
        assert segment.multiplication_factor == 2.5


class TestEnums:
    """测试枚举类型"""
    
    def test_gender_enum(self):
        """测试性别枚举"""
        assert Gender.MALE == "male"
        assert Gender.FEMALE == "female"
    
    def test_vessel_type_enum(self):
        """测试血管类型枚举"""
        assert VesselType.LAD == "LAD"
        assert VesselType.LCX == "LCX"
        assert VesselType.RCA == "RCA"
        assert VesselType.LM == "LM"
    
    def test_stenosis_location_enum(self):
        """测试狭窄位置枚举"""
        assert StenosisLocation.PROXIMAL == "proximal"
        assert StenosisLocation.MID == "mid"
        assert StenosisLocation.DISTAL == "distal"
    
    def test_lesion_morphology_enum(self):
        """测试病变形态枚举"""
        assert LesionMorphology.TYPE_A == "A"
        assert LesionMorphology.TYPE_B1 == "B1"
        assert LesionMorphology.TYPE_B2 == "B2"
        assert LesionMorphology.TYPE_C == "C"