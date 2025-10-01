"""
数据导入导出功能

支持从多种数据源导入患者数据，包括JSON、CSV、Excel等格式。
"""

import json
import csv
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from ..models.patient import PatientData, Lesion, Gender, VesselType, StenosisLocation, LesionMorphology
from ..utils.validation import validate_patient_data, sanitize_input_data


class DataImportError(Exception):
    """数据导入错误"""
    pass


class DataImporter:
    """数据导入器"""
    
    def __init__(self):
        """初始化数据导入器"""
        self.supported_formats = ['.json', '.csv', '.xlsx', '.xml']
    
    def import_from_file(self, file_path: Union[str, Path]) -> List[PatientData]:
        """
        从文件导入患者数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            患者数据列表
            
        Raises:
            DataImportError: 导入失败时抛出
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DataImportError(f"文件不存在: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.json':
                return self._import_from_json(file_path)
            elif file_extension == '.csv':
                return self._import_from_csv(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                return self._import_from_excel(file_path)
            else:
                raise DataImportError(f"不支持的文件格式: {file_extension}")
        except Exception as e:
            raise DataImportError(f"导入文件失败: {str(e)}")
    
    def _import_from_json(self, file_path: Path) -> List[PatientData]:
        """从JSON文件导入"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            # 单个患者数据
            return [self._parse_patient_dict(data)]
        elif isinstance(data, list):
            # 多个患者数据
            return [self._parse_patient_dict(patient_dict) for patient_dict in data]
        else:
            raise DataImportError("JSON数据格式错误")
    
    def _import_from_csv(self, file_path: Path) -> List[PatientData]:
        """从CSV文件导入"""
        df = pd.read_csv(file_path)
        return self._parse_dataframe(df)
    
    def _import_from_excel(self, file_path: Path) -> List[PatientData]:
        """从Excel文件导入"""
        # 尝试读取多个sheet
        excel_file = pd.ExcelFile(file_path)
        
        if 'patients' in excel_file.sheet_names:
            # 如果有patients sheet，优先使用
            df_patients = pd.read_excel(file_path, sheet_name='patients')
            patients = self._parse_dataframe(df_patients)
            
            # 如果有lesions sheet，读取病变数据
            if 'lesions' in excel_file.sheet_names:
                df_lesions = pd.read_excel(file_path, sheet_name='lesions')
                self._merge_lesions_data(patients, df_lesions)
            
            return patients
        else:
            # 使用第一个sheet
            df = pd.read_excel(file_path, sheet_name=0)
            return self._parse_dataframe(df)
    
    def _parse_patient_dict(self, patient_dict: Dict[str, Any]) -> PatientData:
        """解析患者字典数据"""
        # 清理输入数据
        cleaned_data = sanitize_input_data(patient_dict)
        
        # 处理病变数据
        lesions = []
        if 'lesions' in cleaned_data:
            for lesion_dict in cleaned_data['lesions']:
                lesion = self._parse_lesion_dict(lesion_dict)
                lesions.append(lesion)
            del cleaned_data['lesions']
        
        # 创建患者对象
        try:
            patient = PatientData(**cleaned_data)
            patient.lesions = lesions
            
            # 验证数据
            is_valid, errors = validate_patient_data(patient)
            if not is_valid:
                raise DataImportError(f"患者数据验证失败: {'; '.join(errors)}")
            
            return patient
        except Exception as e:
            raise DataImportError(f"创建患者数据失败: {str(e)}")
    
    def _parse_lesion_dict(self, lesion_dict: Dict[str, Any]) -> Lesion:
        """解析病变字典数据"""
        # 枚举值转换
        if 'vessel' in lesion_dict:
            lesion_dict['vessel'] = VesselType(lesion_dict['vessel'])
        if 'location' in lesion_dict:
            lesion_dict['location'] = StenosisLocation(lesion_dict['location'])
        if 'morphology' in lesion_dict:
            lesion_dict['morphology'] = LesionMorphology(lesion_dict['morphology'])
        
        return Lesion(**lesion_dict)
    
    def _parse_dataframe(self, df: pd.DataFrame) -> List[PatientData]:
        """解析DataFrame数据"""
        patients = []
        
        for _, row in df.iterrows():
            # 将行数据转换为字典
            patient_dict = row.to_dict()
            
            # 处理NaN值
            patient_dict = {k: v for k, v in patient_dict.items() 
                          if pd.notna(v)}
            
            # 解析患者数据
            patient = self._parse_patient_dict(patient_dict)
            patients.append(patient)
        
        return patients
    
    def _merge_lesions_data(self, patients: List[PatientData], df_lesions: pd.DataFrame):
        """合并病变数据到患者数据"""
        # 按患者ID分组病变数据
        lesions_by_patient = df_lesions.groupby('patient_id')
        
        for patient in patients:
            if patient.patient_id and patient.patient_id in lesions_by_patient.groups:
                lesion_rows = lesions_by_patient.get_group(patient.patient_id)
                
                for _, lesion_row in lesion_rows.iterrows():
                    lesion_dict = lesion_row.to_dict()
                    lesion_dict = {k: v for k, v in lesion_dict.items() 
                                 if pd.notna(v) and k != 'patient_id'}
                    
                    lesion = self._parse_lesion_dict(lesion_dict)
                    patient.add_lesion(lesion)


class DataExporter:
    """数据导出器"""
    
    def __init__(self):
        """初始化数据导出器"""
        self.supported_formats = ['.json', '.csv', '.xlsx']
    
    def export_to_file(self, patients: List[PatientData], file_path: Union[str, Path], 
                      format_type: Optional[str] = None):
        """
        导出患者数据到文件
        
        Args:
            patients: 患者数据列表
            file_path: 输出文件路径
            format_type: 强制指定格式类型
        """
        file_path = Path(file_path)
        
        if format_type:
            file_extension = f'.{format_type.lower()}'
        else:
            file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.json':
                self._export_to_json(patients, file_path)
            elif file_extension == '.csv':
                self._export_to_csv(patients, file_path)
            elif file_extension in ['.xlsx', '.xls']:
                self._export_to_excel(patients, file_path)
            else:
                raise ValueError(f"不支持的导出格式: {file_extension}")
        except Exception as e:
            raise DataImportError(f"导出文件失败: {str(e)}")
    
    def _export_to_json(self, patients: List[PatientData], file_path: Path):
        """导出到JSON文件"""
        data = [patient.dict() for patient in patients]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def _export_to_csv(self, patients: List[PatientData], file_path: Path):
        """导出到CSV文件"""
        # 提取患者基本信息
        patient_records = []
        lesion_records = []
        
        for patient in patients:
            # 患者基本信息
            patient_dict = patient.dict()
            lesions = patient_dict.pop('lesions', [])
            patient_records.append(patient_dict)
            
            # 病变信息
            for i, lesion in enumerate(lesions):
                lesion_record = lesion.copy()
                lesion_record['patient_id'] = patient.patient_id
                lesion_record['lesion_index'] = i + 1
                lesion_records.append(lesion_record)
        
        # 导出患者数据
        if patient_records:
            df_patients = pd.DataFrame(patient_records)
            patients_file = file_path.parent / f"{file_path.stem}_patients.csv"
            df_patients.to_csv(patients_file, index=False, encoding='utf-8')
        
        # 导出病变数据
        if lesion_records:
            df_lesions = pd.DataFrame(lesion_records)
            lesions_file = file_path.parent / f"{file_path.stem}_lesions.csv"
            df_lesions.to_csv(lesions_file, index=False, encoding='utf-8')
    
    def _export_to_excel(self, patients: List[PatientData], file_path: Path):
        """导出到Excel文件"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 患者数据sheet
            patient_records = []
            lesion_records = []
            
            for patient in patients:
                patient_dict = patient.dict()
                lesions = patient_dict.pop('lesions', [])
                patient_records.append(patient_dict)
                
                # 病变信息
                for i, lesion in enumerate(lesions):
                    lesion_record = lesion.copy()
                    lesion_record['patient_id'] = patient.patient_id
                    lesion_record['lesion_index'] = i + 1
                    lesion_records.append(lesion_record)
            
            if patient_records:
                df_patients = pd.DataFrame(patient_records)
                df_patients.to_excel(writer, sheet_name='patients', index=False)
            
            if lesion_records:
                df_lesions = pd.DataFrame(lesion_records)
                df_lesions.to_excel(writer, sheet_name='lesions', index=False)


def create_sample_data() -> List[PatientData]:
    """创建示例数据"""
    sample_patients = []
    
    # 示例患者1
    patient1 = PatientData(
        patient_id="P001",
        age=65,
        gender=Gender.MALE,
        diabetes=True,
        hypertension=True,
        ejection_fraction=55.0,
        lesions=[
            Lesion(
                lesion_id="L001",
                vessel=VesselType.LAD,
                stenosis_percent=75.0,
                location=StenosisLocation.PROXIMAL,
                length_mm=15.0,
                is_calcified=True
            ),
            Lesion(
                lesion_id="L002", 
                vessel=VesselType.RCA,
                stenosis_percent=60.0,
                location=StenosisLocation.MID,
                length_mm=8.0
            )
        ]
    )
    
    # 示例患者2
    patient2 = PatientData(
        patient_id="P002",
        age=58,
        gender=Gender.FEMALE,
        diabetes=False,
        hypertension=False,
        ejection_fraction=60.0,
        lesions=[
            Lesion(
                lesion_id="L003",
                vessel=VesselType.LCX,
                stenosis_percent=85.0,
                location=StenosisLocation.PROXIMAL,
                length_mm=20.0,
                is_bifurcation=True
            )
        ]
    )
    
    sample_patients.extend([patient1, patient2])
    return sample_patients