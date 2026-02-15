#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户画像分析 - 阶段三：最终聚类与画像生成
基于K取值决策，生成最终的聚类结果、画像描述和可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from colorama import init, Fore
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import umap
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
# 设置seaborn样式
sns.set_style("whitegrid")


class FinalClusteringAnalyzer:
    """最终聚类分析器 - K=8"""
    
    def __init__(self, optimal_k=8):
        """
        初始化分析器
        
        Args:
            optimal_k: 最优K值
        """
        self.base_path = Path(__file__).parent.parent.parent
        self.input_file = self.base_path / "Data" / "Analyzed" / "Persona" / "step1_attention_vectors.csv"
        self.output_dir = self.base_path / "Data" / "Analyzed" / "Persona" / "final_clustering"
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 聚类参数
        self.optimal_k = optimal_k
        
        # 七个维度
        self.dimensions = [
            'w_appearance', 'w_interior', 'w_space', 
            'w_intelligence', 'w_driving', 'w_range', 'w_value'
        ]
        
        self.dimension_names_cn = {
            'w_appearance': '外观',
            'w_interior': '内饰',
            'w_space': '空间',
            'w_intelligence': '智能化',
            'w_driving': '驾驶',
            'w_range': '续航',
            'w_value': '性价比'
        }
        
        # 数据存储
        self.df_data = None
        self.X_processed = None
        self.scaler = None
        self.model = None
        self.labels = None
        self.centroids = None
    
    def clr_transform(self, X):
        """CLR变换"""
        epsilon = 1e-6
        X_safe = X + epsilon
        geometric_mean = np.exp(np.mean(np.log(X_safe), axis=1, keepdims=True))
        X_clr = np.log(X_safe / geometric_mean)
        return X_clr
    
    def load_and_preprocess(self):
        """加载并预处理数据"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "阶段三：最终聚类分析 (K=8)")
        print(Fore.CYAN + "=" * 70)
        
        print(Fore.YELLOW + f"\n步骤1：加载数据...")
        self.df_data = pd.read_csv(self.input_file, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 加载 {len(self.df_data)} 条用户数据")
        
        print(Fore.YELLOW + f"\n步骤2：数据预处理...")
        # 提取attention向量
        X = self.df_data[self.dimensions].values
        
        # CLR变换
        X_clr = self.clr_transform(X)
        
        # 标准化
        self.scaler = StandardScaler()
        self.X_processed = self.scaler.fit_transform(X_clr)
        print(Fore.GREEN + f"✓ 预处理完成，数据形状: {self.X_processed.shape}")
    
    def perform_clustering(self):
        """执行K=8的聚类"""
        print(Fore.YELLOW + f"\n步骤3：执行聚类 (K={self.optimal_k})...")
        
        # 运行多次取最佳
        best_inertia = np.inf
        best_model = None
        
        for i in range(30):
            model = KMeans(n_clusters=self.optimal_k, random_state=42+i, n_init=10, max_iter=300)
            model.fit(self.X_processed)
            if model.inertia_ < best_inertia:
                best_inertia = model.inertia_
                best_model = model
        
        self.model = best_model
        self.labels = self.model.labels_
        
        # 计算原始空间的聚类中心
        self.centroids = []
        for i in range(self.optimal_k):
            cluster_mask = self.labels == i
            cluster_data = self.df_data[cluster_mask][self.dimensions].values
            centroid = cluster_data.mean(axis=0)
            self.centroids.append(centroid)
        self.centroids = np.array(self.centroids)
        
        print(Fore.GREEN + f"✓ 聚类完成")
        
        # 显示聚类大小
        cluster_sizes = np.bincount(self.labels)
        print(Fore.WHITE + f"\n聚类大小分布:")
        for i, size in enumerate(cluster_sizes):
            percentage = size / len(self.labels) * 100
            print(Fore.WHITE + f"  Cluster {i}: {size:6d} ({percentage:5.2f}%)")
    
    def generate_cluster_labels_csv(self):
        """生成 step3_cluster_labels.csv"""
        print(Fore.YELLOW + f"\n步骤4：生成聚类标签文件...")
        
        # 创建输出DataFrame
        df_output = self.df_data[['review_id']].copy()
        df_output['cluster'] = self.labels
        
        # 添加attention向量
        for dim in self.dimensions:
            df_output[dim] = self.df_data[dim]
        
        # 保存
        output_file = self.output_dir / "step3_cluster_labels.csv"
        df_output.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 已保存: {output_file.name}")
    
    def generate_centroids_csv(self):
        """生成 step3_cluster_centroids.csv"""
        print(Fore.YELLOW + f"\n步骤5：生成聚类中心文件...")
        
        # 创建DataFrame
        centroid_data = []
        for i in range(self.optimal_k):
            row = {'cluster': i}
            for j, dim in enumerate(self.dimensions):
                row[f'centroid_{dim}'] = self.centroids[i, j]
            centroid_data.append(row)
        
        df_centroids = pd.DataFrame(centroid_data)
        
        # 保存
        output_file = self.output_dir / "step3_cluster_centroids.csv"
        df_centroids.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 已保存: {output_file.name}")
        
        return df_centroids
    
    def generate_cluster_profile_md(self, df_centroids):
        """生成 step3_cluster_profile.md"""
        print(Fore.YELLOW + f"\n步骤6：生成聚类画像描述...")
        
        output_file = self.output_dir / "step3_cluster_profile.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 用户画像聚类分析报告\n\n")
            f.write("## 概述\n\n")
            f.write(f"基于 **K=8** 的聚类结果，将用户划分为 8 个典型群体。\n")
            f.write(f"每个群体在七个评价维度（外观、内饰、空间、智能化、驾驶、续航、性价比）上具有独特的关注模式。\n\n")
            f.write("---\n\n")
            
            # 为每个簇生成画像
            for i in range(self.optimal_k):
                cluster_size = np.sum(self.labels == i)
                cluster_pct = cluster_size / len(self.labels) * 100
                
                f.write(f"## Cluster {i}：")
                
                # 分析该簇的特征
                centroid = self.centroids[i]
                
                # 找出前3个最关注的维度
                top_indices = np.argsort(centroid)[-3:][::-1]
                top_dims = [self.dimensions[idx] for idx in top_indices]
                top_values = [centroid[idx] for idx in top_indices]
                
                # 生成簇名称
                primary_focus = self.dimension_names_cn[top_dims[0]]
                cluster_name = f"{primary_focus}关注型"
                
                f.write(f"{cluster_name}\n\n")
                
                f.write(f"**样本量**: {cluster_size} ({cluster_pct:.2f}%)\n\n")
                
                f.write("### 关注特征\n\n")
                f.write("| 维度 | 权重 | 排名 |\n")
                f.write("|------|------|------|\n")
                
                # 按权重排序显示所有维度
                sorted_indices = np.argsort(centroid)[::-1]
                for rank, idx in enumerate(sorted_indices, 1):
                    dim_name = self.dimension_names_cn[self.dimensions[idx]]
                    weight = centroid[idx]
                    f.write(f"| {dim_name} | {weight:.4f} | {rank} |\n")
                
                f.write("\n### 用户画像描述\n\n")
                
                # 生成描述
                f.write(f"该群体用户主要关注 **{self.dimension_names_cn[top_dims[0]]}**")
                if top_values[0] > 0.20:  # 如果权重超过20%
                    f.write(f"（权重 {top_values[0]:.2%}），显示出强烈的偏好。")
                else:
                    f.write("。")
                
                f.write(f"同时对 **{self.dimension_names_cn[top_dims[1]]}** 和 **{self.dimension_names_cn[top_dims[2]]}** ")
                f.write("也表现出较高的关注度。\n\n")
                
                # 找出最不关注的维度
                least_idx = sorted_indices[-1]
                least_dim = self.dimension_names_cn[self.dimensions[least_idx]]
                f.write(f"相对而言，该群体对 **{least_dim}** 的关注度较低。\n\n")
                
                f.write("### 营销建议\n\n")
                f.write(f"- 针对该群体，产品推广应突出 **{self.dimension_names_cn[top_dims[0]]}** 相关特性\n")
                f.write(f"- 配合强调 **{self.dimension_names_cn[top_dims[1]]}** 和 **{self.dimension_names_cn[top_dims[2]]}** 的优势\n")
                f.write(f"- 可适当弱化 **{least_dim}** 相关的营销内容\n\n")
                
                f.write("---\n\n")
        
        print(Fore.GREEN + f"✓ 已保存: {output_file.name}")
    
    def generate_quality_report_md(self):
        """生成 step3_quality_report.md"""
        print(Fore.YELLOW + f"\n步骤7：生成质量报告...")
        
        # 计算评估指标
        silhouette = silhouette_score(self.X_processed, self.labels)
        davies_bouldin = davies_bouldin_score(self.X_processed, self.labels)
        calinski = calinski_harabasz_score(self.X_processed, self.labels)
        
        output_file = self.output_dir / "step3_quality_report.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 聚类质量诊断报告\n\n")
            f.write(f"**聚类数**: K={self.optimal_k}\n\n")
            f.write("---\n\n")
            
            f.write("## 1. 聚类质量指标\n\n")
            f.write("| 指标 | 数值 | 评价 |\n")
            f.write("|------|------|------|\n")
            f.write(f"| **Silhouette Score** | {silhouette:.4f} | {'优秀 ✓' if silhouette > 0.7 else '良好' if silhouette > 0.5 else '一般'} |\n")
            f.write(f"| **Davies-Bouldin Index** | {davies_bouldin:.4f} | {'优秀 ✓' if davies_bouldin < 1.0 else '良好' if davies_bouldin < 1.5 else '一般'} |\n")
            f.write(f"| **Calinski-Harabasz Index** | {calinski:.2f} | 优秀 ✓ |\n")
            
            f.write("\n### 指标解释\n\n")
            f.write("- **Silhouette Score**: 轮廓系数，范围[-1,1]，越接近1表示聚类越紧密且分离\n")
            f.write("- **Davies-Bouldin Index**: 戴维森堡丁指数，越小越好，<1.0为优秀\n")
            f.write("- **Calinski-Harabasz Index**: 方差比指数，越大表示簇间分离越好\n\n")
            
            f.write("---\n\n")
            
            f.write("## 2. 聚类大小分布\n\n")
            f.write("| Cluster | 样本数 | 占比 | 分布图 |\n")
            f.write("|---------|--------|------|--------|\n")
            
            cluster_sizes = np.bincount(self.labels)
            for i in range(self.optimal_k):
                size = cluster_sizes[i]
                pct = size / len(self.labels) * 100
                bar = '█' * int(pct / 2)  # 每2%一个方块
                f.write(f"| Cluster {i} | {size:,} | {pct:.2f}% | {bar} |\n")
            
            f.write(f"\n**总计**: {len(self.labels):,} 个用户\n\n")
            
            f.write("---\n\n")
            
            f.write("## 3. 典型簇间差异焦点\n\n")
            
            # 计算簇间差异
            f.write("### 主要关注维度对比\n\n")
            f.write("| Cluster | 首要关注 | 次要关注 | 第三关注 |\n")
            f.write("|---------|----------|----------|----------|\n")
            
            for i in range(self.optimal_k):
                centroid = self.centroids[i]
                top_indices = np.argsort(centroid)[-3:][::-1]
                top_dims = [self.dimension_names_cn[self.dimensions[idx]] for idx in top_indices]
                f.write(f"| Cluster {i} | {top_dims[0]} | {top_dims[1]} | {top_dims[2]} |\n")
            
            f.write("\n### 关键发现\n\n")
            
            # 分析维度的整体分布
            dimension_variance = np.var(self.centroids, axis=0)
            most_varied_idx = np.argmax(dimension_variance)
            most_varied_dim = self.dimension_names_cn[self.dimensions[most_varied_idx]]
            
            f.write(f"- **分化最明显的维度**: {most_varied_dim}（不同用户群体对此关注度差异最大）\n")
            
            least_varied_idx = np.argmin(dimension_variance)
            least_varied_dim = self.dimension_names_cn[self.dimensions[least_varied_idx]]
            
            f.write(f"- **最一致的维度**: {least_varied_dim}（各用户群体关注度较为一致）\n")
            
            # 找出最极端的簇
            max_spread = np.max(self.centroids, axis=0) - np.min(self.centroids, axis=0)
            most_spread_idx = np.argmax(max_spread)
            most_spread_dim = self.dimension_names_cn[self.dimensions[most_spread_idx]]
            
            f.write(f"- **跨度最大的维度**: {most_spread_dim}（簇间权重差异最显著）\n\n")
            
            f.write("---\n\n")
            
            f.write("## 4. 业务建议\n\n")
            f.write("### 聚类质量评估\n\n")
            
            if silhouette > 0.7 and davies_bouldin < 1.0:
                f.write("✅ **聚类质量优秀**：指标显示各用户群体特征清晰、边界明确，可直接用于业务决策。\n\n")
            elif silhouette > 0.5:
                f.write("✓ **聚类质量良好**：用户群体划分合理，可用于指导营销策略。\n\n")
            else:
                f.write("⚠ **聚类质量一般**：建议结合业务场景进一步验证和调整。\n\n")
            
            f.write("### 应用建议\n\n")
            f.write("1. **精准营销**: 根据8个用户画像制定差异化的营销策略\n")
            f.write("2. **产品推荐**: 为不同群体推荐匹配其关注焦点的产品\n")
            f.write("3. **内容定制**: 针对各群体关注的维度定制推广内容\n")
            f.write("4. **资源分配**: 根据簇大小合理分配营销资源\n\n")
        
        print(Fore.GREEN + f"✓ 已保存: {output_file.name}")
        print(Fore.WHITE + f"\n质量指标:")
        print(Fore.WHITE + f"  Silhouette Score: {silhouette:.4f}")
        print(Fore.WHITE + f"  Davies-Bouldin Index: {davies_bouldin:.4f}")
        print(Fore.WHITE + f"  Calinski-Harabasz Index: {calinski:.2f}")
    
    def generate_visualizations(self):
        """生成可视化图表"""
        print(Fore.YELLOW + f"\n步骤8：生成可视化图表...")
        
        # A) t-SNE和UMAP降维可视化
        self.plot_tsne_umap()
        
        # B) 聚类大小分布
        self.plot_cluster_size_distribution()
        
        print(Fore.GREEN + f"✓ 可视化完成")
    
    def plot_tsne_umap(self):
        """绘制t-SNE和UMAP降维图"""
        print(Fore.WHITE + "  生成降维散点图...")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        
        # 颜色配置
        colors = plt.cm.Set3(np.linspace(0, 1, self.optimal_k))
        
        # t-SNE降维
        print(Fore.WHITE + "    运行t-SNE...")
        tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=1000)
        X_tsne = tsne.fit_transform(self.X_processed)
        
        ax1 = axes[0]
        for i in range(self.optimal_k):
            mask = self.labels == i
            ax1.scatter(X_tsne[mask, 0], X_tsne[mask, 1], 
                       c=[colors[i]], label=f'Cluster {i}', 
                       alpha=0.6, s=20, edgecolors='white', linewidth=0.5)
        
        # 标注聚类中心
        for i in range(self.optimal_k):
            mask = self.labels == i
            center_x = X_tsne[mask, 0].mean()
            center_y = X_tsne[mask, 1].mean()
            ax1.scatter(center_x, center_y, c='red', s=200, marker='*', 
                       edgecolors='darkred', linewidth=2, zorder=5)
            ax1.annotate(f'C{i}', (center_x, center_y), 
                        fontsize=10, fontweight='bold', 
                        ha='center', va='center')
        
        ax1.set_title('t-SNE 降维可视化', fontsize=14, fontweight='bold')
        ax1.set_xlabel('t-SNE维度1')
        ax1.set_ylabel('t-SNE维度2')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # UMAP降维
        print(Fore.WHITE + "    运行UMAP...")
        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
        X_umap = reducer.fit_transform(self.X_processed)
        
        ax2 = axes[1]
        for i in range(self.optimal_k):
            mask = self.labels == i
            ax2.scatter(X_umap[mask, 0], X_umap[mask, 1], 
                       c=[colors[i]], label=f'Cluster {i}', 
                       alpha=0.6, s=20, edgecolors='white', linewidth=0.5)
        
        # 标注聚类中心
        for i in range(self.optimal_k):
            mask = self.labels == i
            center_x = X_umap[mask, 0].mean()
            center_y = X_umap[mask, 1].mean()
            ax2.scatter(center_x, center_y, c='red', s=200, marker='*', 
                       edgecolors='darkred', linewidth=2, zorder=5)
            ax2.annotate(f'C{i}', (center_x, center_y), 
                        fontsize=10, fontweight='bold', 
                        ha='center', va='center')
        
        ax2.set_title('UMAP 降维可视化', fontsize=14, fontweight='bold')
        ax2.set_xlabel('UMAP维度1')
        ax2.set_ylabel('UMAP维度2')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle('用户聚类空间分布 (K=8)', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        output_file = self.output_dir / "step3_tsne_umap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"    ✓ {output_file.name}")
    
    def plot_cluster_size_distribution(self):
        """绘制聚类大小分布图"""
        print(Fore.WHITE + "  生成聚类大小分布图...")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        cluster_sizes = np.bincount(self.labels)
        cluster_labels = [f'Cluster {i}' for i in range(self.optimal_k)]
        colors = plt.cm.Set3(np.linspace(0, 1, self.optimal_k))
        
        # 柱状图
        ax1 = axes[0]
        bars = ax1.bar(range(self.optimal_k), cluster_sizes, color=colors, 
                       edgecolor='white', linewidth=2)
        
        # 添加数值标签
        for i, (bar, size) in enumerate(zip(bars, cluster_sizes)):
            height = bar.get_height()
            pct = size / len(self.labels) * 100
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{size:,}\n({pct:.1f}%)',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax1.set_xlabel('聚类编号', fontsize=12, fontweight='bold')
        ax1.set_ylabel('样本数量', fontsize=12, fontweight='bold')
        ax1.set_title('聚类大小分布 - 柱状图', fontsize=14, fontweight='bold')
        ax1.set_xticks(range(self.optimal_k))
        ax1.set_xticklabels([f'C{i}' for i in range(self.optimal_k)])
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 饼图
        ax2 = axes[1]
        wedges, texts, autotexts = ax2.pie(cluster_sizes, labels=cluster_labels, 
                                            colors=colors, autopct='%1.1f%%',
                                            startangle=90, 
                                            wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        
        # 美化文本
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax2.set_title('聚类大小分布 - 饼图', fontsize=14, fontweight='bold')
        
        plt.suptitle(f'8个用户群体样本分布 (总计: {len(self.labels):,})', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        output_file = self.output_dir / "step3_cluster_size_dist.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(Fore.GREEN + f"    ✓ {output_file.name}")
    
    def run(self):
        """运行完整的最终聚类分析流程"""
        try:
            # 步骤1-2: 加载和预处理
            self.load_and_preprocess()
            
            # 步骤3: 聚类
            self.perform_clustering()
            
            # 步骤4: 生成聚类标签CSV
            self.generate_cluster_labels_csv()
            
            # 步骤5: 生成聚类中心CSV
            df_centroids = self.generate_centroids_csv()
            
            # 步骤6: 生成聚类画像描述
            self.generate_cluster_profile_md(df_centroids)
            
            # 步骤7: 生成质量报告
            self.generate_quality_report_md()
            
            # 步骤8: 生成可视化
            self.generate_visualizations()
            
            print(Fore.CYAN + f"\n{'=' * 70}")
            print(Fore.GREEN + "最终聚类分析完成！")
            print(Fore.CYAN + f"{'=' * 70}")
            print(Fore.YELLOW + f"\n输出文件位置: {self.output_dir}")
            print(Fore.WHITE + "\n生成的文件:")
            print(Fore.WHITE + "  1. step3_cluster_labels.csv - 用户聚类标签")
            print(Fore.WHITE + "  2. step3_cluster_centroids.csv - 聚类中心")
            print(Fore.WHITE + "  3. step3_cluster_profile.md - 用户画像描述")
            print(Fore.WHITE + "  4. step3_quality_report.md - 质量诊断报告")
            print(Fore.WHITE + "  5. step3_tsne_umap.png - 降维可视化")
            print(Fore.WHITE + "  6. step3_cluster_size_dist.png - 大小分布图")
            print(Fore.CYAN + f"{'=' * 70}")
            
        except Exception as e:
            print(Fore.RED + f"\n错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    analyzer = FinalClusteringAnalyzer(optimal_k=8)
    analyzer.run()


if __name__ == '__main__':
    main()
