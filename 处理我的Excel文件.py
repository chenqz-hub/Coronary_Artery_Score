"""
自定义Excel文件处理器
直接处理您提供的Excel文件
"""

import pandas as pd
import sys
from pathlib import Path

# 导入处理器类
sys.path.append('.')
from single_sheet_processor_v2 import SingleSheetProcessor

def process_your_excel_file(file_path):
    """处理您的Excel文件"""
    
    print("🏥 冠脉病变评分系统")
    print("📋 正在处理您的Excel文件...")
    print("=" * 60)
    
    # 检查文件是否存在
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        print("请确认文件路径正确！")
        return
    
    try:
        # 创建处理器
        processor = SingleSheetProcessor()
        
        # 处理文件
        results, original_df = processor.process_excel_file(file_path)
        
        # 生成结果文件
        output_file = file_path.parent / f"{file_path.stem}_评分结果.xlsx"
        processor.export_results(results, output_file)
        
        print(f"\n📊 评分完成！结果已保存到：")
        print(f"📄 {output_file}")
        
        # 显示评分汇总
        print(f"\n📈 评分汇总报告：")
        print("=" * 60)
        
        syntax_scores = []
        cad_rads_grades = []
        gensini_scores = []
        
        for i, result in enumerate(results, 1):
            if result['patient_data'] and 'error' not in result['scores']:
                scores = result['scores']
                patient_id = result['patient_id']
                
                print(f"\n{i:2d}. 患者 {patient_id}:")
                
                # 获取评分
                syntax_score = scores.get('SYNTAX', {}).get('score', 'N/A')
                syntax_class = scores.get('SYNTAX', {}).get('class', 'N/A')
                cad_rads_grade = scores.get('CAD_RADS', {}).get('grade', 'N/A')  
                gensini_score = scores.get('Gensini', {}).get('score', 'N/A')
                gensini_class = scores.get('Gensini', {}).get('class', 'N/A')
                
                print(f"    SYNTAX:   {syntax_score} ({syntax_class})")
                print(f"    CAD-RADS: {cad_rads_grade}级")
                print(f"    Gensini:  {gensini_score} ({gensini_class})")
                
                # 收集统计数据
                if isinstance(syntax_score, (int, float)):
                    syntax_scores.append(syntax_score)
                if isinstance(cad_rads_grade, (int, float)):
                    cad_rads_grades.append(cad_rads_grade)
                if isinstance(gensini_score, (int, float)):
                    gensini_scores.append(gensini_score)
        
        # 统计摘要
        if syntax_scores or cad_rads_grades or gensini_scores:
            print(f"\n📊 统计摘要：")
            print("-" * 40)
            print(f"总患者数: {len(results)}")
            
            if syntax_scores:
                avg_syntax = sum(syntax_scores) / len(syntax_scores)
                high_risk_count = len([s for s in syntax_scores if s > 32])
                print(f"SYNTAX平均分: {avg_syntax:.1f}")
                print(f"高风险患者: {high_risk_count}人")
            
            if cad_rads_grades:
                severe_count = len([g for g in cad_rads_grades if g >= 4])
                print(f"重度狭窄(≥4级): {severe_count}人")
            
            if gensini_scores:
                avg_gensini = sum(gensini_scores) / len(gensini_scores)
                print(f"Gensini平均分: {avg_gensini:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数 - 处理用户的Excel文件"""
    
    print("请输入您的Excel文件路径:")
    print("例如: C:\\Users\\用户名\\Desktop\\冠脉数据.xlsx")
    print("或者: data/your_file.xlsx")
    print()
    
    # 获取文件路径
    file_path = input("Excel文件路径: ").strip().strip('"').strip("'")
    
    if not file_path:
        # 如果没有输入，尝试查找常见文件
        possible_files = [
            "冠脉病变评分.xlsx",
            "data/冠脉病变评分.xlsx", 
            "冠脉数据.xlsx",
            "data/冠脉数据.xlsx",
            "患者数据.xlsx",
            "data/患者数据.xlsx"
        ]
        
        print("未指定文件，尝试查找常见文件名...")
        
        for possible_file in possible_files:
            if Path(possible_file).exists():
                print(f"找到文件: {possible_file}")
                file_path = possible_file
                break
        
        if not file_path:
            print("❌ 未找到Excel文件")
            print("请将您的Excel文件重命名为 '冠脉病变评分.xlsx' 并放在当前目录")
            return
    
    # 处理文件
    success = process_your_excel_file(file_path)
    
    if success:
        print("\n✅ 评分完成！")
        print("📋 请查看生成的结果文件获取详细评分数据")
    else:
        print("\n❌ 评分失败！")
        print("请检查Excel文件格式是否正确")

if __name__ == "__main__":
    main()