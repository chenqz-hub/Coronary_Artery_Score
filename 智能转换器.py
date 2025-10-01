"""
智能Excel表格转换器
自动识别您的表格格式并转换为标准模板格式
支持多种列名变体和中英文混合
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Optional, Any

class IntelligentExcelConverter:
    """智能Excel转换器"""
    
    def __init__(self):
        # 字段映射字典 - 支持多种可能的列名
        self.field_mapping = {
            'patient_id': [
                'patient_id', 'patientid', 'id', '患者id', '患者ID', '病例号', '住院号', 
                '门诊号', '病历号', '编号', 'case_id', 'caseid', 'number', 'no', '序号'
            ],
            'age': [
                'age', '年龄', 'years', 'yr', 'years_old', '岁'
            ],
            'gender': [
                'gender', 'sex', '性别', '男女', 'male_female', 'gender_mf'
            ],
            'vessel': [
                'vessel', 'artery', '血管', '病变血管', '靶血管', '罪犯血管', '主要病变血管',
                'target_vessel', 'culprit_vessel', 'main_vessel', '血管名称'
            ],
            'stenosis_percent': [
                'stenosis', 'stenosis_percent', '狭窄', '狭窄度', '狭窄百分比', '狭窄程度',
                'narrowing', 'occlusion', '阻塞', '堵塞', 'blockage', '狭窄率', '%'
            ],
            'location': [
                'location', 'position', '位置', '部位', '节段', '段', 'segment',
                '病变位置', '狭窄位置', 'lesion_location'
            ],
            'diabetes': [
                'diabetes', 'dm', '糖尿病', 'diabetic', '血糖', 'glucose'
            ],
            'hypertension': [
                'hypertension', 'htn', 'bp', '高血压', '血压', 'blood_pressure'
            ],
            'hyperlipidemia': [
                'hyperlipidemia', 'lipid', '高脂血症', '血脂', '胆固醇', 'cholesterol'
            ],
            'smoking': [
                'smoking', 'smoke', '吸烟', '烟草', 'tobacco', '抽烟'
            ],
            'ejection_fraction': [
                'ef', 'ejection_fraction', 'lvef', '射血分数', '左室射血分数', 
                'ejection', 'fraction', '心功能'
            ],
            'creatinine_mg_dl': [
                'creatinine', 'cr', 'scr', '肌酐', '血肌酐', '血清肌酐', 'creat'
            ],
            'length_mm': [
                'length', 'lesion_length', '长度', '病变长度', '狭窄长度', 'mm', 'millimeter'
            ],
            'is_bifurcation': [
                'bifurcation', '分叉', '分岔', 'branch', '分支', 'bifur'
            ],
            'is_calcified': [
                'calcified', 'calcium', 'calc', '钙化', '钙质', 'ca'
            ],
            'is_ostial': [
                'ostial', 'ostium', '开口', '起始', '入口', 'mouth'
            ],
            'is_tortuous': [
                'tortuous', 'tortuosity', '迂曲', '扭曲', '弯曲', 'curved', 'winding'
            ],
            'is_cto': [
                'cto', 'occlusion', '完全闭塞', '慢性闭塞', '闭塞', 'total_occlusion',
                'chronic_occlusion', '100%'
            ],
            'thrombus_present': [
                'thrombus', 'clot', '血栓', '血凝块', 'thrombosis'
            ]
        }
        
        # 血管名称标准化
        self.vessel_standardization = {
            # 左主干
            'LM': ['LM', 'LMCA', '左主干', '左主', '主干', 'LEFT_MAIN', 'left_main'],
            # 左前降支
            'LAD': ['LAD', 'LADCA', '左前降', '前降支', '左前降支', 'LEFT_ANTERIOR_DESCENDING'],
            # 左回旋支  
            'LCX': ['LCX', 'LCXCA', '左回旋', '回旋支', '左回旋支', 'LEFT_CIRCUMFLEX'],
            # 右冠脉
            'RCA': ['RCA', 'RCCA', '右冠', '右冠脉', '右冠状动脉', 'RIGHT_CORONARY'],
            # 钝缘支
            'OM': ['OM', 'OM1', 'OM2', '钝缘', '钝缘支', 'OBTUSE_MARGINAL'],
            # 对角支
            'D': ['D', 'D1', 'D2', '对角', '对角支', 'DIAGONAL'],
            # 后降支
            'PDA': ['PDA', '后降', '后降支', 'POSTERIOR_DESCENDING'],
            # 左室后支
            'PLV': ['PLV', '左室后', '左室后支', 'POSTERIOR_LEFT_VENTRICULAR']
        }
        
        # 位置标准化
        self.location_standardization = {
            'proximal': ['近段', '近端', '起始段', '开口段', 'proximal', 'prox', '1段'],
            'mid': ['中段', '中间段', '中部', 'mid', 'middle', '2段'],
            'distal': ['远段', '远端', '末段', '终末段', 'distal', 'dist', '3段']
        }
        
        # 性别标准化
        self.gender_standardization = {
            'male': ['男', '男性', 'male', 'M', 'm', '1'],
            'female': ['女', '女性', 'female', 'F', 'f', '0']
        }
    
    def read_excel_with_encoding(self, file_path: Path) -> pd.DataFrame:
        """智能读取Excel文件，处理编码问题"""
        try:
            # 尝试读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"✓ 成功读取Excel文件: {file_path}")
            return df
        except Exception as e:
            try:
                # 尝试其他引擎
                df = pd.read_excel(file_path, engine='xlrd')
                print(f"✓ 使用xlrd引擎读取: {file_path}")
                return df
            except Exception:
                raise Exception(f"无法读取Excel文件: {str(e)}")
    
    def analyze_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """分析列名并自动映射到标准字段"""
        print("\n🔍 开始智能列名分析...")
        
        column_mapping = {}
        available_columns = [col.strip() for col in df.columns]
        
        print(f"发现列名: {available_columns}")
        
        for standard_field, possible_names in self.field_mapping.items():
            best_match = None
            best_score = 0
            
            for col in available_columns:
                if col in column_mapping.values():
                    continue  # 已经映射过了
                
                col_clean = str(col).lower().strip()
                
                # 完全匹配
                for possible_name in possible_names:
                    possible_clean = possible_name.lower().strip()
                    
                    if col_clean == possible_clean:
                        best_match = col
                        best_score = 100
                        break
                    
                    # 包含匹配
                    elif possible_clean in col_clean or col_clean in possible_clean:
                        score = len(possible_clean) / max(len(col_clean), 1) * 80
                        if score > best_score:
                            best_match = col
                            best_score = score
            
            if best_match and best_score > 50:  # 只有置信度>50%才映射
                column_mapping[standard_field] = best_match
                print(f"  ✓ {standard_field} <- '{best_match}' (置信度: {best_score:.0f}%)")
        
        return column_mapping
    
    def standardize_vessel_name(self, vessel_value: Any) -> str:
        """标准化血管名称"""
        if pd.isna(vessel_value):
            return 'LAD'  # 默认值
        
        vessel_str = str(vessel_value).strip().upper()
        
        for standard_name, variants in self.vessel_standardization.items():
            for variant in variants:
                if variant.upper() in vessel_str or vessel_str in variant.upper():
                    return standard_name
        
        # 如果没找到匹配，尝试从描述中提取
        if '左主' in vessel_str or 'LM' in vessel_str:
            return 'LM'
        elif '前降' in vessel_str or 'LAD' in vessel_str:
            return 'LAD'  
        elif '回旋' in vessel_str or 'LCX' in vessel_str:
            return 'LCX'
        elif '右冠' in vessel_str or 'RCA' in vessel_str:
            return 'RCA'
        
        return 'LAD'  # 默认值
    
    def standardize_location(self, location_value: Any) -> str:
        """标准化病变位置"""
        if pd.isna(location_value):
            return 'proximal'  # 默认值
        
        location_str = str(location_value).strip()
        
        for standard_loc, variants in self.location_standardization.items():
            for variant in variants:
                if variant in location_str or location_str in variant:
                    return standard_loc
        
        return 'proximal'  # 默认值
    
    def standardize_gender(self, gender_value: Any) -> str:
        """标准化性别"""
        if pd.isna(gender_value):
            return 'male'  # 默认值
        
        gender_str = str(gender_value).strip()
        
        for standard_gender, variants in self.gender_standardization.items():
            for variant in variants:
                if variant in gender_str or gender_str in variant:
                    return standard_gender
        
        return 'male'  # 默认值
    
    def extract_stenosis_percent(self, stenosis_value: Any) -> float:
        """从各种格式中提取狭窄百分比"""
        if pd.isna(stenosis_value):
            return 0.0
        
        stenosis_str = str(stenosis_value).strip()
        
        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', stenosis_str)
        if numbers:
            value = float(numbers[0])
            
            # 如果值>1但<100，可能是百分比
            if value > 1:
                return min(value, 100.0)
            # 如果值<=1，可能是小数形式
            elif value <= 1:
                return value * 100
        
        # 特殊情况处理
        if '完全' in stenosis_str or '100' in stenosis_str or 'CTO' in stenosis_str.upper():
            return 100.0
        elif '重度' in stenosis_str or '严重' in stenosis_str:
            return 90.0
        elif '中度' in stenosis_str:
            return 70.0
        elif '轻度' in stenosis_str:
            return 50.0
        
        return 0.0
    
    def safe_convert_boolean(self, value: Any) -> bool:
        """安全转换布尔值"""
        if pd.isna(value):
            return False
        
        value_str = str(value).strip().upper()
        return value_str in ['TRUE', '是', 'YES', '1', 'Y', '有', '阳性', '+']
    
    def safe_convert_float(self, value: Any, default: float = 0.0) -> float:
        """安全转换浮点数"""
        if pd.isna(value):
            return default
        
        try:
            # 提取数字
            value_str = str(value).strip()
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return default
    
    def convert_to_standard_format(self, file_path: str) -> pd.DataFrame:
        """将用户的Excel转换为标准格式"""
        print("🔄 开始智能转换Excel表格...")
        print("=" * 60)
        
        # 读取文件
        file_path = Path(file_path)
        df = self.read_excel_with_encoding(file_path)
        
        print(f"原始数据: {len(df)} 行 x {len(df.columns)} 列")
        
        # 分析列名映射
        column_mapping = self.analyze_columns(df)
        
        # 检查必需字段
        required_fields = ['patient_id', 'age', 'gender', 'vessel', 'stenosis_percent']
        missing_required = [field for field in required_fields if field not in column_mapping]
        
        if missing_required:
            print(f"\n⚠️  警告: 未找到以下关键字段的匹配列: {missing_required}")
            print("将尝试使用默认值或智能推断...")
        
        # 创建标准格式数据
        standard_data = []
        
        for idx, row in df.iterrows():
            try:
                # 基本信息
                patient_id = str(row.get(column_mapping.get('patient_id', df.columns[0]), f'Patient_{idx+1}'))
                
                age_col = column_mapping.get('age')
                age = int(self.safe_convert_float(row.get(age_col) if age_col else 65, 65))
                
                gender_col = column_mapping.get('gender')
                gender = self.standardize_gender(row.get(gender_col) if gender_col else 'male')
                
                # 病变信息
                vessel_col = column_mapping.get('vessel')
                vessel = self.standardize_vessel_name(row.get(vessel_col) if vessel_col else 'LAD')
                
                stenosis_col = column_mapping.get('stenosis_percent')
                stenosis_percent = self.extract_stenosis_percent(row.get(stenosis_col) if stenosis_col else 0)
                
                location_col = column_mapping.get('location')
                location = self.standardize_location(row.get(location_col) if location_col else 'proximal')
                
                # 构建标准行
                standard_row = {
                    'patient_id': patient_id,
                    'age': age,
                    'gender': gender,
                    'vessel': vessel,
                    'stenosis_percent': stenosis_percent,
                    'location': location
                }
                
                # 添加可选字段
                for field in ['diabetes', 'hypertension', 'hyperlipidemia', 'smoking']:
                    col = column_mapping.get(field)
                    if col:
                        standard_row[field] = self.safe_convert_boolean(row.get(col))
                
                for field in ['ejection_fraction', 'creatinine_mg_dl', 'length_mm']:
                    col = column_mapping.get(field)
                    if col:
                        standard_row[field] = self.safe_convert_float(row.get(col))
                
                for field in ['is_bifurcation', 'is_calcified', 'is_ostial', 'is_tortuous', 'is_cto', 'thrombus_present']:
                    col = column_mapping.get(field)
                    if col:
                        standard_row[field] = self.safe_convert_boolean(row.get(col))
                
                standard_data.append(standard_row)
                
            except Exception as e:
                print(f"  ⚠️  行 {idx+1} 处理异常: {str(e)}")
                continue
        
        # 创建标准DataFrame
        standard_df = pd.DataFrame(standard_data)
        
        print(f"\n✅ 转换完成!")
        print(f"转换后数据: {len(standard_df)} 行 x {len(standard_df.columns)} 列")
        
        # 显示转换预览
        if len(standard_df) > 0:
            print(f"\n📋 转换预览 (前3行):")
            print(standard_df.head(3).to_string())
        
        return standard_df
    
    def save_converted_file(self, df: pd.DataFrame, original_path: str) -> str:
        """保存转换后的文件"""
        original_path = Path(original_path)
        output_path = original_path.parent / f"{original_path.stem}_标准格式.xlsx"
        
        df.to_excel(output_path, index=False)
        print(f"\n💾 标准格式文件已保存: {output_path}")
        
        return str(output_path)

def main():
    """主函数"""
    print("🔧 智能Excel表格转换器")
    print("📋 自动识别您的表格格式并转换为标准模板")
    print("=" * 60)
    
    # 获取输入文件
    print("请输入您的Excel文件路径:")
    file_path = input("文件路径: ").strip().strip('"').strip("'")
    
    if not file_path:
        # 查找可能的文件
        possible_files = [
            "冠脉病变评分.xlsx", "冠脉数据.xlsx", "患者数据.xlsx",
            "data.xlsx", "病例.xlsx", "cases.xlsx"
        ]
        
        for possible_file in possible_files:
            if Path(possible_file).exists():
                file_path = possible_file
                print(f"自动找到文件: {file_path}")
                break
    
    if not file_path or not Path(file_path).exists():
        print("❌ 未找到Excel文件！")
        return
    
    try:
        # 创建转换器
        converter = IntelligentExcelConverter()
        
        # 转换文件
        standard_df = converter.convert_to_standard_format(file_path)
        
        if len(standard_df) == 0:
            print("❌ 转换失败，没有有效数据！")
            return
        
        # 保存标准格式文件
        standard_file = converter.save_converted_file(standard_df, file_path)
        
        # 询问是否立即进行评分
        print(f"\n🎯 转换成功！现在可以进行冠脉评分计算")
        choice = input("是否立即计算评分？(y/n): ").strip().lower()
        
        if choice in ['y', 'yes', '是', '1']:
            print("\n开始计算评分...")
            
            # 导入并使用处理器
            from single_sheet_processor_v2 import SingleSheetProcessor
            
            processor = SingleSheetProcessor()
            results, _ = processor.process_excel_file(standard_file)
            
            # 保存评分结果
            result_file = Path(file_path).parent / f"{Path(file_path).stem}_评分结果.xlsx"
            processor.export_results(results, result_file)
            
            print(f"\n🎉 评分完成！结果文件:")
            print(f"📄 {result_file}")
        
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()