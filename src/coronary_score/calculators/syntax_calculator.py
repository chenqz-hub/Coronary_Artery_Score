"""
SYNTAX评分计算器

SYNTAX评分是一个客观量化的评分系统，用于评估复杂冠脉病变的严重程度。
该评分系统考虑了病变的数量、位置、复杂性等多个因素。
"""

import math
from typing import Dict, List, Optional, Tuple
from ..models.patient import PatientData, Lesion, VesselType
from ..utils.vessel_segments import VESSEL_SEGMENTS


class SyntaxCalculator:
    """SYNTAX评分计算器"""
    
    # 血管节段权重系数
    VESSEL_WEIGHTS = {
        # 左主干
        5: 5.0,  # LM
        
        # LAD系统
        6: 3.5,  # LAD近段
        7: 2.5,  # LAD中段  
        8: 1.0,  # LAD远段
        9: 1.0,  # 第一对角支
        10: 0.5, # 第二对角支
        
        # LCX系统
        11: 3.5, # LCX近段
        12: 1.0, # 第一钝缘支
        13: 1.0, # LCX中段
        14: 1.0, # LCX远段/LPL
        15: 0.5, # 第二钝缘支
        
        # RCA系统
        1: 3.5,  # RCA近段
        2: 1.0,  # RCA中段
        3: 1.0,  # RCA远段
        4: 1.0,  # 后降支
        16: 0.5, # 后侧支
    }
    
    # 病变复杂性评分
    COMPLEXITY_SCORES = {
        'bifurcation': 1,      # 分叉病变
        'ostial': 0.5,        # 开口病变
        'severe_calcification': 2,  # 重度钙化
        'thrombus': 1,         # 血栓
        'diffuse_disease': 1,  # 弥漫性病变
        'chronic_occlusion': 5,  # 慢性完全闭塞
        'tortuous': 1,         # 迂曲
    }
    
    def __init__(self):
        """初始化SYNTAX计算器"""
        self.vessel_segments = VESSEL_SEGMENTS
    
    def calculate(self, patient_data: PatientData) -> Dict[str, float]:
        """
        计算SYNTAX评分
        
        Args:
            patient_data: 患者数据
            
        Returns:
            包含各项评分的字典
        """
        if not patient_data.lesions:
            return {
                'total_score': 0.0,
                'anatomical_score': 0.0,
                'clinical_score': 0.0,
                'syntax_ii_score': 0.0,
                'risk_category': 'low'
            }
        
        # 计算解剖学评分
        anatomical_score = self._calculate_anatomical_score(patient_data.lesions)
        
        # 计算临床评分
        clinical_score = self._calculate_clinical_score(patient_data)
        
        # 计算SYNTAX II评分
        syntax_ii_score = self._calculate_syntax_ii_score(patient_data, anatomical_score)
        
        # 确定风险分层
        risk_category = self._get_risk_category(anatomical_score)
        
        return {
            'total_score': anatomical_score,
            'anatomical_score': anatomical_score,
            'clinical_score': clinical_score,
            'syntax_ii_score': syntax_ii_score,
            'risk_category': risk_category
        }
    
    def _calculate_anatomical_score(self, lesions: List[Lesion]) -> float:
        """计算解剖学评分"""
        total_score = 0.0
        
        for lesion in lesions:
            if lesion.stenosis_percent < 50:
                continue  # 只计算≥50%的狭窄
            
            # 基础评分
            base_score = self._get_base_score(lesion)
            
            # 复杂性评分
            complexity_score = self._get_complexity_score(lesion)
            
            # 病变总分
            lesion_score = base_score + complexity_score
            
            total_score += lesion_score
        
        return round(total_score, 1)
    
    def _get_base_score(self, lesion: Lesion) -> float:
        """获取病变基础评分"""
        # 根据病变位置确定节段ID
        segment_id = self._get_segment_id(lesion)
        
        # 获取节段权重
        weight = self.VESSEL_WEIGHTS.get(segment_id, 1.0)
        
        # 根据狭窄程度调整
        stenosis_factor = 1.0
        if lesion.stenosis_percent >= 99:
            stenosis_factor = 5.0  # 完全闭塞
        elif lesion.stenosis_percent >= 90:
            stenosis_factor = 2.0
        elif lesion.stenosis_percent >= 70:
            stenosis_factor = 1.5
        
        return weight * stenosis_factor
    
    def _get_complexity_score(self, lesion: Lesion) -> float:
        """获取病变复杂性评分"""
        complexity_score = 0.0
        
        if lesion.is_bifurcation:
            complexity_score += self.COMPLEXITY_SCORES['bifurcation']
        
        if lesion.is_ostial:
            complexity_score += self.COMPLEXITY_SCORES['ostial']
        
        if lesion.is_calcified:
            complexity_score += self.COMPLEXITY_SCORES['severe_calcification']
        
        if lesion.thrombus_present:
            complexity_score += self.COMPLEXITY_SCORES['thrombus']
        
        if lesion.is_cto:
            complexity_score += self.COMPLEXITY_SCORES['chronic_occlusion']
        
        if lesion.is_tortuous:
            complexity_score += self.COMPLEXITY_SCORES['tortuous']
        
        # 弥漫性病变判断(病变长度>20mm)
        if lesion.length_mm and lesion.length_mm > 20:
            complexity_score += self.COMPLEXITY_SCORES['diffuse_disease']
        
        return complexity_score
    
    def _get_segment_id(self, lesion: Lesion) -> int:
        """根据病变信息确定血管节段ID"""
        if lesion.segment_id:
            return lesion.segment_id
        
        # 根据血管类型和位置推断节段ID
        vessel_mapping = {
            VesselType.LM: 5,
            VesselType.LAD: {
                'proximal': 6,
                'mid': 7,
                'distal': 8
            },
            VesselType.LCX: {
                'proximal': 11,
                'mid': 13,
                'distal': 14
            },
            VesselType.RCA: {
                'proximal': 1,
                'mid': 2,
                'distal': 3
            }
        }
        
        vessel_map = vessel_mapping.get(lesion.vessel)
        if isinstance(vessel_map, dict):
            return vessel_map.get(lesion.location.value, 1)
        else:
            return vessel_map or 1
    
    def _calculate_clinical_score(self, patient_data: PatientData) -> float:
        """计算临床评分(用于SYNTAX II)"""
        clinical_score = 0.0
        
        # 年龄评分
        if patient_data.age >= 80:
            clinical_score += 10
        elif patient_data.age >= 70:
            clinical_score += 5
        elif patient_data.age >= 60:
            clinical_score += 2
        
        # 性别评分
        if patient_data.gender.value == 'female':
            clinical_score += 2
        
        # 合并症评分
        if patient_data.diabetes:
            clinical_score += 3
        
        if patient_data.creatinine_mg_dl and patient_data.creatinine_mg_dl > 2.0:
            clinical_score += 4
        
        if patient_data.ejection_fraction and patient_data.ejection_fraction < 50:
            clinical_score += 3
        
        return clinical_score
    
    def _calculate_syntax_ii_score(self, patient_data: PatientData, anatomical_score: float) -> float:
        """计算SYNTAX II评分"""
        clinical_score = self._calculate_clinical_score(patient_data)
        
        # SYNTAX II = 解剖学评分 × (1 + 临床评分/100)
        syntax_ii = anatomical_score * (1 + clinical_score / 100)
        
        return round(syntax_ii, 1)
    
    def _get_risk_category(self, score: float) -> str:
        """根据评分确定风险分层"""
        if score <= 22:
            return 'low'      # 低风险
        elif score <= 32:
            return 'intermediate'  # 中等风险
        else:
            return 'high'     # 高风险
    
    def get_detailed_report(self, patient_data: PatientData) -> Dict:
        """获取详细评分报告"""
        scores = self.calculate(patient_data)
        
        # 分析每个病变的贡献
        lesion_details = []
        for i, lesion in enumerate(patient_data.lesions):
            if lesion.stenosis_percent >= 50:
                base_score = self._get_base_score(lesion)
                complexity_score = self._get_complexity_score(lesion)
                
                lesion_details.append({
                    'lesion_index': i + 1,
                    'vessel': lesion.vessel.value,
                    'stenosis_percent': lesion.stenosis_percent,
                    'base_score': base_score,
                    'complexity_score': complexity_score,
                    'total_contribution': base_score + complexity_score
                })
        
        return {
            'scores': scores,
            'lesion_details': lesion_details,
            'recommendation': self._get_treatment_recommendation(scores['total_score'])
        }
    
    def _get_treatment_recommendation(self, score: float) -> str:
        """根据评分给出治疗建议"""
        if score <= 22:
            return "低复杂性病变，适合PCI治疗"
        elif score <= 32:
            return "中等复杂性病变，PCI和CABG均可考虑，建议心脏团队讨论"
        else:
            return "高复杂性病变，优先考虑CABG治疗"