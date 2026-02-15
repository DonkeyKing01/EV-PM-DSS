#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户画像分析 - 阶段二：聚类分析
使用KMeans对用户attention向量进行聚类，并通过多种指标评估最优聚类数
"""

import pandas as pd
import numpy as np
from pathlib import Path
from colorama import init, Fore
import warnings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score, 
    davies_bouldin_score, 
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score
)
from sklearn.utils import resample
import json
from tqdm import tqdm

warnings.filterwarnings('ignore')
init(autoreset=True)


class PersonaClusteringAnalyzer:
    """用户画像聚类分析器"""
    
    def __init__(self, k_range=(5, 20), n_init_runs=30, n_bootstrap=30, bootstrap_ratio=0.8):
        """
        初始化聚类分析器
        
        Args:
            k_range: K值范围 (min, max)
            n_init_runs: 每个K值运行KMeans的次数（不同随机种子）
            n_bootstrap: Bootstrap重抽样次数
            bootstrap_ratio: Bootstrap抽样比例
        """
        self.base_path = Path(__file__).parent.parent.parent
        self.input_file = self.base_path / "Data" / "Analyzed" / "Persona" / "step1_attention_vectors.csv"
        self.output_dir = self.base_path / "Data" / "Analyzed" / "Persona" / 
        self.labels_dir = self.base_path / "Data" / "Analyzed" / "Persona" / "clustering_labels"
        
        # 聚类参数
        self.k_min, self.k_max = k_range
        self.n_init_runs = n_init_runs
        self.n_bootstrap = n_bootstrap
        self.bootstrap_ratio = bootstrap_ratio
        
        # 七个维度
        self.dimensions = [
            'w_appearance', 'w_interior', 'w_space', 
            'w_intelligence', 'w_driving', 'w_range', 'w_value'
        ]
        
        # 结果存储
        self.clustering_results = {}
        self.metrics_summary = []
    
    def clr_transform(self, X):
        """
        Step A: CLR (Centered Log-Ratio) 变换
        用于处理成分数据（compositional data），即和为1的数据
        
        CLR(x) = log(x / geometric_mean(x))
        
        Args:
            X: 原始数据 (n_samples, n_features)
            
        Returns:
            X_clr: CLR变换后的数据
        """
        # 添加小常数避免log(0)
        epsilon = 1e-6
        X_safe = X + epsilon
        
        # 计算几何平均
        geometric_mean = np.exp(np.mean(np.log(X_safe), axis=1, keepdims=True))
        
        # CLR变换
        X_clr = np.log(X_safe / geometric_mean)
        
        return X_clr
    
    def preprocess_data(self, df):
        """
        Step A: 预处理数据
        1. CLR变换
        2. 标准化
        
        Args:
            df: 包含persona向量的DataFrame
            
        Returns:
            X_processed: 预处理后的数据
            scaler: 标准化器（用于后续逆变换）
        """
        print(Fore.YELLOW + "\nStep A: 数据预处理")
        print(Fore.WHITE + "  1. 提取7维attention向量...")
        
        # 提取7维向量
        X = df[self.dimensions].values
        print(Fore.GREEN + f"    ✓ 数据形状: {X.shape}")
        
        # CLR变换
        print(Fore.WHITE + "  2. 执行CLR变换...")
        X_clr = self.clr_transform(X)
        print(Fore.GREEN + f"    ✓ CLR变换完成")
        
        # 标准化
        print(Fore.WHITE + "  3. 标准化数据...")
        scaler = StandardScaler()
        X_processed = scaler.fit_transform(X_clr)
        print(Fore.GREEN + f"    ✓ 标准化完成")
        print(Fore.GREEN + f"    ✓ 最终数据形状: {X_processed.shape}")
        
        return X_processed, scaler
    
    def run_kmeans_multiple_inits(self, X, k, random_state_base=42):
        """
        对给定的K值运行多次KMeans（不同随机种子）
        
        Args:
            X: 预处理后的数据
            k: 聚类数
            random_state_base: 随机种子基数
            
        Returns:
            best_model: 最佳模型
            all_models: 所有模型列表
        """
        models = []
        inertias = []
        
        for i in range(self.n_init_runs):
            model = KMeans(
                n_clusters=k, 
                random_state=random_state_base + i,
                n_init=10,
                max_iter=300
            )
            model.fit(X)
            models.append(model)
            inertias.append(model.inertia_)
        
        # 选择inertia最小的模型作为最佳模型
        best_idx = np.argmin(inertias)
        best_model = models[best_idx]
        
        return best_model, models
    
    def calculate_internal_metrics(self, X, labels):
        """
        计算内部评估指标
        
        Args:
            X: 数据
            labels: 聚类标签
            
        Returns:
            metrics: 指标字典
        """
        metrics = {}
        
        # Silhouette Score (越大越好, [-1, 1])
        metrics['silhouette'] = silhouette_score(X, labels)
        
        # Davies-Bouldin Index (越小越好, [0, +∞))
        metrics['davies_bouldin'] = davies_bouldin_score(X, labels)
        
        # Calinski-Harabasz Index (越大越好, [0, +∞))
        metrics['calinski_harabasz'] = calinski_harabasz_score(X, labels)
        
        return metrics
    
    def bootstrap_stability_test(self, X, k, base_labels):
        """
        Bootstrap重抽样稳定性检验
        
        Args:
            X: 原始数据
            k: 聚类数
            base_labels: 全样本模型的标签
            
        Returns:
            stability_metrics: 稳定性指标
        """
        n_samples = X.shape[0]
        sample_size = int(n_samples * self.bootstrap_ratio)
        
        nmi_scores = []
        ari_scores = []
        
        for i in range(self.n_bootstrap):
            # Bootstrap抽样
            indices = resample(
                np.arange(n_samples), 
                n_samples=sample_size, 
                random_state=42 + i
            )
            X_boot = X[indices]
            
            # 在bootstrap样本上运行KMeans
            model_boot = KMeans(
                n_clusters=k, 
                random_state=42 + i,
                n_init=10,
                max_iter=300
            )
            labels_boot = model_boot.fit_predict(X_boot)
            
            # 计算与原始标签的一致性
            base_labels_boot = base_labels[indices]
            
            # NMI: Normalized Mutual Information
            nmi = normalized_mutual_info_score(base_labels_boot, labels_boot)
            nmi_scores.append(nmi)
            
            # ARI: Adjusted Rand Index
            ari = adjusted_rand_score(base_labels_boot, labels_boot)
            ari_scores.append(ari)
        
        stability_metrics = {
            'nmi_mean': np.mean(nmi_scores),
            'nmi_std': np.std(nmi_scores),
            'ari_mean': np.mean(ari_scores),
            'ari_std': np.std(ari_scores)
        }
        
        return stability_metrics
    
    def cluster_for_k(self, X, k):
        """
        Step B: 对给定的K值进行完整聚类分析
        
        Args:
            X: 预处理后的数据
            k: 聚类数
            
        Returns:
            result: 包含所有指标的结果字典
        """
        print(Fore.CYAN + f"\n{'─' * 70}")
        print(Fore.CYAN + f"  K = {k}")
        print(Fore.CYAN + f"{'─' * 70}")
        
        # 1. 运行多次KMeans
        print(Fore.WHITE + f"  运行KMeans {self.n_init_runs}次（不同随机种子）...")
        best_model, all_models = self.run_kmeans_multiple_inits(X, k)
        labels = best_model.labels_
        print(Fore.GREEN + f"    ✓ 完成，选择了inertia最小的模型")
        
        # 2. 计算内部指标
        print(Fore.WHITE + f"  计算内部评估指标...")
        internal_metrics = self.calculate_internal_metrics(X, labels)
        print(Fore.GREEN + f"    ✓ Silhouette: {internal_metrics['silhouette']:.4f}")
        print(Fore.GREEN + f"    ✓ Davies-Bouldin: {internal_metrics['davies_bouldin']:.4f}")
        print(Fore.GREEN + f"    ✓ Calinski-Harabasz: {internal_metrics['calinski_harabasz']:.2f}")
        
        # 3. Bootstrap稳定性检验
        print(Fore.WHITE + f"  进行Bootstrap稳定性检验 ({self.n_bootstrap}次)...")
        stability_metrics = self.bootstrap_stability_test(X, k, labels)
        print(Fore.GREEN + f"    ✓ NMI: {stability_metrics['nmi_mean']:.4f} ± {stability_metrics['nmi_std']:.4f}")
        print(Fore.GREEN + f"    ✓ ARI: {stability_metrics['ari_mean']:.4f} ± {stability_metrics['ari_std']:.4f}")
        
        # 4. 汇总结果
        result = {
            'k': k,
            'inertia': best_model.inertia_,
            'silhouette': internal_metrics['silhouette'],
            'davies_bouldin': internal_metrics['davies_bouldin'],
            'calinski_harabasz': internal_metrics['calinski_harabasz'],
            'nmi_mean': stability_metrics['nmi_mean'],
            'nmi_std': stability_metrics['nmi_std'],
            'ari_mean': stability_metrics['ari_mean'],
            'ari_std': stability_metrics['ari_std'],
            'model': best_model,
            'labels': labels,
            'cluster_sizes': np.bincount(labels)
        }
        
        # 显示聚类大小分布
        print(Fore.WHITE + f"  聚类大小分布:")
        for cluster_id, size in enumerate(result['cluster_sizes']):
            percentage = size / len(labels) * 100
            print(Fore.WHITE + f"    Cluster {cluster_id}: {size} ({percentage:.1f}%)")
        
        return result
    
    def analyze_all_k_values(self):
        """
        Step B: 对所有K值进行聚类分析
        """
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "Step B: 聚类分析 - 评估K值范围")
        print(Fore.CYAN + "=" * 70)
        print(Fore.YELLOW + f"\nK值范围: {self.k_min} - {self.k_max}")
        print(Fore.YELLOW + f"每个K值运行次数: {self.n_init_runs}")
        print(Fore.YELLOW + f"Bootstrap次数: {self.n_bootstrap} (抽样比例: {self.bootstrap_ratio})")
        
        # 读取数据
        print(Fore.YELLOW + f"\n正在读取数据: {self.input_file.name}")
        df = pd.read_csv(self.input_file, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 成功读取 {len(df)} 条数据")
        
        # 预处理
        X_processed, scaler = self.preprocess_data(df)
        
        # 对每个K值进行分析
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.CYAN + "开始聚类分析")
        print(Fore.CYAN + f"{'=' * 70}")
        
        for k in range(self.k_min, self.k_max + 1):
            result = self.cluster_for_k(X_processed, k)
            self.clustering_results[k] = result
            
            # 添加到汇总列表
            self.metrics_summary.append({
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
        
        # 保存结果
        self.save_results(df)
        
        # 分析最优K值
        self.analyze_optimal_k()
        
        return self.clustering_results, self.metrics_summary
    
    def save_results(self, df_original):
        """保存分析结果"""
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.YELLOW + "保存结果...")
        print(Fore.CYAN + f"{'=' * 70}")
        
        # 确保labels目录存在
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存指标汇总
        metrics_file = self.output_dir / "clustering_metrics.csv"
        df_metrics = pd.DataFrame(self.metrics_summary)
        df_metrics.to_csv(metrics_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 指标汇总已保存: {metrics_file.name}")
        
        # 2. 保存每个K值的标签
        for k, result in self.clustering_results.items():
            labels_file = self.labels_dir / f"clustering_labels_k{k}.csv"
            df_labels = df_original[['review_id']].copy()
            df_labels['cluster'] = result['labels']
            df_labels.to_csv(labels_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 所有K值的标签已保存到: {self.labels_dir.name}/clustering_labels_k*.csv")
        
        # 3. 保存详细报告
        report_file = self.output_dir / "clustering_report.json"
        report = {
            'parameters': {
                'k_range': [self.k_min, self.k_max],
                'n_init_runs': self.n_init_runs,
                'n_bootstrap': self.n_bootstrap,
                'bootstrap_ratio': self.bootstrap_ratio
            },
            'metrics_summary': self.metrics_summary
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(Fore.GREEN + f"✓ 详细报告已保存: {report_file.name}")
    
    def analyze_optimal_k(self):
        """分析并推荐最优K值"""
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.CYAN + "最优K值分析")
        print(Fore.CYAN + f"{'=' * 70}")
        
        df_metrics = pd.DataFrame(self.metrics_summary)
        
        # 标准化指标（使所有指标方向一致：越大越好）
        # Silhouette: 越大越好（已满足）
        # Davies-Bouldin: 越小越好 -> 取负数
        # Calinski-Harabasz: 越大越好（已满足）
        # NMI/ARI: 越大越好（已满足）
        
        df_metrics['silhouette_norm'] = (df_metrics['silhouette'] - df_metrics['silhouette'].min()) / \
                                         (df_metrics['silhouette'].max() - df_metrics['silhouette'].min())
        
        df_metrics['davies_bouldin_norm'] = (df_metrics['davies_bouldin'].max() - df_metrics['davies_bouldin']) / \
                                             (df_metrics['davies_bouldin'].max() - df_metrics['davies_bouldin'].min())
        
        df_metrics['calinski_harabasz_norm'] = (df_metrics['calinski_harabasz'] - df_metrics['calinski_harabasz'].min()) / \
                                                (df_metrics['calinski_harabasz'].max() - df_metrics['calinski_harabasz'].min())
        
        df_metrics['nmi_norm'] = (df_metrics['nmi_mean'] - df_metrics['nmi_mean'].min()) / \
                                  (df_metrics['nmi_mean'].max() - df_metrics['nmi_mean'].min())
        
        df_metrics['ari_norm'] = (df_metrics['ari_mean'] - df_metrics['ari_mean'].min()) / \
                                  (df_metrics['ari_mean'].max() - df_metrics['ari_mean'].min())
        
        # 综合得分（加权平均）
        weights = {
            'silhouette': 0.25,
            'davies_bouldin': 0.20,
            'calinski_harabasz': 0.20,
            'nmi': 0.20,
            'ari': 0.15
        }
        
        df_metrics['composite_score'] = (
            weights['silhouette'] * df_metrics['silhouette_norm'] +
            weights['davies_bouldin'] * df_metrics['davies_bouldin_norm'] +
            weights['calinski_harabasz'] * df_metrics['calinski_harabasz_norm'] +
            weights['nmi'] * df_metrics['nmi_norm'] +
            weights['ari'] * df_metrics['ari_norm']
        )
        
        # 找出最优K值
        best_k_composite = df_metrics.loc[df_metrics['composite_score'].idxmax(), 'k']
        best_k_silhouette = df_metrics.loc[df_metrics['silhouette'].idxmax(), 'k']
        best_k_davies_bouldin = df_metrics.loc[df_metrics['davies_bouldin'].idxmin(), 'k']
        best_k_calinski = df_metrics.loc[df_metrics['calinski_harabasz'].idxmax(), 'k']
        
        print(Fore.YELLOW + "\n各指标推荐的最优K值:")
        print(Fore.WHITE + f"  综合得分最优: K = {int(best_k_composite)}")
        print(Fore.WHITE + f"  Silhouette最优: K = {int(best_k_silhouette)}")
        print(Fore.WHITE + f"  Davies-Bouldin最优: K = {int(best_k_davies_bouldin)}")
        print(Fore.WHITE + f"  Calinski-Harabasz最优: K = {int(best_k_calinski)}")
        
        print(Fore.YELLOW + f"\n前5个K值的综合得分:")
        top5 = df_metrics.nlargest(5, 'composite_score')[['k', 'composite_score', 'silhouette', 
                                                            'davies_bouldin', 'nmi_mean', 'ari_mean']]
        for idx, row in top5.iterrows():
            print(Fore.WHITE + f"  K={int(row['k'])}: 得分={row['composite_score']:.4f}, "
                  f"Silhouette={row['silhouette']:.4f}, "
                  f"DB={row['davies_bouldin']:.4f}, "
                  f"NMI={row['nmi_mean']:.4f}")
        
        print(Fore.GREEN + f"\n{'=' * 70}")
        print(Fore.GREEN + f"推荐使用 K = {int(best_k_composite)} 作为最优聚类数")
        print(Fore.GREEN + f"{'=' * 70}")


def main():
    """主函数"""
    # 创建分析器
    analyzer = PersonaClusteringAnalyzer(
        k_range=(5, 20),      # K值范围
        n_init_runs=30,       # 每个K运行30次
        n_bootstrap=30,       # Bootstrap 30次
        bootstrap_ratio=0.8   # 80%抽样
    )
    
    # 执行分析
    results, metrics = analyzer.analyze_all_k_values()
    
    print(Fore.CYAN + f"\n{'=' * 70}")
    print(Fore.GREEN + "聚类分析完成！")
    print(Fore.CYAN + f"{'=' * 70}")


if __name__ == '__main__':
    main()
