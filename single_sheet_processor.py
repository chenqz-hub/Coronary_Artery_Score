"""
单表格式Excel处理器
专门处理一行一个患者的简单格式
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import traceback

class CoronaryScoreCalculator:
    """冠脉评分计算器"""
    
    def __init__(self):
        self.vessel_weights = {
            'LM': 5.0,   # 左主干
            'LAD': 3.5,  # 左前降支近段
            'LCX': 3.5,  # 左回旋支近段
            'RCA': 3.5,  # 右冠脉近段
            'OM': 1.0,   # 钝缘支
            'D': 1.0,    # 对角支
            'PDA': 1.0,  # 后降支
            'PLV': 0.5   # 左室后支
        }
    
    def calculate_syntax_score(self, patient):
        """计算SYNTAX评分"""
        total_score = 0
        lesion_details = []
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            
            if stenosis < 50:
                continue  # SYNTAX只计算≥50%的病变
            
            # 获取血管权重
            vessel = lesion['vessel']
            base_weight = self.vessel_weights.get(vessel, 1.0)
            
            # 根据位置调整权重
            location = lesion.get('location', 'proximal')
            if location == 'mid':
                base_weight *= 0.7
            elif location == 'distal':
                base_weight *= 0.4
            
            # 狭窄程度系数
            if stenosis >= 99:
                stenosis_factor = 5.0  # 完全闭塞
            elif stenosis >= 90:
                stenosis_factor = 2.0
            elif stenosis >= 70:
                stenosis_factor = 1.5
            else:
                stenosis_factor = 1.0
            
            # 基础评分
            base_score = base_weight * stenosis_factor
            
            # 复杂性评分
            complexity_score = 0
            if lesion.get('is_bifurcation', False):
                complexity_score += 1.0
            if lesion.get('is_calcified', False):
                complexity_score += 2.0
            if lesion.get('is_cto', False):
                complexity_score += 5.0
            if lesion.get('is_ostial', False):
                complexity_score += 0.5
            if lesion.get('is_tortuous', False):
                complexity_score += 1.0
            if lesion.get('thrombus_present', False):
                complexity_score += 1.0
            
            # 弥漫性病变(长度>20mm)
            length = lesion.get('length_mm', 0)
            if length > 20:
                complexity_score += 1.0
            
            lesion_score = base_score + complexity_score
            total_score += lesion_score
            
            lesion_details.append({
                'vessel': vessel,
                'stenosis_percent': stenosis,
                'base_score': round(base_score, 2),
                'complexity_score': round(complexity_score, 2),
                'total_contribution': round(lesion_score, 2)
            })
        
        # 风险分层
        if total_score <= 22:
            risk_category = 'low'
            risk_desc = '低风险 - 适合PCI治疗'
        elif total_score <= 32:
            risk_category = 'intermediate'
            risk_desc = '中等风险 - PCI和CABG均可考虑'
        else:
            risk_category = 'high'
            risk_desc = '高风险 - 优先考虑CABG治疗'
        
        return {
            'total_score': round(total_score, 1),
            'risk_category': risk_category,
            'risk_description': risk_desc,
            'lesion_details': lesion_details
        }
    
    def calculate_cad_rads_grade(self, patient):
        """计算CAD-RADS评分"""
        max_grade = 0
        vessel_grades = {}
        max_stenosis = 0
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            vessel = lesion['vessel']
            
            # 确定等级
            if stenosis == 0:
                grade = 0
            elif stenosis <= 24:
                grade = 1
            elif stenosis <= 49:
                grade = 2
            elif stenosis <= 69:
                grade = 3
            elif stenosis <= 99:
                grade = 4
            else:
                grade = 5
            
            max_grade = max(max_grade, grade)
            max_stenosis = max(max_stenosis, stenosis)
            
            # 记录各血管最高等级
            if vessel not in vessel_grades:
                vessel_grades[vessel] = grade
            else:
                vessel_grades[vessel] = max(vessel_grades[vessel], grade)
        
        # 等级描述和建议
        grade_descriptions = {
            0: ("无冠脉病变", "无需特殊处理"),
            1: ("轻微病变", "生活方式干预，控制危险因素"),
            2: ("轻度病变", "药物治疗，控制危险因素"),
            3: ("中度病变", "考虑功能学检查评估心肌缺血"),
            4: ("重度病变", "建议血管造影，考虑血运重建"),
            5: ("完全闭塞", "建议血管造影，考虑血运重建")
        }
        
        description, recommendation = grade_descriptions.get(max_grade, ("请咨询医师", "请咨询医师"))
        
        return {
            'grade': max_grade,
            'max_stenosis': max_stenosis,
            'vessel_grades': vessel_grades,
            'description': description,
            'recommendation': recommendation
        }
    
    def calculate_gensini_score(self, patient):
        """计算Gensini评分"""
        total_score = 0
        vessel_scores = {}
        
        # Gensini权重系数
        gensini_weights = {
            'LM': 5.0,
            'LAD': 2.5,
            'LCX': 2.5,
            'RCA': 1.0,
            'OM': 1.0,
            'D': 1.0,
            'PDA': 1.0,
            'PLV': 0.5
        }
        
        # 狭窄程度评分
        stenosis_scores = {
            (0, 25): 1,
            (25, 50): 2,
            (50, 75): 4,
            (75, 90): 8,
            (90, 99): 16,
            (99, 100): 32
        }
        
        for lesion in patient.get('lesions', []):
            stenosis = lesion['stenosis_percent']
            vessel = lesion['vessel']
            
            # 获取狭窄程度评分
            stenosis_score = 0
            for (min_s, max_s), score in stenosis_scores.items():
                if min_s < stenosis <= max_s:
                    stenosis_score = score
                    break
            
            # 获取血管权重
            vessel_weight = gensini_weights.get(vessel, 1.0)
            
            # 根据位置调整
            location = lesion.get('location', 'proximal')
            if location == 'mid':
                vessel_weight *= 0.8
            elif location == 'distal':
                vessel_weight *= 0.5
            
            lesion_score = stenosis_score * vessel_weight
            total_score += lesion_score
            
            if vessel not in vessel_scores:
                vessel_scores[vessel] = 0
            vessel_scores[vessel] += lesion_score
        
        # 严重程度分级
        if total_score == 0:
            risk_category = 'normal'
            risk_desc = '无病变'
        elif total_score <= 20:
            risk_category = 'mild'
            risk_desc = '轻度病变'
        elif total_score <= 40:
            risk_category = 'moderate'
            risk_desc = '中度病变'
        elif total_score <= 80:
            risk_category = 'severe'
            risk_desc = '重度病变'
        else:
            risk_category = 'critical'
            risk_desc = '极重度病变'
        
        return {
            'total_score': round(total_score, 1),
            'vessel_scores': vessel_scores,
            'risk_category': risk_category,
            'risk_description': risk_desc
        }

class SingleSheetProcessor:
    """单工作表格式处理器"""
    
    def __init__(self):
        self.calculator = CoronaryScoreCalculator()
    
    def parse_excel_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """读取Excel文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 尝试读取Excel文件
        try:
            df = pd.read_excel(file_path)
            print(f"✓ 成功读取Excel文件: {file_path}")
            print(f"✓ 找到 {len(df)} 行数据")
            return df
        except Exception as e:
            raise ValueError(f"读取Excel文件失败: {str(e)}")
    
    def validate_required_columns(self, df: pd.DataFrame) -> List[str]:
        """验证必需列是否存在"""
        required_columns = [
            'patient_id', 'age', 'gender',
            'vessel', 'stenosis_percent', 'location'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        return missing_columns
    
    def parse_vessel_and_location(self, vessel: str, location: str) -> tuple:
        """解析血管类型和位置"""
        vessel = str(vessel).strip().upper()
        location = str(location).strip().lower()
        
        # 血管映射
        vessel_mapping = {
            'LM': VesselType.LM,
            'LEFT_MAIN': VesselType.LM,
            'LAD': VesselType.LAD,
            'LEFT_ANTERIOR_DESCENDING': VesselType.LAD,
            'LCX': VesselType.LCX, 
            'LEFT_CIRCUMFLEX': VesselType.LCX,
            'RCA': VesselType.RCA,
            'RIGHT_CORONARY_ARTERY': VesselType.RCA,
            'OM': VesselType.OM,
            'OBTUSE_MARGINAL': VesselType.OM,
            'D': VesselType.D,
            'DIAGONAL': VesselType.D,
            'PDA': VesselType.PDA,
            'POSTERIOR_DESCENDING': VesselType.PDA
        }
        
        # 位置映射
        location_mapping = {
            'proximal': StenosisLocation.PROXIMAL,
            'mid': StenosisLocation.MID, 
            'middle': StenosisLocation.MID,
            'distal': StenosisLocation.DISTAL
        }
        
        # 获取血管类型
        vessel_type = vessel_mapping.get(vessel, VesselType.LAD)
        if vessel not in vessel_mapping:
            print(f"⚠️ 未知血管: {vessel}，使用LAD")
        
        # 获取位置
        stenosis_location = location_mapping.get(location, StenosisLocation.PROXIMAL)
        if location not in location_mapping:
            print(f"⚠️ 未知位置: {location}，使用proximal")
        
        return vessel_type, stenosis_location
    
    def safe_convert_boolean(self, value) -> bool:
        """安全转换为布尔值"""
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.upper() in ['TRUE', 'YES', '1', 'Y', '是']
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def safe_convert_float(self, value, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def create_patient_from_row(self, row: pd.Series) -> PatientData:
        """从DataFrame行创建患者数据"""
        
        # 基本信息
        patient_id = str(row['patient_id'])
        age = int(row['age'])
        gender = Gender.MALE if str(row['gender']).lower() == 'male' else Gender.FEMALE
        
        # 创建主要病变
        vessel_type, stenosis_location = self.parse_vessel_and_location(row['vessel'], row['location'])
        stenosis_percent = self.safe_convert_float(row['stenosis_percent'])
        
        main_lesion = Lesion(
            vessel=vessel_type,
            location=stenosis_location,
            stenosis_percent=stenosis_percent,
            length_mm=self.safe_convert_float(row.get('length_mm', 10.0), 10.0),
            is_bifurcation=self.safe_convert_boolean(row.get('is_bifurcation')),
            is_calcified=self.safe_convert_boolean(row.get('is_calcified')),
            is_ostial=self.safe_convert_boolean(row.get('is_ostial')),
            is_tortuous=self.safe_convert_boolean(row.get('is_tortuous')),
            is_cto=self.safe_convert_boolean(row.get('is_cto')),
            thrombus_present=self.safe_convert_boolean(row.get('thrombus_present'))
        )
        
        # 创建患者数据
        patient_data = PatientData(
            patient_id=patient_id,
            age=age,
            gender=gender,
            lesions=[main_lesion]
        )
        
        # 添加可选的临床信息
        if 'diabetes' in row:
            patient_data.diabetes = self.safe_convert_boolean(row['diabetes'])
        if 'hypertension' in row:
            patient_data.hypertension = self.safe_convert_boolean(row['hypertension'])
        if 'hyperlipidemia' in row:
            patient_data.hyperlipidemia = self.safe_convert_boolean(row['hyperlipidemia'])
        if 'smoking' in row:
            patient_data.smoking = self.safe_convert_boolean(row['smoking'])
        if 'ejection_fraction' in row:
            patient_data.ejection_fraction = self.safe_convert_float(row['ejection_fraction'])
        if 'creatinine_mg_dl' in row:
            patient_data.creatinine_mg_dl = self.safe_convert_float(row['creatinine_mg_dl'])
        
        return patient_data
    
    def calculate_scores(self, patient_dict: Dict) -> Dict:
        """计算所有评分"""
        scores = {}
        
        # 使用简化的计算器
        calculator = CoronaryScoreCalculator()
        
        # SYNTAX评分
        try:
            syntax_result = calculator.calculate_syntax_score(patient_dict)
            scores['SYNTAX'] = {
                'score': round(syntax_result['total_score'], 1),
                'class': syntax_result['risk_category'].title(),
                'interpretation': syntax_result['risk_description']
            }
        except Exception as e:
            scores['SYNTAX'] = {'error': str(e)}
        
        # CAD-RADS评分
        try:
            cad_rads_result = calculator.calculate_cad_rads_grade(patient_dict)
            scores['CAD_RADS'] = {
                'grade': cad_rads_result['grade'],
                'interpretation': cad_rads_result['description']
            }
        except Exception as e:
            scores['CAD_RADS'] = {'error': str(e)}
        
        # Gensini评分
        try:
            gensini_result = calculator.calculate_gensini_score(patient_dict)
            scores['Gensini'] = {
                'score': round(gensini_result['total_score'], 1),
                'class': gensini_result['risk_category'].title(),
                'interpretation': gensini_result['risk_description']
            }
        except Exception as e:
            scores['Gensini'] = {'error': str(e)}
        
        return scores
    
    def process_excel_file(self, file_path: Union[str, Path]) -> Tuple[List[Dict], pd.DataFrame]:
        """处理Excel文件并计算所有评分"""
        
        print("📊 开始处理单表格式Excel文件")
        print("=" * 50)
        
        # 读取Excel文件
        df = self.parse_excel_file(file_path)
        
        # 验证必需列
        missing_cols = self.validate_required_columns(df)
        if missing_cols:
            raise ValueError(f"缺少必需列: {missing_cols}")
        
        print("✓ 必需列验证通过")
        
        # 处理每一行数据
        results = []
        
        for idx, row in df.iterrows():
            try:
                print(f"\n📋 处理患者 {idx + 1}/{len(df)}: {row['patient_id']}")
                
                # 创建患者数据
                patient_data = self.create_patient_from_row(row)
                print(f"  ✓ 患者信息: {patient_data.age}岁 {patient_data.gender}")
                print(f"  ✓ 主要病变: {patient_data.lesions[0].vessel} {patient_data.lesions[0].location} {patient_data.lesions[0].stenosis_percent}%")
                
                # 计算评分
                scores = self.calculate_scores(patient_data)
                
                # 构建结果
                result = {
                    'patient_id': patient_data.patient_id,
                    'patient_data': patient_data,
                    'scores': scores
                }
                
                results.append(result)
                
                # 显示评分结果
                print(f"  📊 评分结果:")
                for score_name, score_data in scores.items():
                    if 'error' in score_data:
                        print(f"    {score_name}: ❌ {score_data['error']}")
                    else:
                        if score_name in ['SYNTAX', 'Gensini']:
                            print(f"    {score_name}: {score_data['score']} ({score_data['class']})")
                        else:  # CAD-RADS
                            print(f"    {score_name}: {score_data['grade']}")
                
            except Exception as e:
                print(f"  ❌ 处理失败: {str(e)}")
                error_result = {
                    'patient_id': str(row.get('patient_id', f'Row_{idx}')),
                    'patient_data': None,
                    'scores': {'error': str(e)}
                }
                results.append(error_result)
        
        print(f"\n✅ 处理完成！共处理 {len(results)} 个患者")
        return results, df
    
    def export_results(self, results: List[Dict], output_path: Union[str, Path]):
        """导出结果到Excel"""
        
        # 准备导出数据
        export_data = []
        
        for result in results:
            row_data = {
                'patient_id': result['patient_id']
            }
            
            if result['patient_data']:
                patient = result['patient_data']
                row_data.update({
                    'age': patient.age,
                    'gender': patient.gender,
                    'diabetes': patient.diabetes,
                    'hypertension': patient.hypertension,
                    'ejection_fraction': patient.ejection_fraction
                })
                
                # 主要病变信息
                if patient.lesions:
                    main_lesion = patient.lesions[0]
                    row_data.update({
                        'vessel': main_lesion.vessel,
                        'location': main_lesion.location,
                        'stenosis_percent': main_lesion.stenosis_percent,
                        'length_mm': main_lesion.length_mm
                    })
            
            # 评分结果
            scores = result['scores']
            if 'error' not in scores:
                # SYNTAX评分
                if 'SYNTAX' in scores and 'error' not in scores['SYNTAX']:
                    row_data['SYNTAX_score'] = scores['SYNTAX']['score']
                    row_data['SYNTAX_class'] = scores['SYNTAX']['class']
                
                # CAD-RADS评分
                if 'CAD_RADS' in scores and 'error' not in scores['CAD_RADS']:
                    row_data['CAD_RADS_grade'] = scores['CAD_RADS']['grade']
                
                # Gensini评分
                if 'Gensini' in scores and 'error' not in scores['Gensini']:
                    row_data['Gensini_score'] = scores['Gensini']['score']
                    row_data['Gensini_class'] = scores['Gensini']['class']
            else:
                row_data['error'] = scores['error']
            
            export_data.append(row_data)
        
        # 创建DataFrame并导出
        export_df = pd.DataFrame(export_data)
        export_df.to_excel(output_path, index=False)
        
        print(f"📄 结果已导出到: {output_path}")

def main():
    """主程序"""
    print("🏥 冠脉病变评分系统 - 单表格式处理器")
    print("=" * 60)
    
    # 创建处理器
    processor = SingleSheetProcessor()
    
    # 示例：处理模板文件
    template_path = Path('data/single_sheet_template.xlsx')
    
    if template_path.exists():
        print(f"📁 找到示例文件: {template_path}")
        
        try:
            # 处理文件
            results, original_df = processor.process_excel_file(template_path)
            
            # 导出结果
            output_path = Path('data/single_sheet_results.xlsx')
            processor.export_results(results, output_path)
            
            print("\n📊 评分汇总:")
            print("-" * 40)
            
            for result in results:
                if result['patient_data']:
                    scores = result['scores']
                    print(f"\n患者 {result['patient_id']}:")
                    
                    for score_name, score_data in scores.items():
                        if 'error' not in score_data:
                            if score_name in ['SYNTAX', 'Gensini']:
                                print(f"  {score_name}: {score_data['score']} ({score_data['class']})")
                            else:
                                print(f"  {score_name}: {score_data['grade']}")
                        else:
                            print(f"  {score_name}: ❌ {score_data['error']}")
            
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            traceback.print_exc()
    
    else:
        print("❌ 未找到示例文件，请先运行 create_single_template.py")

if __name__ == "__main__":
    main()