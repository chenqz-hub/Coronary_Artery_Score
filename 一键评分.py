"""
一键冠脉评分处理工具
自动识别您的Excel格式并完成评分计算
"""

import pandas as pd
from pathlib import Path
import sys
import os

def quick_coronary_scoring(file_path=None):
    """一键完成冠脉评分"""
    
    print("🏥 一键冠脉评分系统")
    print("📊 智能识别 + 自动转换 + 评分计算")
    print("=" * 50)
    
    # 如果没有提供文件路径，尝试自动查找
    if not file_path:
        print("🔍 自动查找Excel文件...")
        
        # 当前目录下查找可能的文件
        current_dir = Path('.')
        excel_files = []
        
        # 查找Excel文件
        for pattern in ['*.xlsx', '*.xls']:
            excel_files.extend(current_dir.glob(pattern))
        
        if not excel_files:
            print("❌ 当前目录未找到Excel文件")
            print("请将您的Excel文件放在当前目录下，文件名建议包含:")
            print("  - 冠脉、病变、患者、数据、评分等关键词")
            return False
        
        # 选择最可能的文件
        best_file = None
        for file in excel_files:
            name_lower = file.name.lower()
            if any(keyword in name_lower for keyword in 
                   ['冠脉', '病变', '患者', '数据', '评分', 'coronary', 'patient', 'data']):
                best_file = file
                break
        
        if not best_file:
            best_file = excel_files[0]  # 选择第一个文件
        
        file_path = str(best_file)
        print(f"📁 选择文件: {file_path}")
    
    try:
        # 导入智能转换器
        from 智能转换器 import IntelligentExcelConverter
        from single_sheet_processor_v2 import SingleSheetProcessor
        
        print(f"\n第一步: 智能分析Excel格式")
        print("-" * 30)
        
        # 创建转换器
        converter = IntelligentExcelConverter()
        
        # 转换为标准格式
        standard_df = converter.convert_to_standard_format(file_path)
        
        if len(standard_df) == 0:
            print("❌ 转换失败，请检查Excel文件格式")
            return False
        
        # 保存标准格式（临时文件）
        temp_standard_file = Path(file_path).parent / 'temp_standard_format.xlsx'
        standard_df.to_excel(temp_standard_file, index=False)
        
        print(f"\n第二步: 计算冠脉评分")
        print("-" * 30)
        
        # 创建评分处理器
        processor = SingleSheetProcessor()
        
        # 计算评分
        results, _ = processor.process_excel_file(temp_standard_file)
        
        # 保存最终结果
        original_path = Path(file_path)
        final_result_file = original_path.parent / f"{original_path.stem}_冠脉评分结果.xlsx"
        processor.export_results(results, final_result_file)
        
        # 清理临时文件
        if temp_standard_file.exists():
            temp_standard_file.unlink()
        
        print(f"\n🎉 评分完成！")
        print(f"📄 结果文件: {final_result_file}")
        
        # 显示评分汇总
        print(f"\n📊 评分汇总:")
        print("=" * 60)
        
        successful_cases = 0
        syntax_high_risk = 0
        cad_rads_severe = 0
        
        for i, result in enumerate(results, 1):
            if result['patient_data'] and 'error' not in result['scores']:
                successful_cases += 1
                scores = result['scores']
                
                # 统计高风险病例
                syntax_score = scores.get('SYNTAX', {}).get('score', 0)
                cad_rads_grade = scores.get('CAD_RADS', {}).get('grade', 0)
                
                if isinstance(syntax_score, (int, float)) and syntax_score > 32:
                    syntax_high_risk += 1
                
                if isinstance(cad_rads_grade, (int, float)) and cad_rads_grade >= 4:
                    cad_rads_severe += 1
                
                print(f"{i:2d}. {result['patient_id']:10s} | "
                      f"SYNTAX: {syntax_score:5.1f} | "
                      f"CAD-RADS: {cad_rads_grade:2d}级 | "
                      f"Gensini: {scores.get('Gensini', {}).get('score', 0):5.1f}")
        
        print("-" * 60)
        print(f"📈 统计摘要:")
        print(f"  总患者数: {len(results)}")
        print(f"  成功评分: {successful_cases}")
        print(f"  SYNTAX高风险 (>32分): {syntax_high_risk} 人")
        print(f"  重度狭窄 (CAD-RADS≥4级): {cad_rads_severe} 人")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
    print("请选择处理方式:")
    print("1. 自动查找并处理Excel文件")
    print("2. 手动指定文件路径")
    print("3. 退出")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == '1':
        # 自动处理
        success = quick_coronary_scoring()
        
    elif choice == '2':
        # 手动指定文件
        file_path = input("请输入Excel文件路径: ").strip().strip('"').strip("'")
        
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            return
        
        success = quick_coronary_scoring(file_path)
        
    elif choice == '3':
        print("👋 再见！")
        return
        
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("\n✅ 处理完成！请查看生成的结果文件")
    else:
        print("\n❌ 处理失败！请检查文件格式或联系技术支持")

if __name__ == "__main__":
    main()