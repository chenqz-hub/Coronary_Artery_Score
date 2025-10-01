"""
临床冠脉造影数据库处理器
专门处理包含详细血管段信息的临床数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

class ClinicalCoronaryProcessor:
    """临床冠脉数据处理器"""
    
    def __init__(self):
        # 血管节段映射
        self.vessel_segments = {
            '右冠近段': 'RCA_PROXIMAL',
            '右冠中段': 'RCA_MID', 
            '右冠远段': 'RCA_DISTAL',
            '右冠-后降支': 'RCA_PDA',
            '右冠-左室后侧支': 'RCA_PLV',
            '左主干': 'LM',
            '左冠-前降支近段': 'LAD_PROXIMAL',
            '左冠-前降支中段': 'LAD_MID',
            '左冠-前降支远段': 'LAD_DISTAL',
            '左冠-第一对角支': 'LAD_D1',
            '左冠-第二对角支': 'LAD_D2',
            '左冠-回旋支近段': 'LCX_PROXIMAL',
            '左冠-回旋支中段': 'LCX_MID',
            '左冠-回旋支远段': 'LCX_DISTAL',
            '左冠-第一钝缘支': 'LCX_OM1',
            '左冠-第二钝缘支': 'LCX_OM2'
        }
        
        # SYNTAX评分权重（基于AHA分段）
        self.syntax_weights = {
            'LM': 5.0,
            'LAD_PROXIMAL': 3.5,
            'LAD_MID': 2.5,
            'LAD_DISTAL': 1.0,
            'LAD_D1': 1.0,
            'LAD_D2': 0.5,
            'LCX_PROXIMAL': 3.5,
            'LCX_MID': 2.5,
            'LCX_DISTAL': 1.0,
            'LCX_OM1': 1.0,
            'LCX_OM2': 0.5,
            'RCA_PROXIMAL': 3.5,
            'RCA_MID': 2.5,
            'RCA_DISTAL': 1.0,
            'RCA_PDA': 1.0,
            'RCA_PLV': 0.5
        }
        
    def extract_stenosis_info(self, text: str) -> Dict:
        """从文本描述中提取狭窄信息"""
        if pd.isna(text) or text in ['正常', '未见明显狭窄', 'NaN']:
            return {'stenosis_percent': 0, 'features': []}
        
        text = str(text).strip()
        stenosis_info = {'stenosis_percent': 0, 'features': []}
        
        # 提取狭窄百分比
        percentages = re.findall(r'(\d+)[-~]*(\d*)[%％]', text)
        if percentages:
            # 取最高的狭窄百分比
            max_stenosis = 0
            for match in percentages:
                if match[1]:  # 范围形式 "90-95%"
                    stenosis = max(int(match[0]), int(match[1]))
                else:  # 单个数字 "90%"
                    stenosis = int(match[0])
                max_stenosis = max(max_stenosis, stenosis)
            stenosis_info['stenosis_percent'] = max_stenosis
        
        # 识别狭窄程度描述
        elif '完全闭塞' in text or 'CTO' in text or '100%' in text:
            stenosis_info['stenosis_percent'] = 100
        elif '次全闭塞' in text or '次全阻塞' in text:
            stenosis_info['stenosis_percent'] = 95
        elif '严重狭窄' in text or '重度狭窄' in text:
            stenosis_info['stenosis_percent'] = 90
        elif '中重度狭窄' in text:
            stenosis_info['stenosis_percent'] = 80
        elif '中度狭窄' in text:
            stenosis_info['stenosis_percent'] = 70
        elif '轻中度狭窄' in text:
            stenosis_info['stenosis_percent'] = 60
        elif '轻度狭窄' in text:
            stenosis_info['stenosis_percent'] = 50
        elif '管壁不规则' in text or '斑块' in text:
            stenosis_info['stenosis_percent'] = 30
        
        # 识别病变特征
        features = []
        if '分叉' in text or '分岔' in text:
            features.append('bifurcation')
        if '钙化' in text:
            features.append('calcified')
        if '血栓' in text:
            features.append('thrombus')
        if '迂曲' in text or '扭曲' in text:
            features.append('tortuous')
        if '开口' in text or '起始' in text:
            features.append('ostial')
        if '弥漫性' in text or '弥散性' in text:
            features.append('diffuse')
        if 'CTO' in text or '慢性闭塞' in text:
            features.append('cto')
        
        stenosis_info['features'] = features
        return stenosis_info
    
    def process_patient_record(self, row: pd.Series) -> Dict:
        """处理单个患者记录"""
        
        # 基本信息
        patient_data = {
            'patient_id': str(row.get('入组编号', row.get('入组ID', 'Unknown'))),
            'name': str(row.get('姓名', '')),
            'age': int(row.get('当前年龄', 65)),
            'gender': 'male' if row.get('性别') == 1 else 'female',
            'exam_date': str(row.get('冠脉造影日期', '')),
            'lesions': []
        }
        
        # 处理每个血管节段
        significant_lesions = []
        
        for segment_name, segment_code in self.vessel_segments.items():
            if segment_name in row and pd.notna(row[segment_name]):
                stenosis_info = self.extract_stenosis_info(row[segment_name])
                
                if stenosis_info['stenosis_percent'] > 0:  # 只记录有狭窄的节段
                    lesion = {
                        'segment': segment_code,
                        'segment_name': segment_name,
                        'stenosis_percent': stenosis_info['stenosis_percent'],
                        'description': str(row[segment_name]),
                        'features': stenosis_info['features'],
                        'weight': self.syntax_weights.get(segment_code, 1.0)
                    }
                    significant_lesions.append(lesion)
        
        patient_data['lesions'] = significant_lesions
        
        # 添加总结信息
        patient_data['conclusion'] = str(row.get('冠脉造影结论', ''))
        
        return patient_data
    
    def calculate_syntax_score(self, patient_data: Dict) -> Dict:
        """计算SYNTAX评分"""
        total_score = 0
        lesion_scores = []
        
        for lesion in patient_data['lesions']:
            if lesion['stenosis_percent'] < 50:
                continue  # SYNTAX只计算≥50%的病变
            
            # 基础评分 = 权重 × 狭窄系数
            stenosis = lesion['stenosis_percent']
            weight = lesion['weight']
            
            # 狭窄系数
            if stenosis >= 100:
                stenosis_factor = 5.0
            elif stenosis >= 99:
                stenosis_factor = 5.0
            elif stenosis >= 90:
                stenosis_factor = 2.0
            elif stenosis >= 70:
                stenosis_factor = 1.5
            else:
                stenosis_factor = 1.0
            
            base_score = weight * stenosis_factor
            
            # 复杂性加分
            complexity_score = 0
            for feature in lesion['features']:
                if feature == 'bifurcation':
                    complexity_score += 1.0
                elif feature == 'calcified':
                    complexity_score += 2.0
                elif feature == 'cto':
                    complexity_score += 5.0
                elif feature == 'ostial':
                    complexity_score += 0.5
                elif feature == 'tortuous':
                    complexity_score += 1.0
                elif feature == 'thrombus':
                    complexity_score += 1.0
                elif feature == 'diffuse':
                    complexity_score += 1.0
            
            lesion_score = base_score + complexity_score
            total_score += lesion_score
            
            lesion_scores.append({
                'segment': lesion['segment_name'],
                'stenosis': stenosis,
                'base_score': round(base_score, 2),
                'complexity_score': round(complexity_score, 2),
                'total_score': round(lesion_score, 2)
            })
        
        # 风险分层
        if total_score <= 22:
            risk_category = 'Low'
            risk_description = '低风险 - 适合PCI治疗'
        elif total_score <= 32:
            risk_category = 'Intermediate'  
            risk_description = '中等风险 - PCI和CABG均可考虑'
        else:
            risk_category = 'High'
            risk_description = '高风险 - 优先考虑CABG治疗'
        
        return {
            'total_score': round(total_score, 1),
            'risk_category': risk_category,
            'risk_description': risk_description,
            'lesion_details': lesion_scores
        }
    
    def calculate_cad_rads_grade(self, patient_data: Dict) -> Dict:
        """计算CAD-RADS分级"""
        max_stenosis = 0
        vessel_grades = {}
        
        for lesion in patient_data['lesions']:
            stenosis = lesion['stenosis_percent']
            max_stenosis = max(max_stenosis, stenosis)
            
            # 血管分级
            vessel = lesion['segment'].split('_')[0]  # 获取主血管名
            
            if stenosis >= 100:
                grade = 5
            elif stenosis >= 70:
                grade = 4
            elif stenosis >= 50:
                grade = 3
            elif stenosis >= 25:
                grade = 2
            elif stenosis > 0:
                grade = 1
            else:
                grade = 0
            
            if vessel not in vessel_grades:
                vessel_grades[vessel] = grade
            else:
                vessel_grades[vessel] = max(vessel_grades[vessel], grade)
        
        # 整体分级
        if max_stenosis >= 100:
            overall_grade = 5
            description = "完全闭塞"
            recommendation = "建议血管造影，考虑血运重建"
        elif max_stenosis >= 70:
            overall_grade = 4
            description = "重度狭窄"
            recommendation = "建议血管造影，考虑血运重建"
        elif max_stenosis >= 50:
            overall_grade = 3
            description = "中度狭窄"
            recommendation = "考虑功能学检查评估心肌缺血"
        elif max_stenosis >= 25:
            overall_grade = 2
            description = "轻度狭窄"
            recommendation = "药物治疗，控制危险因素"
        elif max_stenosis > 0:
            overall_grade = 1
            description = "轻微病变"
            recommendation = "生活方式干预，控制危险因素"
        else:
            overall_grade = 0
            description = "无冠脉病变"
            recommendation = "无需特殊处理"
        
        return {
            'overall_grade': overall_grade,
            'max_stenosis': max_stenosis,
            'vessel_grades': vessel_grades,
            'description': description,
            'recommendation': recommendation
        }
    
    def calculate_gensini_score(self, patient_data: Dict) -> Dict:
        """计算Gensini评分"""
        total_score = 0
        vessel_scores = {}
        
        # Gensini权重映射
        gensini_weights = {
            'LM': 5.0,
            'LAD_PROXIMAL': 2.5,
            'LAD_MID': 1.5,
            'LAD_DISTAL': 1.0,
            'LAD_D1': 1.0,
            'LAD_D2': 0.5,
            'LCX_PROXIMAL': 2.5,
            'LCX_MID': 1.5,
            'LCX_DISTAL': 1.0,
            'LCX_OM1': 1.0,
            'LCX_OM2': 0.5,
            'RCA_PROXIMAL': 1.0,
            'RCA_MID': 1.0,
            'RCA_DISTAL': 1.0,
            'RCA_PDA': 1.0,
            'RCA_PLV': 0.5
        }
        
        for lesion in patient_data['lesions']:
            stenosis = lesion['stenosis_percent']
            segment = lesion['segment']
            
            # 狭窄程度评分
            if stenosis >= 99:
                stenosis_score = 32
            elif stenosis >= 90:
                stenosis_score = 16
            elif stenosis >= 75:
                stenosis_score = 8
            elif stenosis >= 50:
                stenosis_score = 4
            elif stenosis >= 25:
                stenosis_score = 2
            else:
                stenosis_score = 1
            
            # 血管权重
            weight = gensini_weights.get(segment, 1.0)
            
            lesion_score = stenosis_score * weight
            total_score += lesion_score
            
            vessel = segment.split('_')[0]
            if vessel not in vessel_scores:
                vessel_scores[vessel] = 0
            vessel_scores[vessel] += lesion_score
        
        # 严重程度分级
        if total_score == 0:
            severity_grade = 'Normal'
            severity_description = '无病变'
        elif total_score <= 20:
            severity_grade = 'Mild'
            severity_description = '轻度病变'
        elif total_score <= 40:
            severity_grade = 'Moderate'
            severity_description = '中度病变'
        elif total_score <= 80:
            severity_grade = 'Severe'
            severity_description = '重度病变'
        else:
            severity_grade = 'Critical'
            severity_description = '极重度病变'
        
        return {
            'total_score': round(total_score, 1),
            'vessel_scores': vessel_scores,
            'severity_grade': severity_grade,
            'severity_description': severity_description
        }
    
    def process_clinical_data(self, file_path: str) -> List[Dict]:
        """处理完整的临床数据文件"""
        
        print("🏥 开始处理临床冠脉造影数据")
        print("=" * 60)
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"✓ 读取数据: {len(df)} 名患者")
        
        results = []
        valid_count = 0
        
        for idx, row in df.iterrows():
            try:
                # 处理患者数据
                patient_data = self.process_patient_record(row)
                
                if len(patient_data['lesions']) == 0:
                    continue  # 跳过无病变的患者
                
                valid_count += 1
                
                # 计算评分
                syntax_result = self.calculate_syntax_score(patient_data)
                cad_rads_result = self.calculate_cad_rads_grade(patient_data)
                gensini_result = self.calculate_gensini_score(patient_data)
                
                result = {
                    'patient_id': patient_data['patient_id'],
                    'name': patient_data['name'],
                    'age': patient_data['age'],
                    'gender': patient_data['gender'],
                    'exam_date': patient_data['exam_date'],
                    'lesion_count': len(patient_data['lesions']),
                    'lesions': patient_data['lesions'],
                    'syntax_score': syntax_result,
                    'cad_rads_grade': cad_rads_result,
                    'gensini_score': gensini_result,
                    'conclusion': patient_data['conclusion']
                }
                
                results.append(result)
                
                if valid_count <= 10:  # 显示前10个患者的详情
                    print(f"\n患者 {valid_count}: {patient_data['name']} ({patient_data['patient_id']})")
                    print(f"  年龄性别: {patient_data['age']}岁 {patient_data['gender']}")
                    print(f"  病变数量: {len(patient_data['lesions'])}处")
                    
                    for lesion in patient_data['lesions'][:3]:  # 显示前3处病变
                        features_str = ', '.join(lesion['features']) if lesion['features'] else '无特殊'
                        print(f"    {lesion['segment_name']}: {lesion['stenosis_percent']}% ({features_str})")
                    
                    print(f"  SYNTAX: {syntax_result['total_score']} ({syntax_result['risk_category']})")
                    print(f"  CAD-RADS: {cad_rads_result['overall_grade']}级")
                    print(f"  Gensini: {gensini_result['total_score']} ({gensini_result['severity_grade']})")
                
            except Exception as e:
                print(f"  ⚠️ 患者 {idx+1} 处理失败: {str(e)}")
                continue
        
        print(f"\n✅ 处理完成！")
        print(f"有效患者数: {valid_count}/{len(df)}")
        
        return results

def main():
    """主函数"""
    print("🏥 临床冠脉造影数据处理器")
    print("专门处理详细的临床造影数据库")
    print("=" * 60)
    
    # 处理data目录下的文件
    file_path = 'data/冠脉病变评分.xlsx'
    
    try:
        processor = ClinicalCoronaryProcessor()
        results = processor.process_clinical_data(file_path)
        
        if not results:
            print("❌ 未找到有效的病变数据")
            return
        
        # 生成统计报告
        print(f"\n📊 数据统计报告:")
        print("-" * 40)
        
        syntax_scores = [r['syntax_score']['total_score'] for r in results]
        cad_rads_grades = [r['cad_rads_grade']['overall_grade'] for r in results]
        gensini_scores = [r['gensini_score']['total_score'] for r in results]
        
        print(f"总患者数: {len(results)}")
        print(f"SYNTAX评分 - 平均: {np.mean(syntax_scores):.1f}, 最高: {max(syntax_scores):.1f}")
        print(f"高风险患者 (SYNTAX>32): {len([s for s in syntax_scores if s > 32])}人")
        print(f"重度狭窄 (CAD-RADS≥4): {len([g for g in cad_rads_grades if g >= 4])}人")
        print(f"Gensini评分 - 平均: {np.mean(gensini_scores):.1f}, 最高: {max(gensini_scores):.1f}")
        
        # 保存结果到Excel
        output_data = []
        for result in results:
            output_data.append({
                'patient_id': result['patient_id'],
                'name': result['name'],
                'age': result['age'],
                'gender': result['gender'],
                'lesion_count': result['lesion_count'],
                'SYNTAX_score': result['syntax_score']['total_score'],
                'SYNTAX_risk': result['syntax_score']['risk_category'],
                'CAD_RADS_grade': result['cad_rads_grade']['overall_grade'],
                'CAD_RADS_desc': result['cad_rads_grade']['description'],
                'Gensini_score': result['gensini_score']['total_score'],
                'Gensini_severity': result['gensini_score']['severity_grade'],
                'conclusion': result['conclusion'][:100] + '...' if len(result['conclusion']) > 100 else result['conclusion']
            })
        
        output_df = pd.DataFrame(output_data)
        output_path = 'data/临床冠脉评分结果.xlsx'
        output_df.to_excel(output_path, index=False)
        
        print(f"\n📄 结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()