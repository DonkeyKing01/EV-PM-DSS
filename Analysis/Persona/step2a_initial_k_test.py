#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
聚类分析 - 快速测试版本
仅测试K=5,10,15三个值，每个K运行5次，Bootstrap 5次
用于快速验证代码正确性
"""

import sys
from pathlib import Path
from colorama import init, Fore

init(autoreset=True)

sys.path.insert(0, str(Path(__file__).parent))

from step2b_k_range_eval import PersonaClusteringAnalyzer


def main():
    """快速测试版本"""
    
    print(Fore.CYAN + "=" * 70)
    print(Fore.CYAN + "聚类分析 - 快速测试模式")
    print(Fore.CYAN + "=" * 70)
    print(Fore.YELLOW + "\n测试参数：")
    print(Fore.WHITE + "  K值: 5, 10, 15")
    print(Fore.WHITE + "  每个K运行: 5次")
    print(Fore.WHITE + "  Bootstrap: 5次")
    print(Fore.YELLOW + "\n注意: 这是快速测试模式，不用于正式分析\n")
    
    # 创建测试分析器
    analyzer = PersonaClusteringAnalyzer(
        k_range=(5, 15),      # 只测试3个K值
        n_init_runs=5,        # 每个K只运行5次
        n_bootstrap=5,        # Bootstrap只5次
        bootstrap_ratio=0.8
    )
    
    # 修改k_range使其只测试5, 10, 15
    test_k_values = [5, 10, 15]
    
    import pandas as pd
    import numpy as np
    
    # 读取数据
    print(Fore.YELLOW + f"正在读取数据...")
    df = pd.read_csv(analyzer.input_file, encoding='utf-8-sig')
    print(Fore.GREEN + f"✓ 成功读取 {len(df)} 条数据")
    
    # 预处理
    X_processed, scaler = analyzer.preprocess_data(df)
    
    # 只测试指定的K值
    print(Fore.CYAN + f"\n{'=' * 70}")
    print(Fore.CYAN + "开始测试聚类")
    print(Fore.CYAN + f"{'=' * 70}")
    
    for k in test_k_values:
        result = analyzer.cluster_for_k(X_processed, k)
        analyzer.clustering_results[k] = result
        
        analyzer.metrics_summary.append({
            'k': k,
            'inertia': result['inertia'],
            'silhouette': result['silhouette'],
            'davies_bouldin': result['davies_bouldin'],
            'calinski_harabasz': result['calinski_harabasz'],
            'nmi_mean': result['nmi_mean'],
            'nmi_std': result['nmi_std'],
            'ari_mean': result['ari_mean'],
            'ari_std': result['ari_std']
        })
    
    # 保存测试结果
    print(Fore.YELLOW + "\n保存测试结果...")
    
    # 指标汇总
    metrics_file = analyzer.output_dir / "step2a_initial_k_metrics.csv"
    df_metrics = pd.DataFrame(analyzer.metrics_summary)
    df_metrics.to_csv(metrics_file, index=False, encoding='utf-8-sig')
    print(Fore.GREEN + f"✓ 测试指标已保存: {metrics_file.name}")
    
    # 显示结果对比
    print(Fore.CYAN + f"\n{'=' * 70}")
    print(Fore.CYAN + "测试结果对比")
    print(Fore.CYAN + f"{'=' * 70}")
    
    for _, row in df_metrics.iterrows():
        print(Fore.YELLOW + f"\nK = {int(row['k'])}")
        print(Fore.WHITE + f"  Silhouette:        {row['silhouette']:.4f}")
        print(Fore.WHITE + f"  Davies-Bouldin:    {row['davies_bouldin']:.4f}")
        print(Fore.WHITE + f"  Calinski-Harabasz: {row['calinski_harabasz']:.2f}")
        print(Fore.WHITE + f"  NMI:               {row['nmi_mean']:.4f} ± {row['nmi_std']:.4f}")
        print(Fore.WHITE + f"  ARI:               {row['ari_mean']:.4f} ± {row['ari_std']:.4f}")
    
    print(Fore.GREEN + f"\n{'=' * 70}")
    print(Fore.GREEN + "快速测试完成！")
    print(Fore.YELLOW + "如需完整分析，请运行: python persona_clustering.py")
    print(Fore.GREEN + f"{'=' * 70}")


if __name__ == '__main__':
    main()
