"""
患者数据模型

定义了用于冠脉评分计算的数据结构，包括患者信息、病变信息等。
"""

from typing import List, Optional, Union, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Gender(str, Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = "female"


class VesselType(str, Enum):
    """血管类型枚举"""
    LAD = "LAD"  # 左前降支
    LCX = "LCX"  # 左回旋支
    RCA = "RCA"  # 右冠脉
    LM = "LM"    # 左主干
    OM = "OM"    # 钝缘支
    D = "D"      # 对角支
    PLV = "PLV"  # 左室后支
    PDA = "PDA"  # 后降支


class StenosisLocation(str, Enum):
    """狭窄部位枚举"""
    PROXIMAL = "proximal"    # 近端
    MID = "mid"             # 中段
    DISTAL = "distal"       # 远端


class LesionMorphology(str, Enum):
    """病变形态枚举"""
    TYPE_A = "A"  # 简单病变
    TYPE_B1 = "B1"  # 中等复杂病变
    TYPE_B2 = "B2"  # 复杂病变
    TYPE_C = "C"   # 最复杂病变


class VesselSegment(BaseModel):
    """血管节段模型"""
    segment_id: int = Field(..., description="节段编号")
    vessel_type: VesselType = Field(..., description="血管类型")
    name: str = Field(..., description="节段名称")
    multiplication_factor: float = Field(..., description="Gensini评分乘数因子")
    
    class Config:
        use_enum_values = True


class Lesion(BaseModel):
    """病变信息模型"""
    lesion_id: Optional[str] = Field(None, description="病变唯一标识")
    vessel: VesselType = Field(..., description="病变血管")
    segment_id: Optional[int] = Field(None, description="血管节段ID")
    stenosis_percent: float = Field(..., ge=0, le=100, description="狭窄百分比")
    location: StenosisLocation = Field(..., description="狭窄位置")
    length_mm: Optional[float] = Field(None, ge=0, description="病变长度(mm)")
    morphology: Optional[LesionMorphology] = Field(None, description="病变形态")
    
    # SYNTAX评分相关字段
    is_bifurcation: bool = Field(False, description="是否分叉病变")
    is_ostial: bool = Field(False, description="是否开口病变") 
    is_calcified: bool = Field(False, description="是否钙化病变")
    is_tortuous: bool = Field(False, description="是否迂曲病变")
    is_cto: bool = Field(False, description="是否慢性完全闭塞")
    thrombus_present: bool = Field(False, description="是否存在血栓")
    
    # 介入治疗相关
    is_treated: bool = Field(False, description="是否已治疗")
    treatment_method: Optional[str] = Field(None, description="治疗方法")
    
    class Config:
        use_enum_values = True
    
    @validator('stenosis_percent')
    def validate_stenosis_percent(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('狭窄百分比必须在0-100之间')
        return v


class PatientData(BaseModel):
    """患者数据模型"""
    # 基本信息
    patient_id: Optional[str] = Field(None, description="患者ID")
    age: int = Field(..., ge=0, le=150, description="年龄")
    gender: Gender = Field(..., description="性别")
    
    # 临床信息
    diabetes: bool = Field(False, description="是否糖尿病")
    hypertension: bool = Field(False, description="是否高血压")
    hyperlipidemia: bool = Field(False, description="是否高脂血症")
    smoking: bool = Field(False, description="是否吸烟")
    family_history: bool = Field(False, description="是否有冠心病家族史")
    
    # 生化指标
    creatinine_mg_dl: Optional[float] = Field(None, ge=0, description="肌酐值(mg/dL)")
    ldl_cholesterol: Optional[float] = Field(None, ge=0, description="低密度脂蛋白胆固醇")
    
    # 左室功能
    ejection_fraction: Optional[float] = Field(None, ge=0, le=100, description="射血分数(%)")
    
    # 病变信息
    lesions: List[Lesion] = Field(default_factory=list, description="病变列表")
    
    # 检查信息
    examination_date: Optional[datetime] = Field(None, description="检查日期")
    examination_type: Optional[str] = Field(None, description="检查类型")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('age')
    def validate_age(cls, v):
        if not 0 <= v <= 150:
            raise ValueError('年龄必须在0-150之间')
        return v
    
    @validator('ejection_fraction')
    def validate_ejection_fraction(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('射血分数必须在0-100之间')
        return v
    
    def add_lesion(self, lesion: Lesion) -> None:
        """添加病变"""
        self.lesions.append(lesion)
    
    def get_lesions_by_vessel(self, vessel: VesselType) -> List[Lesion]:
        """根据血管类型获取病变"""
        return [lesion for lesion in self.lesions if lesion.vessel == vessel]
    
    def get_significant_lesions(self, threshold: float = 50.0) -> List[Lesion]:
        """获取显著狭窄病变"""
        return [lesion for lesion in self.lesions if lesion.stenosis_percent >= threshold]