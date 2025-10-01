"""
Gensini评分计算器

Gensini评分是一个量化冠脉病变严重程度的评分系统，
考虑了狭窄程度、病变位置的重要性等因素。
"""

from typing import Dict, List, Optional
from ..models.patient import PatientData, Lesion, VesselType
from ..utils.vessel_segments import GENSINI_WEIGHTS


class GensiniCalculator:
    """Gensini评分计算器"""
    
    # 狭窄程度评分系数
    STENOSIS_SCORES = {
        (0, 25): 1,      # 1-25%
        (25, 50): 2,     # 25-50%
        (50, 75): 4,     # 50-75%
        (75, 90): 8,     # 75-90%
        (90, 99): 16,    # 90-99%
        (99, 100): 32,   # 99-100%
    }
    
    def __init__(self):
        """初始化Gensini计算器"""
        self.vessel_weights = GENSINI_WEIGHTS
    
    def calculate(self, patient_data: PatientData) -> Dict[str, float]:
        """
        计算Gensini评分
        
        Args:
            patient_data: 患者数据
            
        Returns:
            包含Gensini评分信息的字典
        """
        if not patient_data.lesions:
            return {
                'total_score': 0.0,
                'vessel_scores': {},
                'lesion_contributions': [],
                'severity_grade': 'normal'
            }
        
        total_score = 0.0
        vessel_scores = {}
        lesion_contributions = []
        
        for i, lesion in enumerate(patient_data.lesions):
            # 获取狭窄程度评分
            stenosis_score = self._get_stenosis_score(lesion.stenosis_percent)
            
            # 获取血管权重
            vessel_weight = self._get_vessel_weight(lesion)
            
            # 计算该病变的Gensini评分
            lesion_score = stenosis_score * vessel_weight
            
            # 累加总分
            total_score += lesion_score
            
            # 记录各血管评分
            vessel_key = lesion.vessel.value
            if vessel_key not in vessel_scores:
                vessel_scores[vessel_key] = 0
            vessel_scores[vessel_key] += lesion_score
            
            # 记录病变贡献
            lesion_contributions.append({
                'lesion_index': i + 1,
                'vessel': vessel_key,
                'stenosis_percent': lesion.stenosis_percent,
                'stenosis_score': stenosis_score,
                'vessel_weight': vessel_weight,
                'contribution': lesion_score
            })
        
        # 确定严重程度分级
        severity_grade = self._get_severity_grade(total_score)
        
        return {
            'total_score': round(total_score, 2),
            'vessel_scores': vessel_scores,
            'lesion_contributions': lesion_contributions,
            'severity_grade': severity_grade
        }
    
    def _get_stenosis_score(self, stenosis_percent: float) -> int:
        """根据狭窄程度获取评分"""
        for (min_stenosis, max_stenosis), score in self.STENOSIS_SCORES.items():
            if min_stenosis < stenosis_percent <= max_stenosis:
                return score
        return 0  # 0%狭窄
    
    def _get_vessel_weight(self, lesion: Lesion) -> float:
        """获取血管权重系数"""
        # 如果有具体的节段ID，使用节段权重
        if lesion.segment_id and lesion.segment_id in self.vessel_weights:
            return self.vessel_weights[lesion.segment_id]
        
        # 否则根据血管类型和位置推断权重
        vessel_type = lesion.vessel
        
        # 默认权重映射
        default_weights = {
            VesselType.LM: 5.0,    # 左主干
            VesselType.LAD: 2.5,   # 左前降支(默认近段权重)
            VesselType.LCX: 2.5,   # 左回旋支(默认近段权重)
            VesselType.RCA: 1.0,   # 右冠脉(默认权重)
            VesselType.OM: 1.0,    # 钝缘支
            VesselType.D: 1.0,     # 对角支
            VesselType.PDA: 1.0,   # 后降支
            VesselType.PLV: 0.5,   # 左室后支
        }
        
        base_weight = default_weights.get(vessel_type, 1.0)
        
        # 根据位置调整权重
        if hasattr(lesion, 'location') and lesion.location:
            location = lesion.location.value
            if location == 'proximal':
                # 近端病变权重更高
                if vessel_type in [VesselType.LAD, VesselType.LCX]:
                    base_weight = 2.5
                elif vessel_type == VesselType.RCA:
                    base_weight = 1.0
            elif location == 'mid':
                # 中段病变
                if vessel_type in [VesselType.LAD, VesselType.LCX]:
                    base_weight = 1.5
                elif vessel_type == VesselType.RCA:
                    base_weight = 1.0
            elif location == 'distal':
                # 远端病变权重较低
                base_weight = 1.0
        
        return base_weight
    
    def _get_severity_grade(self, total_score: float) -> str:
        """根据总分确定严重程度分级"""
        if total_score == 0:
            return 'normal'
        elif total_score <= 20:
            return 'mild'
        elif total_score <= 40:
            return 'moderate'
        elif total_score <= 80:
            return 'severe'
        else:
            return 'critical'
    
    def get_detailed_report(self, patient_data: PatientData) -> Dict:
        """获取详细的Gensini评分报告"""
        result = self.calculate(patient_data)
        
        # 风险分层
        risk_assessment = self._assess_cardiovascular_risk(
            result['total_score'], 
            patient_data
        )
        
        # 治疗建议
        treatment_recommendation = self._get_treatment_recommendation(
            result['total_score'],
            result['severity_grade']
        )
        
        # 预后评估
        prognosis = self._assess_prognosis(result['total_score'], patient_data)
        
        return {
            'gensini_result': result,
            'risk_assessment': risk_assessment,
            'treatment_recommendation': treatment_recommendation,
            'prognosis': prognosis,
            'comparison_with_syntax': self._compare_with_syntax_implications(result['total_score'])
        }
    
    def _assess_cardiovascular_risk(self, gensini_score: float, patient_data: PatientData) -> Dict:
        """评估心血管风险"""
        base_risk = "low"
        
        # 基于Gensini评分的基础风险
        if gensini_score > 80:
            base_risk = "very_high"
        elif gensini_score > 40:
            base_risk = "high"
        elif gensini_score > 20:
            base_risk = "moderate"
        elif gensini_score > 0:
            base_risk = "low"
        
        # 临床因素修正
        risk_modifiers = []
        
        if patient_data.age >= 75:
            risk_modifiers.append("高龄")
        if patient_data.diabetes:
            risk_modifiers.append("糖尿病")
        if patient_data.ejection_fraction and patient_data.ejection_fraction < 50:
            risk_modifiers.append("心功能不全")
        if patient_data.creatinine_mg_dl and patient_data.creatinine_mg_dl > 2.0:
            risk_modifiers.append("肾功能不全")
        
        return {
            'risk_level': base_risk,
            'risk_modifiers': risk_modifiers,
            'annual_event_risk': self._estimate_annual_event_risk(gensini_score, len(risk_modifiers))
        }
    
    def _estimate_annual_event_risk(self, gensini_score: float, modifier_count: int) -> str:
        """估算年度心血管事件风险"""
        base_risk = 0
        
        if gensini_score <= 20:
            base_risk = 2  # 2%
        elif gensini_score <= 40:
            base_risk = 5  # 5%
        elif gensini_score <= 80:
            base_risk = 10  # 10%
        else:
            base_risk = 20  # 20%
        
        # 每个危险因素增加风险
        adjusted_risk = base_risk + (modifier_count * 2)
        
        if adjusted_risk < 5:
            return "低风险 (<5%/年)"
        elif adjusted_risk < 10:
            return "中等风险 (5-10%/年)"
        elif adjusted_risk < 20:
            return "高风险 (10-20%/年)"
        else:
            return "极高风险 (>20%/年)"
    
    def _get_treatment_recommendation(self, gensini_score: float, severity_grade: str) -> Dict:
        """获取治疗建议"""
        recommendations = {
            'normal': {
                'primary': '无需特殊治疗',
                'lifestyle': '健康生活方式维持',
                'followup': '常规体检'
            },
            'mild': {
                'primary': '药物治疗，积极控制危险因素',
                'lifestyle': '戒烟、合理饮食、规律运动',
                'followup': '6-12个月复查'
            },
            'moderate': {
                'primary': '强化药物治疗，考虑功能学检查',
                'lifestyle': '严格控制危险因素',
                'followup': '3-6个月复查，必要时负荷试验'
            },
            'severe': {
                'primary': '建议冠脉造影，评估血运重建指征',
                'lifestyle': '全面危险因素管理',
                'followup': '密切随访，根据造影结果制定治疗方案'
            },
            'critical': {
                'primary': '紧急冠脉造影，积极血运重建',
                'lifestyle': '住院治疗期间全面评估',
                'followup': '术后按指南规范随访'
            }
        }
        
        return recommendations.get(severity_grade, recommendations['moderate'])
    
    def _assess_prognosis(self, gensini_score: float, patient_data: PatientData) -> Dict:
        """评估预后"""
        # 基于评分的基础预后
        if gensini_score <= 20:
            base_prognosis = "良好"
        elif gensini_score <= 40:
            base_prognosis = "相对良好"
        elif gensini_score <= 80:
            base_prognosis = "需要关注"
        else:
            base_prognosis = "较差，需要积极干预"
        
        # 影响预后的因素
        prognostic_factors = []
        if patient_data.age >= 80:
            prognostic_factors.append("高龄影响预后")
        if patient_data.diabetes:
            prognostic_factors.append("糖尿病影响预后")
        if patient_data.ejection_fraction and patient_data.ejection_fraction < 40:
            prognostic_factors.append("心功能不全显著影响预后")
        
        return {
            'overall_prognosis': base_prognosis,
            'prognostic_factors': prognostic_factors,
            'five_year_survival': self._estimate_survival(gensini_score, len(prognostic_factors))
        }
    
    def _estimate_survival(self, gensini_score: float, adverse_factors: int) -> str:
        """估算5年生存率"""
        base_survival = 95
        
        if gensini_score > 80:
            base_survival -= 15
        elif gensini_score > 40:
            base_survival -= 10
        elif gensini_score > 20:
            base_survival -= 5
        
        # 每个不良因素降低生存率
        adjusted_survival = base_survival - (adverse_factors * 5)
        adjusted_survival = max(adjusted_survival, 50)  # 最低50%
        
        return f"约{adjusted_survival}%"
    
    def _compare_with_syntax_implications(self, gensini_score: float) -> Dict:
        """与SYNTAX评分的比较说明"""
        return {
            'gensini_focus': 'Gensini评分主要反映病变的解剖严重程度和范围',
            'syntax_difference': 'SYNTAX评分更注重病变的复杂性和介入治疗的可行性',
            'clinical_application': 'Gensini评分适用于病变严重程度的定量评估和预后判断',
            'complementary_use': '两种评分可以互补使用，全面评估患者病情'
        }