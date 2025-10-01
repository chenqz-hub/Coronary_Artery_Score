"""
CAD-RADS评分计算器

CAD-RADS (Coronary Artery Disease Reporting and Data System) 是一个标准化的
冠脉CT评分系统，用于评估冠脉狭窄的严重程度。
"""

from typing import Dict, List, Optional, Tuple
from ..models.patient import PatientData, Lesion, VesselType


class CadRadsCalculator:
    """CAD-RADS评分计算器"""
    
    # CAD-RADS评分标准
    CADRADS_GRADES = {
        0: {"range": (0, 0), "description": "无冠脉病变", "stenosis": "0%"},
        1: {"range": (1, 24), "description": "轻微冠脉病变", "stenosis": "1-24%"},
        2: {"range": (25, 49), "description": "轻度冠脉病变", "stenosis": "25-49%"},
        3: {"range": (50, 69), "description": "中度冠脉病变", "stenosis": "50-69%"},
        4: {"range": (70, 99), "description": "重度冠脉病变", "stenosis": "70-99%"},
        5: {"range": (100, 100), "description": "完全闭塞", "stenosis": "100%"}
    }
    
    # 血管重要性权重
    VESSEL_IMPORTANCE = {
        VesselType.LM: 5,    # 左主干最重要
        VesselType.LAD: 4,   # 左前降支
        VesselType.LCX: 3,   # 左回旋支
        VesselType.RCA: 3,   # 右冠脉
        VesselType.OM: 2,    # 钝缘支
        VesselType.D: 2,     # 对角支
        VesselType.PDA: 2,   # 后降支
        VesselType.PLV: 1,   # 左室后支
    }
    
    def __init__(self):
        """初始化CAD-RADS计算器"""
        pass
    
    def calculate(self, patient_data: PatientData) -> Dict[str, any]:
        """
        计算CAD-RADS评分
        
        Args:
            patient_data: 患者数据
            
        Returns:
            包含CAD-RADS评分信息的字典
        """
        if not patient_data.lesions:
            return {
                'overall_grade': 0,
                'max_stenosis': 0,
                'vessel_grades': {},
                'dominant_vessel': None,
                'recommendation': self._get_recommendation(0),
                'follow_up': self._get_follow_up_recommendation(0)
            }
        
        # 计算每个血管的最高评分
        vessel_grades = self._calculate_vessel_grades(patient_data.lesions)
        
        # 确定总体评分(取最高分)
        overall_grade = max(vessel_grades.values()) if vessel_grades else 0
        
        # 找到最大狭窄程度
        max_stenosis = max(lesion.stenosis_percent for lesion in patient_data.lesions)
        
        # 确定主要病变血管
        dominant_vessel = self._find_dominant_vessel(patient_data.lesions)
        
        return {
            'overall_grade': overall_grade,
            'max_stenosis': max_stenosis,
            'vessel_grades': vessel_grades,
            'dominant_vessel': dominant_vessel.value if dominant_vessel else None,
            'recommendation': self._get_recommendation(overall_grade),
            'follow_up': self._get_follow_up_recommendation(overall_grade)
        }
    
    def _calculate_vessel_grades(self, lesions: List[Lesion]) -> Dict[str, int]:
        """计算每个血管的CAD-RADS评分"""
        vessel_grades = {}
        
        # 按血管分组
        vessel_lesions = {}
        for lesion in lesions:
            vessel = lesion.vessel.value
            if vessel not in vessel_lesions:
                vessel_lesions[vessel] = []
            vessel_lesions[vessel].append(lesion)
        
        # 计算每个血管的最高评分
        for vessel, lesions_list in vessel_lesions.items():
            max_stenosis = max(lesion.stenosis_percent for lesion in lesions_list)
            vessel_grades[vessel] = self._stenosis_to_grade(max_stenosis)
        
        return vessel_grades
    
    def _stenosis_to_grade(self, stenosis_percent: float) -> int:
        """将狭窄百分比转换为CAD-RADS评分"""
        for grade, info in self.CADRADS_GRADES.items():
            min_stenosis, max_stenosis = info["range"]
            if min_stenosis <= stenosis_percent <= max_stenosis:
                return grade
        return 0
    
    def _find_dominant_vessel(self, lesions: List[Lesion]) -> Optional[VesselType]:
        """找到主要病变血管"""
        if not lesions:
            return None
        
        vessel_scores = {}
        
        for lesion in lesions:
            vessel = lesion.vessel
            
            # 计算血管病变严重程度评分
            stenosis_score = lesion.stenosis_percent / 100
            importance_weight = self.VESSEL_IMPORTANCE.get(vessel, 1)
            
            vessel_score = stenosis_score * importance_weight
            
            if vessel not in vessel_scores:
                vessel_scores[vessel] = 0
            vessel_scores[vessel] += vessel_score
        
        # 返回评分最高的血管
        return max(vessel_scores, key=vessel_scores.get) if vessel_scores else None
    
    def _get_recommendation(self, grade: int) -> str:
        """根据CAD-RADS评分给出建议"""
        recommendations = {
            0: "无冠脉病变，无需特殊处理",
            1: "轻微冠脉病变，生活方式干预，控制危险因素",
            2: "轻度冠脉病变，药物治疗，控制危险因素",
            3: "中度冠脉病变，考虑功能学检查(如负荷试验)评估心肌缺血",
            4: "重度冠脉病变，建议血管造影评估，考虑血运重建",
            5: "完全闭塞，建议血管造影评估，考虑血运重建"
        }
        return recommendations.get(grade, "请咨询心血管专科医师")
    
    def _get_follow_up_recommendation(self, grade: int) -> str:
        """根据CAD-RADS评分给出随访建议"""
        follow_ups = {
            0: "5-10年复查冠脉CT(如有危险因素)",
            1: "3-5年复查冠脉CT",
            2: "2-3年复查冠脉CT或根据症状调整",
            3: "1-2年复查或根据功能学检查结果调整",
            4: "血运重建后按指南随访",
            5: "血运重建后按指南随访"
        }
        return follow_ups.get(grade, "请咨询心血管专科医师")
    
    def get_detailed_report(self, patient_data: PatientData) -> Dict:
        """获取详细的CAD-RADS报告"""
        result = self.calculate(patient_data)
        
        # 详细的病变分析
        lesion_analysis = []
        for lesion in patient_data.lesions:
            grade = self._stenosis_to_grade(lesion.stenosis_percent)
            lesion_analysis.append({
                'vessel': lesion.vessel.value,
                'stenosis_percent': lesion.stenosis_percent,
                'grade': grade,
                'description': self.CADRADS_GRADES[grade]['description'],
                'location': lesion.location.value if lesion.location else 'unknown'
            })
        
        # 风险分层
        risk_level = self._assess_risk_level(result['overall_grade'], patient_data)
        
        return {
            'cadrads_result': result,
            'lesion_analysis': lesion_analysis,
            'risk_assessment': risk_level,
            'clinical_significance': self._get_clinical_significance(result['overall_grade']),
            'quality_measures': self._assess_image_quality_requirements(result['overall_grade'])
        }
    
    def _assess_risk_level(self, grade: int, patient_data: PatientData) -> str:
        """评估患者风险水平"""
        base_risk = "low"
        
        if grade >= 4:
            base_risk = "high"
        elif grade == 3:
            base_risk = "intermediate"
        elif grade <= 2:
            base_risk = "low"
        
        # 考虑临床因素调整风险
        risk_factors = 0
        if patient_data.diabetes:
            risk_factors += 1
        if patient_data.hypertension:
            risk_factors += 1
        if patient_data.age >= 65:
            risk_factors += 1
        if patient_data.gender.value == 'male':
            risk_factors += 1
        
        if risk_factors >= 3 and base_risk == "low":
            base_risk = "intermediate"
        elif risk_factors >= 2 and base_risk == "intermediate":
            base_risk = "high"
        
        return base_risk
    
    def _get_clinical_significance(self, grade: int) -> str:
        """获取临床意义说明"""
        significance = {
            0: "无冠脉粥样硬化，心血管事件风险极低",
            1: "轻微冠脉粥样硬化，需要控制危险因素预防进展",
            2: "轻度冠脉狭窄，通常不引起心肌缺血，但需要积极药物治疗",
            3: "中度冠脉狭窄，可能引起心肌缺血，需要进一步功能学评估",
            4: "重度冠脉狭窄，很可能引起心肌缺血，通常需要血运重建",
            5: "完全闭塞，如果供血区域存活心肌，应考虑血运重建"
        }
        return significance.get(grade, "请专科医师进一步评估")
    
    def _assess_image_quality_requirements(self, grade: int) -> Dict:
        """评估影像质量要求"""
        if grade >= 3:
            return {
                'quality_requirement': 'high',
                'recommendation': '建议高质量CT扫描，必要时行冠脉造影确认',
                'additional_imaging': '考虑功能学检查评估心肌缺血'
            }
        elif grade >= 1:
            return {
                'quality_requirement': 'standard',
                'recommendation': '标准CT扫描质量可满足评估需求',
                'additional_imaging': '根据临床症状决定是否需要进一步检查'
            }
        else:
            return {
                'quality_requirement': 'standard',
                'recommendation': '标准CT扫描质量已足够',
                'additional_imaging': '无需额外影像学检查'
            }