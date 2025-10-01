"""
冠脉病变严重程度评分系统

这个包提供了多种冠状动脉病变严重程度评分的计算工具，包括：
- SYNTAX评分
- CAD-RADS评分  
- Gensini评分
"""

from .models.patient import PatientData, Lesion, VesselSegment
from .calculators.syntax_calculator import SyntaxCalculator
from .calculators.cad_rads_calculator import CadRadsCalculator
from .calculators.gensini_calculator import GensiniCalculator

__version__ = "1.0.0"
__author__ = "Coronary Artery Score Team"

__all__ = [
    "PatientData",
    "Lesion", 
    "VesselSegment",
    "SyntaxCalculator",
    "CadRadsCalculator",
    "GensiniCalculator",
]