"""
数据验证工具

提供患者数据和病变数据的验证功能。
"""

from typing import List, Dict, Any, Optional, Tuple
from ..models.patient import PatientData, Lesion, VesselType


class ValidationError(Exception):
    """验证错误异常"""
    pass


def validate_patient_data(patient_data: PatientData) -> Tuple[bool, List[str]]:
    """
    验证患者数据的完整性和合理性
    
    Args:
        patient_data: 患者数据对象
        
    Returns:
        (is_valid, error_messages): 验证结果和错误信息列表
    """
    errors = []
    
    # 基本信息验证
    if patient_data.age < 0 or patient_data.age > 150:
        errors.append("患者年龄必须在0-150岁之间")
    
    # 生化指标验证
    if patient_data.creatinine_mg_dl is not None:
        if patient_data.creatinine_mg_dl < 0 or patient_data.creatinine_mg_dl > 20:
            errors.append("肌酐值异常，应在0-20 mg/dL范围内")
    
    if patient_data.ejection_fraction is not None:
        if patient_data.ejection_fraction < 10 or patient_data.ejection_fraction > 100:
            errors.append("射血分数应在10-100%范围内")
    
    # 病变数据验证
    if not patient_data.lesions:
        errors.append("至少需要一个病变数据")
    else:
        for i, lesion in enumerate(patient_data.lesions):
            lesion_errors = validate_lesion_data(lesion)
            if lesion_errors:
                errors.extend([f"病变{i+1}: {error}" for error in lesion_errors])
    
    return len(errors) == 0, errors


def validate_lesion_data(lesion: Lesion) -> List[str]:
    """
    验证单个病变数据
    
    Args:
        lesion: 病变对象
        
    Returns:
        error_messages: 错误信息列表
    """
    errors = []
    
    # 狭窄程度验证
    if lesion.stenosis_percent < 0 or lesion.stenosis_percent > 100:
        errors.append("狭窄百分比必须在0-100%之间")
    
    # 病变长度验证
    if lesion.length_mm is not None:
        if lesion.length_mm < 0 or lesion.length_mm > 200:
            errors.append("病变长度异常，应在0-200mm范围内")
    
    # 逻辑一致性验证
    if lesion.is_cto and lesion.stenosis_percent < 99:
        errors.append("慢性完全闭塞(CTO)的狭窄程度应为99-100%")
    
    if lesion.thrombus_present and lesion.stenosis_percent < 70:
        errors.append("存在血栓的病变通常狭窄程度较重(≥70%)")
    
    return errors


def validate_scoring_parameters(parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证评分计算参数
    
    Args:
        parameters: 评分参数字典
        
    Returns:
        (is_valid, error_messages): 验证结果和错误信息列表
    """
    errors = []
    
    # 检查必需参数
    required_params = ['patient_data']
    for param in required_params:
        if param not in parameters:
            errors.append(f"缺少必需参数: {param}")
    
    return len(errors) == 0, errors


def check_data_consistency(patient_data: PatientData) -> List[str]:
    """
    检查数据一致性
    
    Args:
        patient_data: 患者数据
        
    Returns:
        warnings: 警告信息列表
    """
    warnings = []
    
    # 检查年龄与疾病的一致性
    if patient_data.age < 40:
        significant_lesions = [l for l in patient_data.lesions if l.stenosis_percent >= 70]
        if significant_lesions:
            warnings.append("年轻患者出现严重冠脉病变，建议检查是否有遗传性疾病")
    
    # 检查糖尿病与肌酐的关系
    if patient_data.diabetes and patient_data.creatinine_mg_dl and patient_data.creatinine_mg_dl > 1.5:
        warnings.append("糖尿病患者肌酐升高，需注意糖尿病肾病")
    
    # 检查射血分数与病变严重程度
    if patient_data.ejection_fraction and patient_data.ejection_fraction < 40:
        lm_lesions = [l for l in patient_data.lesions if l.vessel == VesselType.LM]
        if lm_lesions:
            warnings.append("左主干病变合并心功能不全，属于高危情况")
    
    return warnings


def sanitize_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理和标准化输入数据
    
    Args:
        data: 原始输入数据
        
    Returns:
        清理后的数据
    """
    cleaned_data = data.copy()
    
    # 清理字符串数据
    for key, value in cleaned_data.items():
        if isinstance(value, str):
            cleaned_data[key] = value.strip().lower() if key in ['gender', 'vessel', 'location'] else value.strip()
    
    # 标准化百分比数据
    if 'stenosis_percent' in cleaned_data:
        stenosis = cleaned_data['stenosis_percent']
        if isinstance(stenosis, str) and stenosis.endswith('%'):
            cleaned_data['stenosis_percent'] = float(stenosis.rstrip('%'))
    
    return cleaned_data