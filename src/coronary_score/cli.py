"""
命令行接口

提供命令行工具用于计算冠脉评分。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .models.patient import PatientData
from .calculators import SyntaxCalculator, CadRadsCalculator, GensiniCalculator
from .data_io import DataImporter, DataExporter, create_sample_data


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='冠脉病变严重程度评分计算工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 计算SYNTAX评分
  coronary-score --input data.json --calculator syntax
  
  # 计算所有评分并导出结果
  coronary-score --input data.json --calculator all --output results.json
  
  # 创建示例数据
  coronary-score --create-sample --output sample.json
        '''
    )
    
    # 输入选项
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='输入数据文件路径 (支持JSON, CSV, Excel格式)'
    )
    
    # 输出选项
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出结果文件路径'
    )
    
    # 计算器选择
    parser.add_argument(
        '--calculator', '-c',
        choices=['syntax', 'cadrads', 'gensini', 'all'],
        default='all',
        help='选择评分计算器 (默认: all)'
    )
    
    # 创建示例数据
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='创建示例数据文件'
    )
    
    # 详细输出
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )
    
    # 验证数据
    parser.add_argument(
        '--validate',
        action='store_true',
        help='只验证数据不计算评分'
    )
    
    return parser


def load_data(input_path: str) -> List[PatientData]:
    """加载患者数据"""
    try:
        importer = DataImporter()
        patients = importer.import_from_file(input_path)
        return patients
    except Exception as e:
        print(f"错误: 加载数据失败 - {str(e)}", file=sys.stderr)
        sys.exit(1)


def calculate_scores(patients: List[PatientData], calculator_type: str) -> List[dict]:
    """计算评分"""
    results = []
    
    calculators = {}
    if calculator_type in ['syntax', 'all']:
        calculators['syntax'] = SyntaxCalculator()
    if calculator_type in ['cadrads', 'all']:
        calculators['cadrads'] = CadRadsCalculator()
    if calculator_type in ['gensini', 'all']:
        calculators['gensini'] = GensiniCalculator()
    
    for patient in patients:
        patient_result = {
            'patient_id': patient.patient_id,
            'patient_info': {
                'age': patient.age,
                'gender': patient.gender.value,
                'lesion_count': len(patient.lesions)
            },
            'scores': {}
        }
        
        # 计算各种评分
        for calc_name, calculator in calculators.items():
            try:
                if calc_name == 'syntax':
                    score_result = calculator.get_detailed_report(patient)
                elif calc_name == 'cadrads':
                    score_result = calculator.get_detailed_report(patient)
                elif calc_name == 'gensini':
                    score_result = calculator.get_detailed_report(patient)
                
                patient_result['scores'][calc_name] = score_result
                
            except Exception as e:
                patient_result['scores'][calc_name] = {
                    'error': f'计算失败: {str(e)}'
                }
        
        results.append(patient_result)
    
    return results


def save_results(results: List[dict], output_path: str):
    """保存结果"""
    try:
        output_file = Path(output_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"错误: 保存结果失败 - {str(e)}", file=sys.stderr)
        sys.exit(1)


def create_sample_file(output_path: str):
    """创建示例数据文件"""
    try:
        sample_patients = create_sample_data()
        exporter = DataExporter()
        exporter.export_to_file(sample_patients, output_path)
        
        print(f"示例数据已创建: {output_path}")
        
    except Exception as e:
        print(f"错误: 创建示例数据失败 - {str(e)}", file=sys.stderr)
        sys.exit(1)


def validate_data_only(patients: List[PatientData]) -> bool:
    """只验证数据"""
    from .utils.validation import validate_patient_data, check_data_consistency
    
    all_valid = True
    
    for i, patient in enumerate(patients):
        print(f"\n验证患者 {i+1} (ID: {patient.patient_id or 'N/A'})")
        
        # 基本验证
        is_valid, errors = validate_patient_data(patient)
        
        if is_valid:
            print("  ✓ 数据验证通过")
        else:
            print("  ✗ 数据验证失败:")
            for error in errors:
                print(f"    - {error}")
            all_valid = False
        
        # 一致性检查
        warnings = check_data_consistency(patient)
        if warnings:
            print("  ⚠ 数据一致性警告:")
            for warning in warnings:
                print(f"    - {warning}")
    
    return all_valid


def print_summary(results: List[dict], verbose: bool = False):
    """打印结果摘要"""
    print(f"\n处理了 {len(results)} 名患者的数据")
    print("=" * 60)
    
    for result in results:
        patient_id = result['patient_id'] or 'Unknown'
        patient_info = result['patient_info']
        
        print(f"\n患者: {patient_id}")
        print(f"  年龄: {patient_info['age']} 岁")
        print(f"  性别: {patient_info['gender']}")
        print(f"  病变数量: {patient_info['lesion_count']}")
        
        scores = result['scores']
        
        # SYNTAX评分
        if 'syntax' in scores:
            if 'error' in scores['syntax']:
                print(f"  SYNTAX评分: {scores['syntax']['error']}")
            else:
                syntax_result = scores['syntax']['scores']
                print(f"  SYNTAX评分: {syntax_result['total_score']} ({syntax_result['risk_category']})")
        
        # CAD-RADS评分
        if 'cadrads' in scores:
            if 'error' in scores['cadrads']:
                print(f"  CAD-RADS评分: {scores['cadrads']['error']}")
            else:
                cadrads_result = scores['cadrads']['cadrads_result']
                print(f"  CAD-RADS评分: {cadrads_result['overall_grade']}")
        
        # Gensini评分
        if 'gensini' in scores:
            if 'error' in scores['gensini']:
                print(f"  Gensini评分: {scores['gensini']['error']}")
            else:
                gensini_result = scores['gensini']['gensini_result']
                print(f"  Gensini评分: {gensini_result['total_score']} ({gensini_result['severity_grade']})")
        
        if verbose:
            print("  详细信息:")
            for calc_name, calc_result in scores.items():
                if 'error' not in calc_result:
                    print(f"    {calc_name.upper()}:")
                    # 这里可以添加更详细的输出


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 如果没有提供任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # 创建示例数据
    if args.create_sample:
        if not args.output:
            print("错误: 创建示例数据需要指定输出文件 (--output)", file=sys.stderr)
            sys.exit(1)
        
        create_sample_file(args.output)
        return
    
    # 需要输入文件
    if not args.input:
        print("错误: 需要指定输入文件 (--input)", file=sys.stderr)
        sys.exit(1)
    
    # 加载数据
    if args.verbose:
        print(f"正在加载数据: {args.input}")
    
    patients = load_data(args.input)
    
    if args.verbose:
        print(f"成功加载 {len(patients)} 名患者的数据")
    
    # 只验证数据
    if args.validate:
        is_valid = validate_data_only(patients)
        sys.exit(0 if is_valid else 1)
    
    # 计算评分
    if args.verbose:
        print(f"正在计算评分 (计算器: {args.calculator})")
    
    results = calculate_scores(patients, args.calculator)
    
    # 输出结果
    if args.output:
        save_results(results, args.output)
    
    # 打印摘要
    print_summary(results, args.verbose)


if __name__ == '__main__':
    main()