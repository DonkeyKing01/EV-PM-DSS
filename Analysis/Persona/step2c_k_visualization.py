#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户画像分析 - 阶段二C：K值评估可视化
绘制各指标随K值变化的趋势图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from colorama import init, Fore
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class KValueVisualizer:
    """K值评估可视化器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.metrics_file = self.base_path / "Data" / "Analyzed" / "Persona" / "step2b_k_range_metrics.csv"
        self.labels_dir = self.base_path / "Data" / "Analyzed" / "Persona" / "clustering_labels"
        self.output_dir = self.base_path / "Data" / "Analyzed" / "Persona" / "trend_charts"
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据存储
        self.df_metrics = None
        self.cluster_sizes = {}
    
    def load_data(self):
        """加载数据"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "K值评估可视化")
        print(Fore.CYAN + "=" * 70)
        
        print(Fore.YELLOW + f"\n加载数据...")
        
        # 加载指标数据
        self.df_metrics = pd.read_csv(self.metrics_file, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 加载指标数据: {len(self.df_metrics)} 个K值")
        
        # 加载每个K的聚类大小
        print(Fore.YELLOW + f"加载聚类大小数据...")
        for k in self.df_metrics['k'].values:
            labels_file = self.labels_dir / f"clustering_labels_k{int(k)}.csv"
            if labels_file.exists():
                df_labels = pd.read_csv(labels_file, encoding='utf-8-sig')
                cluster_counts = df_labels['cluster'].value_counts().sort_index()
                self.cluster_sizes[int(k)] = cluster_counts.values
        print(Fore.GREEN + f"✓ 加载完成，共 {len(self.cluster_sizes)} 个K值")
    
    def plot_line(self, k_list, values, title, ylabel, filename, invert_y=False):
        """
        绘制折线图
        
        Args:
            k_list: K值列表
            values: 对应的指标值列表
            title: 图表标题
            ylabel: Y轴标签
            filename: 保存文件名
            invert_y: 是否反转Y轴（对于越小越好的指标）
        """
        plt.figure(figsize=(10, 6))
        
        # 绘制折线
        plt.plot(k_list, values, marker='o', linewidth=2, markersize=8, color='#2E86AB')
        
        # 标记最优值
        if invert_y:
            best_k = k_list[np.argmin(values)]
            best_value = min(values)
        else:
            best_k = k_list[np.argmax(values)]
            best_value = max(values)
        
        plt.scatter([best_k], [best_value], color='red', s=200, zorder=5, 
                   label=f'最优 K={best_k}', edgecolors='darkred', linewidths=2)
        
        # 设置标题和标签
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('聚类数 K', fontsize=12, fontweight='bold')
        plt.ylabel(ylabel, fontsize=12, fontweight='bold')
        
        # 网格
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 图例
        plt.legend(fontsize=10)
        
        # 设置X轴刻度
        plt.xticks(k_list)
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"  ✓ {filename}")
    
    def plot_bar_stacked(self, k_list, cluster_size_matrix, title, filename):
        """
        绘制堆叠柱状图显示聚类大小分布
        
        Args:
            k_list: K值列表
            cluster_size_matrix: 聚类大小矩阵 (K x max_clusters)
            title: 图表标题
            filename: 保存文件名
        """
        plt.figure(figsize=(14, 7))
        
        # 检查矩阵是否全为0
        if cluster_size_matrix.sum() == 0:
            print(Fore.RED + f"  ⚠ 警告: 聚类大小矩阵全为0，无法绘制")
            plt.close()
            return
        
        # 转换为百分比
        row_sums = cluster_size_matrix.sum(axis=1, keepdims=True)
        # 避免除以0
        row_sums[row_sums == 0] = 1
        cluster_size_pct = cluster_size_matrix / row_sums * 100
        
        # 获取最大聚类数
        n_clusters_max = cluster_size_matrix.shape[1]
        
        # 生成颜色
        colors = plt.cm.Set3(np.linspace(0, 1, n_clusters_max))
        
        # 绘制堆叠柱状图
        bottom = np.zeros(len(k_list))
        bars = []
        
        for i in range(n_clusters_max):
            # 只绘制非零的聚类
            if cluster_size_pct[:, i].sum() > 0:
                bar = plt.bar(k_list, cluster_size_pct[:, i], bottom=bottom, 
                             color=colors[i], edgecolor='white', linewidth=0.5,
                             label=f'Cluster {i}')
                bars.append(bar)
                bottom += cluster_size_pct[:, i]
        
        # 设置标题和标签
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('聚类数 K', fontsize=12, fontweight='bold')
        plt.ylabel('聚类大小占比 (%)', fontsize=12, fontweight='bold')
        
        # 网格
        plt.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 图例（放在右侧）
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                  fontsize=9, ncol=1)
        
        # 设置X轴刻度
        plt.xticks(k_list)
        
        # Y轴范围
        plt.ylim(0, 100)
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"  ✓ {filename}")
    
    def plot_stability_with_error(self, k_list, mean_values, std_values, title, ylabel, filename):
        """
        绘制带误差条的折线图（用于NMI和ARI）
        
        Args:
            k_list: K值列表
            mean_values: 均值列表
            std_values: 标准差列表
            title: 图表标题
            ylabel: Y轴标签
            filename: 保存文件名
        """
        plt.figure(figsize=(10, 6))
        
        # 绘制带误差条的折线
        plt.errorbar(k_list, mean_values, yerr=std_values, 
                    marker='o', linewidth=2, markersize=8, 
                    color='#2E86AB', ecolor='gray', 
                    capsize=5, capthick=2, alpha=0.8)
        
        # 标记最优值
        best_k = k_list[np.argmax(mean_values)]
        best_value = max(mean_values)
        plt.scatter([best_k], [best_value], color='red', s=200, zorder=5, 
                   label=f'最优 K={best_k}', edgecolors='darkred', linewidths=2)
        
        # 设置标题和标签
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('聚类数 K', fontsize=12, fontweight='bold')
        plt.ylabel(ylabel, fontsize=12, fontweight='bold')
        
        # 网格
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 图例
        plt.legend(fontsize=10)
        
        # 设置X轴刻度
        plt.xticks(k_list)
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"  ✓ {filename}")
    
    def create_all_visualizations(self):
        """创建所有可视化图表"""
        print(Fore.YELLOW + f"\n开始生成图表...")
        print(Fore.WHITE + f"保存路径: {self.output_dir}\n")
        
        # 提取数据
        k_list = self.df_metrics['k'].values
        silhouette_list = self.df_metrics['silhouette'].values
        db_list = self.df_metrics['davies_bouldin'].values
        ch_list = self.df_metrics['calinski_harabasz'].values
        nmi_mean = self.df_metrics['nmi_mean'].values
        nmi_std = self.df_metrics['nmi_std'].values
        ari_mean = self.df_metrics['ari_mean'].values
        ari_std = self.df_metrics['ari_std'].values
        
        # 1. Silhouette Score vs K
        print(Fore.WHITE + "生成图表 1/6: Silhouette Score")
        self.plot_line(
            k_list, silhouette_list, 
            "Silhouette Score vs K", 
            "Silhouette Score",
            "01_silhouette_vs_k.png"
        )
        
        # 2. Davies-Bouldin Index vs K
        print(Fore.WHITE + "生成图表 2/6: Davies-Bouldin Index")
        self.plot_line(
            k_list, db_list, 
            "Davies-Bouldin Index vs K", 
            "Davies-Bouldin Index",
            "02_davies_bouldin_vs_k.png",
            invert_y=True
        )
        
        # 3. Calinski-Harabasz Index vs K
        print(Fore.WHITE + "生成图表 3/6: Calinski-Harabasz Index")
        self.plot_line(
            k_list, ch_list, 
            "Calinski-Harabasz Index vs K", 
            "Calinski-Harabasz Index",
            "03_calinski_harabasz_vs_k.png"
        )
        
        # 4. Cluster Size Distribution
        print(Fore.WHITE + "生成图表 4/6: Cluster Size Distribution")
        
        # 检查是否有聚类大小数据
        if not self.cluster_sizes:
            print(Fore.RED + "  ⚠ 警告: 没有聚类大小数据，跳过此图表")
        else:
            # 找出最大的聚类数（即max(K)）
            max_clusters = max(len(sizes) for sizes in self.cluster_sizes.values())
            
            # 构建矩阵
            cluster_size_matrix = np.zeros((len(k_list), max_clusters))
            
            for i, k in enumerate(k_list):
                k_int = int(k)
                if k_int in self.cluster_sizes:
                    sizes = self.cluster_sizes[k_int]
                    cluster_size_matrix[i, :len(sizes)] = sizes
            
            self.plot_bar_stacked(
                k_list, cluster_size_matrix,
                "Cluster Size Distribution vs K",
                "04_cluster_size_vs_k.png"
            )
        
        # 5. NMI (Stability) vs K
        print(Fore.WHITE + "生成图表 5/6: NMI")
        self.plot_stability_with_error(
            k_list, nmi_mean, nmi_std,
            "NMI (Normalized Mutual Information) vs K",
            "NMI",
            "05_nmi_vs_k.png"
        )
        
        # 6. ARI (Stability) vs K
        print(Fore.WHITE + "生成图表 6/6: ARI")
        self.plot_stability_with_error(
            k_list, ari_mean, ari_std,
            "ARI (Adjusted Rand Index) vs K",
            "ARI",
            "06_ari_vs_k.png"
        )
        
        print(Fore.GREEN + f"\n✓ 所有图表生成完成！")
        print(Fore.CYAN + f"{'=' * 70}")
    
    def create_summary_dashboard(self):
        """创建综合仪表板（6个子图）"""
        print(Fore.YELLOW + f"\n生成综合仪表板...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('K值评估综合仪表板', fontsize=18, fontweight='bold', y=0.995)
        
        # 提取数据
        k_list = self.df_metrics['k'].values
        silhouette_list = self.df_metrics['silhouette'].values
        db_list = self.df_metrics['davies_bouldin'].values
        ch_list = self.df_metrics['calinski_harabasz'].values
        nmi_mean = self.df_metrics['nmi_mean'].values
        nmi_std = self.df_metrics['nmi_std'].values
        ari_mean = self.df_metrics['ari_mean'].values
        ari_std = self.df_metrics['ari_std'].values
        
        # 子图1: Silhouette
        ax1 = axes[0, 0]
        ax1.plot(k_list, silhouette_list, marker='o', linewidth=2, color='#2E86AB')
        best_k = k_list[np.argmax(silhouette_list)]
        ax1.scatter([best_k], [max(silhouette_list)], color='red', s=100, zorder=5)
        ax1.set_title('Silhouette Score', fontweight='bold')
        ax1.set_xlabel('K')
        ax1.set_ylabel('Score')
        ax1.grid(True, alpha=0.3)
        
        # 子图2: Davies-Bouldin
        ax2 = axes[0, 1]
        ax2.plot(k_list, db_list, marker='o', linewidth=2, color='#A23B72')
        best_k = k_list[np.argmin(db_list)]
        ax2.scatter([best_k], [min(db_list)], color='red', s=100, zorder=5)
        ax2.set_title('Davies-Bouldin Index', fontweight='bold')
        ax2.set_xlabel('K')
        ax2.set_ylabel('Index')
        ax2.grid(True, alpha=0.3)
        
        # 子图3: Calinski-Harabasz
        ax3 = axes[0, 2]
        ax3.plot(k_list, ch_list, marker='o', linewidth=2, color='#F18F01')
        best_k = k_list[np.argmax(ch_list)]
        ax3.scatter([best_k], [max(ch_list)], color='red', s=100, zorder=5)
        ax3.set_title('Calinski-Harabasz Index', fontweight='bold')
        ax3.set_xlabel('K')
        ax3.set_ylabel('Index')
        ax3.grid(True, alpha=0.3)
        
        # 子图4: NMI
        ax4 = axes[1, 0]
        ax4.errorbar(k_list, nmi_mean, yerr=nmi_std, marker='o', linewidth=2, 
                     color='#6A994E', capsize=5)
        best_k = k_list[np.argmax(nmi_mean)]
        ax4.scatter([best_k], [max(nmi_mean)], color='red', s=100, zorder=5)
        ax4.set_title('NMI (稳定性)', fontweight='bold')
        ax4.set_xlabel('K')
        ax4.set_ylabel('NMI')
        ax4.grid(True, alpha=0.3)
        
        # 子图5: ARI
        ax5 = axes[1, 1]
        ax5.errorbar(k_list, ari_mean, yerr=ari_std, marker='o', linewidth=2, 
                     color='#BC4B51', capsize=5)
        best_k = k_list[np.argmax(ari_mean)]
        ax5.scatter([best_k], [max(ari_mean)], color='red', s=100, zorder=5)
        ax5.set_title('ARI (稳定性)', fontweight='bold')
        ax5.set_xlabel('K')
        ax5.set_ylabel('ARI')
        ax5.grid(True, alpha=0.3)
        
        # 子图6: 聚类大小（箱线图）
        ax6 = axes[1, 2]
        cluster_sizes_list = []
        for k in k_list:
            sizes = self.cluster_sizes.get(k, [])
            if len(sizes) > 0:
                cluster_sizes_list.append(sizes)
            else:
                cluster_sizes_list.append([0])
        
        bp = ax6.boxplot(cluster_sizes_list, positions=k_list, widths=0.6,
                        patch_artist=True, showfliers=False)
        for patch in bp['boxes']:
            patch.set_facecolor('#8B5CF6')
            patch.set_alpha(0.6)
        ax6.set_title('聚类大小分布', fontweight='bold')
        ax6.set_xlabel('K')
        ax6.set_ylabel('样本数')
        ax6.grid(True, alpha=0.3, axis='y')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存
        save_path = self.output_dir / "00_dashboard_summary.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"✓ 综合仪表板已保存: 00_dashboard_summary.png")
    
    def run(self):
        """运行完整的可视化流程"""
        try:
            # 加载数据
            self.load_data()
            
            # 创建综合仪表板
            self.create_summary_dashboard()
            
            # 创建所有单独图表
            self.create_all_visualizations()
            
            print(Fore.CYAN + f"\n{'=' * 70}")
            print(Fore.GREEN + "可视化完成！")
            print(Fore.YELLOW + f"图表保存位置: {self.output_dir}")
            print(Fore.CYAN + f"{'=' * 70}")
            
        except Exception as e:
            print(Fore.RED + f"\n错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    visualizer = KValueVisualizer()
    visualizer.run()


if __name__ == '__main__':
    main()
