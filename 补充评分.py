#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import numpy as np

def main():
    # 读取原始数据和现有结果
    df = pd.read_excel('data/冠脉病变评分.xlsx')
    result_df = pd.read_excel('data/临床冠脉评分结果.xlsx')

    # 遗漏的患者编号
    missing_codes = [3161, 2926, 2861, 2047, 1074]

    print('=== 补充遗漏患者评分 ===')

    # 血管段权重映射（基于SYNTAX评分系统）
    vessel_weights = {
        '左主干': {'syntax': 5, 'gensini': 5},
        '左冠-前降支近段': {'syntax': 3.5, 'gensini': 2.5},
        '左冠-前降支中段': {'syntax': 2.5, 'gensini': 1.5},
        '左冠-前降支远段': {'syntax': 1, 'gensini': 1},
        '左冠-第一对角支': {'syntax': 1, 'gensini': 1},
        '左冠-第二对角支': {'syntax': 0.5, 'gensini': 0.5},
        '左冠-回旋支近段': {'syntax': 3.5, 'gensini': 2.5},
        '左冠-回旋支中段': {'syntax': 2.5, 'gensini': 1.5},
        '左冠-回旋支远段': {'syntax': 1, 'gensini': 1},
        '左冠-第一钝缘支': {'syntax': 1, 'gensini': 1},
        '左冠-第二钝缘支': {'syntax': 0.5, 'gensini': 0.5},
        '右冠近段': {'syntax': 3.5, 'gensini': 1},
        '右冠中段': {'syntax': 2.5, 'gensini': 1},
        '右冠远段': {'syntax': 1, 'gensini': 1},
        '右冠-后降支': {'syntax': 1, 'gensini': 1},
        '右冠-左室后侧支': {'syntax': 0.5, 'gensini': 0.5}
    }

    def extract_stenosis_percentage(description):
        """从描述中提取狭窄百分比"""
        if pd.isna(description) or str(description).strip() == '':
            return 0
        
        desc = str(description).strip()
        
        # 明确无狭窄的情况
        if any(keyword in desc for keyword in ['未见狭窄', '无狭窄', '未见明显狭窄', '未见显著狭窄', '无明显狭窄']):
            return 0
        
        # 提取百分比数字
        percentages = re.findall(r'(\d+)%', desc)
        if percentages:
            return max([int(p) for p in percentages])
        
        # 根据描述判断狭窄程度
        if any(keyword in desc for keyword in ['轻度狭窄', '轻微狭窄']):
            return 30
        elif any(keyword in desc for keyword in ['中度狭窄', '中等狭窄']):
            return 60
        elif any(keyword in desc for keyword in ['重度狭窄', '严重狭窄']):
            return 85
        elif any(keyword in desc for keyword in ['次全闭塞', '亚全闭']):
            return 95
        elif any(keyword in desc for keyword in ['完全闭塞', '全闭', '闭塞']):
            return 100
        
        return 0

    def calculate_scores(patient_row):
        """计算患者的各种评分"""
        syntax_score = 0
        gensini_score = 0
        lesion_count = 0
        max_stenosis = 0
        
        # 遍历所有血管段
        for vessel in vessel_weights.keys():
            if vessel in df.columns:
                stenosis = extract_stenosis_percentage(patient_row[vessel])
                if stenosis > 0:
                    lesion_count += 1
                    max_stenosis = max(max_stenosis, stenosis)
                    
                    # SYNTAX评分计算
                    if stenosis >= 50:
                        syntax_score += vessel_weights[vessel]['syntax']
                        if stenosis >= 90:
                            syntax_score += vessel_weights[vessel]['syntax'] * 0.5
                    
                    # Gensini评分计算
                    if stenosis < 25:
                        stenosis_factor = 1
                    elif stenosis < 50:
                        stenosis_factor = 2
                    elif stenosis < 75:
                        stenosis_factor = 4
                    elif stenosis < 90:
                        stenosis_factor = 8
                    elif stenosis < 99:
                        stenosis_factor = 16
                    else:
                        stenosis_factor = 32
                    
                    gensini_score += vessel_weights[vessel]['gensini'] * stenosis_factor
        
        # CAD-RADS分级
        if max_stenosis == 0:
            cad_rads = 1
            cad_desc = 'Normal'
        elif max_stenosis < 25:
            cad_rads = 2
            cad_desc = 'Minimal stenosis'
        elif max_stenosis < 50:
            cad_rads = 3
            cad_desc = 'Mild-moderate stenosis'
        elif max_stenosis < 70:
            cad_rads = 4
            cad_desc = 'Moderate-severe stenosis'
        else:
            cad_rads = 5
            cad_desc = 'Severe stenosis or occlusion'
        
        return {
            'syntax_score': round(syntax_score, 1),
            'gensini_score': round(gensini_score, 1),
            'lesion_count': lesion_count,
            'cad_rads': cad_rads,
            'cad_desc': cad_desc
        }

    new_rows = []

    for code in missing_codes:
        # 找到患者数据
        patient_row = df[df['入组编号'] == code].iloc[0]
        
        name = patient_row['姓名']
        age = patient_row['当前年龄'] if pd.notna(patient_row['当前年龄']) else 'Unknown'
        gender = patient_row['性别'] if pd.notna(patient_row['性别']) else 'Unknown'
        conclusion = patient_row['冠脉造影结论'] if pd.notna(patient_row['冠脉造影结论']) else 'No conclusion'
        
        # 计算评分
        scores = calculate_scores(patient_row)
        
        print(f'患者 {name} (编号{code}):')
        print(f'  SYNTAX评分: {scores["syntax_score"]}')
        print(f'  Gensini评分: {scores["gensini_score"]}')
        print(f'  病变数量: {scores["lesion_count"]}')
        print(f'  CAD-RADS: {scores["cad_rads"]} ({scores["cad_desc"]})')
        
        # 创建新行
        new_row = {
            'patient_id': code,
            'name': name,
            'age': age,
            'gender': gender,
            'lesion_count': scores['lesion_count'],
            'SYNTAX_score': scores['syntax_score'],
            'SYNTAX_risk': 'Low' if scores['syntax_score'] <= 22 else 'Intermediate' if scores['syntax_score'] <= 32 else 'High',
            'CAD_RADS_grade': scores['cad_rads'],
            'CAD_RADS_desc': scores['cad_desc'],
            'Gensini_score': scores['gensini_score'],
            'Gensini_severity': 'Minimal' if scores['gensini_score'] <= 20 else 'Moderate' if scores['gensini_score'] <= 100 else 'Severe',
            'conclusion': conclusion
        }
        
        new_rows.append(new_row)

    # 将新患者添加到结果中
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        updated_result = pd.concat([result_df, new_df], ignore_index=True)
        
        # 按patient_id排序
        updated_result = updated_result.sort_values('patient_id').reset_index(drop=True)
        
        # 保存更新后的结果
        updated_result.to_excel('data/临床冠脉评分结果_完整版.xlsx', index=False)
        
        print(f'\n✅ 成功补充{len(new_rows)}位患者的评分')
        print(f'更新后总数: {len(updated_result)}位患者')
        print('保存为: data/临床冠脉评分结果_完整版.xlsx')
        
        # 统计更新
        print(f'\n=== 更新统计 ===')
        print(f'原始结果: {len(result_df)}位患者')
        print(f'补充患者: {len(new_rows)}位患者')
        print(f'最终结果: {len(updated_result)}位患者')
        print(f'覆盖率: {len(updated_result)}/209 = {len(updated_result)/209*100:.1f}%')
        
        # 显示新的统计摘要
        print(f'\n=== 完整版统计摘要 ===')
        total_patients = len(updated_result)
        high_syntax = len(updated_result[updated_result['SYNTAX_score'] > 32])
        severe_cad = len(updated_result[updated_result['CAD_RADS_grade'] >= 4])
        
        print(f'总患者数: {total_patients}')
        print(f'SYNTAX高危(>32分): {high_syntax} 位 ({high_syntax/total_patients*100:.1f}%)')
        print(f'重度狭窄(CAD-RADS≥4): {severe_cad} 位 ({severe_cad/total_patients*100:.1f}%)')
        print(f'平均SYNTAX评分: {updated_result["SYNTAX_score"].mean():.1f}')
        print(f'平均Gensini评分: {updated_result["Gensini_score"].mean():.1f}')
        
    else:
        print('未找到需要补充的患者')

if __name__ == "__main__":
    main()