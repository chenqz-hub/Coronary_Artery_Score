"""
血管节段定义

定义了冠脉血管的各个节段及其相关信息，用于评分计算。
"""

from typing import Dict, List
from ..models.patient import VesselSegment, VesselType

# 冠脉血管节段定义 (基于AHA分段标准)
VESSEL_SEGMENTS: Dict[int, VesselSegment] = {
    # 右冠脉系统
    1: VesselSegment(
        segment_id=1,
        vessel_type=VesselType.RCA,
        name="RCA近段",
        multiplication_factor=1.0
    ),
    2: VesselSegment(
        segment_id=2,
        vessel_type=VesselType.RCA,
        name="RCA中段",
        multiplication_factor=1.0
    ),
    3: VesselSegment(
        segment_id=3,
        vessel_type=VesselType.RCA,
        name="RCA远段",
        multiplication_factor=1.0
    ),
    4: VesselSegment(
        segment_id=4,
        vessel_type=VesselType.PDA,
        name="后降支",
        multiplication_factor=1.0
    ),
    16: VesselSegment(
        segment_id=16,
        vessel_type=VesselType.PLV,
        name="左室后支",
        multiplication_factor=0.5
    ),
    
    # 左主干
    5: VesselSegment(
        segment_id=5,
        vessel_type=VesselType.LM,
        name="左主干",
        multiplication_factor=5.0
    ),
    
    # 左前降支系统
    6: VesselSegment(
        segment_id=6,
        vessel_type=VesselType.LAD,
        name="LAD近段",
        multiplication_factor=2.5
    ),
    7: VesselSegment(
        segment_id=7,
        vessel_type=VesselType.LAD,
        name="LAD中段",
        multiplication_factor=1.5
    ),
    8: VesselSegment(
        segment_id=8,
        vessel_type=VesselType.LAD,
        name="LAD远段",
        multiplication_factor=1.0
    ),
    9: VesselSegment(
        segment_id=9,
        vessel_type=VesselType.D,
        name="第一对角支",
        multiplication_factor=1.0
    ),
    10: VesselSegment(
        segment_id=10,
        vessel_type=VesselType.D,
        name="第二对角支",
        multiplication_factor=0.5
    ),
    
    # 左回旋支系统
    11: VesselSegment(
        segment_id=11,
        vessel_type=VesselType.LCX,
        name="LCX近段",
        multiplication_factor=2.5
    ),
    12: VesselSegment(
        segment_id=12,
        vessel_type=VesselType.OM,
        name="第一钝缘支",
        multiplication_factor=1.0
    ),
    13: VesselSegment(
        segment_id=13,
        vessel_type=VesselType.LCX,
        name="LCX中段",
        multiplication_factor=1.0
    ),
    14: VesselSegment(
        segment_id=14,
        vessel_type=VesselType.LCX,
        name="LCX远段/左室后侧支",
        multiplication_factor=1.0
    ),
    15: VesselSegment(
        segment_id=15,
        vessel_type=VesselType.OM,
        name="第二钝缘支",
        multiplication_factor=0.5
    ),
}

# Gensini评分权重系数
GENSINI_WEIGHTS = {
    1: 1.0,   # RCA近段
    2: 1.0,   # RCA中段  
    3: 1.0,   # RCA远段
    4: 1.0,   # 后降支
    5: 5.0,   # 左主干
    6: 2.5,   # LAD近段
    7: 1.5,   # LAD中段
    8: 1.0,   # LAD远段
    9: 1.0,   # 第一对角支
    10: 0.5,  # 第二对角支
    11: 2.5,  # LCX近段
    12: 1.0,  # 第一钝缘支
    13: 1.0,  # LCX中段
    14: 1.0,  # LCX远段
    15: 0.5,  # 第二钝缘支
    16: 0.5,  # 左室后支
}

def get_vessel_segments_by_type(vessel_type: VesselType) -> List[VesselSegment]:
    """根据血管类型获取相关节段"""
    return [segment for segment in VESSEL_SEGMENTS.values() 
            if segment.vessel_type == vessel_type]

def get_segment_by_id(segment_id: int) -> VesselSegment:
    """根据节段ID获取节段信息"""
    return VESSEL_SEGMENTS.get(segment_id)

def get_all_segments() -> List[VesselSegment]:
    """获取所有血管节段"""
    return list(VESSEL_SEGMENTS.values())