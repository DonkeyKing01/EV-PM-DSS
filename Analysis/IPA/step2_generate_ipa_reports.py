#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IPA分析 - 阶段二：生成IPA分析图表和报告
根据 step1 计算的得分矩阵生成四象限图和分析报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from colorama import init, Fore
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class IPAReportGenerator:
    """IPA分析图表和报告生成器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.input_file = self.base_path / "Data" / "Analyzed" / "IPA" / "step1_scores_matrix.csv"
        self.output_dir = self.base_path / "Data" / "Analyzed" / "IPA" 
        self.charts_dir = self.output_dir / "series_charts"
        self.brands_charts_dir = self.base_path / "Data" / "Analyzed" / "IPA" / "brands_charts"
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.brands_charts_dir.mkdir(parents=True, exist_ok=True)
        
        # 七个评价维度
        self.dimensions = [
            'appearance',    # 外观
            'interior',      # 内饰
            'space',         # 空间
            'intelligence',  # 智能化
            'driving',       # 驾驶
            'range',         # 续航
            'value'          # 性价比
        ]
        
        self.dimension_names_cn = {
            'appearance': '外观',
            'interior': '内饰',
            'space': '空间',
            'intelligence': '智能化',
            'driving': '驾驶',
            'range': '续航',
            'value': '性价比'
        }
        
        # IPA 四象限定义
        self.quadrant_names = {
            'Q1': '保持优势区（高I高P）',
            'Q2': '重点改进区（高I低P）',
            'Q3': '低优先级区（低I低P）',
            'Q4': '过度投入区（低I高P）'
        }
    
    def load_data(self):
        """加载得分矩阵数据"""
        print(Fore.CYAN + "正在加载得分矩阵数据...")
        try:
            self.df = pd.read_csv(self.input_file)
            print(Fore.GREEN + f"✓ 成功加载 {len(self.df)} 个车系的数据")
            
            # 标记样本量小于10的车系
            self.min_sample_threshold = 10
            self.low_sample_series = self.df[self.df['sample_count'] < self.min_sample_threshold].copy()
            
            print(Fore.GREEN + f"  品牌数: {self.df['brand'].nunique()}")
            print(Fore.GREEN + f"  车系总数: {len(self.df)}")
            if len(self.low_sample_series) > 0:
                print(Fore.YELLOW + f"  ⚠ 低样本量车系: {len(self.low_sample_series)} (样本量 < {self.min_sample_threshold}，结果仅供参考)")
        except Exception as e:
            print(Fore.RED + f"× 加载数据失败: {e}")
            raise
    
    def calculate_overall_statistics(self):
        """计算整体统计数据"""
        print(Fore.CYAN + "\n正在计算整体统计数据...")
        
        # 计算各维度的 I 和 P 的统计值
        self.stats = {}
        
        for dim in self.dimensions:
            i_col = f'I_{dim}'
            p_col = f'P_{dim}'
            
            self.stats[dim] = {
                'I_mean': self.df[i_col].mean(),
                'I_median': self.df[i_col].median(),
                'I_std': self.df[i_col].std(),
                'P_mean': self.df[p_col].mean(),
                'P_median': self.df[p_col].median(),
                'P_std': self.df[p_col].std()
            }
        
        # 计算全局中位数（用于划分四象限）
        all_i_values = []
        all_p_values = []
        for dim in self.dimensions:
            all_i_values.extend(self.df[f'I_{dim}'].values)
            all_p_values.extend(self.df[f'P_{dim}'].values)
        
        self.global_i_median = np.median(all_i_values)
        self.global_p_median = np.median(all_p_values)
        
        print(Fore.GREEN + f"✓ 全局中位数: I = {self.global_i_median:.4f}, P = {self.global_p_median:.4f}")
    
    def classify_quadrant(self, i_value, p_value):
        """判断数据点所属象限"""
        if i_value >= self.global_i_median and p_value >= self.global_p_median:
            return 'Q1'  # 保持优势区
        elif i_value >= self.global_i_median and p_value < self.global_p_median:
            return 'Q2'  # 重点改进区
        elif i_value < self.global_i_median and p_value < self.global_p_median:
            return 'Q3'  # 低优先级区
        else:  # i_value < median_i and p_value >= median_p
            return 'Q4'  # 过度投入区
    
    def calculate_axis_limits(self):
        """计算所有数据的坐标轴范围（用于优化显示）"""
        all_i_values = []
        all_p_values = []
        
        for dim in self.dimensions:
            all_i_values.extend(self.df[f'I_{dim}'].values)
            all_p_values.extend(self.df[f'P_{dim}'].values)
        
        # 计算数据的实际范围
        i_data_min = np.min(all_i_values)
        i_data_max = np.max(all_i_values)
        p_data_min = np.min(all_p_values)
        p_data_max = np.max(all_p_values)
        
        # 策略：让数据在图表中居中显示，提高坐标轴精度
        # 起点设置为数据最小值向下扩展20%的数据范围
        i_range = i_data_max - i_data_min
        p_range = p_data_max - p_data_min
        
        # 坐标轴起点：最小值 - 20%范围（让数据不贴边）
        self.i_min = max(0, i_data_min - i_range * 0.2)
        self.p_min = max(0, p_data_min - p_range * 0.2)
        
        # 上限始终为1.0（保持语义完整性）
        self.i_max = 1.0
        self.p_max = 1.0
        
        # 比如数据都在0.8以上，起点至少从0.5开始
        if i_data_min > 0.7 and self.i_min < 0.5:
            self.i_min = 0.5
        if p_data_min > 0.5 and self.p_min < 0.3:
            self.p_min = 0.3
        
        print(Fore.GREEN + f"✓ 数据范围: I=[{i_data_min:.4f}, {i_data_max:.4f}], P=[{p_data_min:.4f}, {p_data_max:.4f}]")
        print(Fore.GREEN + f"✓ 坐标轴范围: I=[{self.i_min:.4f}, {self.i_max:.4f}], P=[{self.p_min:.4f}, {self.p_max:.4f}]")
        print(Fore.CYAN + f"  → 坐标轴精度提升: I范围缩小{1/(self.i_max-self.i_min):.2f}倍, P范围缩小{1/(self.p_max-self.p_min):.2f}倍")
    
    def generate_low_sample_warning_report(self):
        """生成低样本量车系警告报告"""
        if len(self.low_sample_series) == 0:
            return
        
        print(Fore.CYAN + "\n正在生成低样本量车系警告报告...")
        
        report_lines = []
        report_lines.append("# 低样本量车系警告报告\n\n")
        report_lines.append(f"**⚠ 警告**: 以下车系评论样本量少于 {self.min_sample_threshold} 条，IPA分析结果可能存在较大误差，请谨慎使用。\n\n")
        report_lines.append(f"**低样本量车系总数**: {len(self.low_sample_series)}\n\n")
        report_lines.append("**建议**: 当样本量过少时，个别极端评论可能对整体分析结果产生较大影响，建议结合更多数据源或延长数据收集周期。\n\n")
        report_lines.append("---\n\n")
        report_lines.append("| 品牌 | 车系 | 样本量 | 风险等级 |\n")
        report_lines.append("|------|------|--------|----------|\n")
        
        for _, row in self.low_sample_series.sort_values('sample_count').iterrows():
            sample_count = row['sample_count']
            if sample_count < 5:
                risk = "高风险"
            elif sample_count < 8:
                risk = "中风险"
            else:
                risk = "低风险"
            report_lines.append(f"| {row['brand']} | {row['series']} | {sample_count} | {risk} |\n")
        
        report_path = self.output_dir / "low_sample_warning_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)
        
        print(Fore.GREEN + f"✓ 低样本量警告报告已保存: {report_path}")
    
    def plot_series_ipa_charts(self):
        """绘制所有车系的IPA散点图"""
        print(Fore.CYAN + f"\n正在绘制所有 {len(self.df)} 个车系的IPA散点图...")
        
        # 处理所有车系
        top_series = self.df
        
        for idx, row in top_series.iterrows():
            brand = row['brand']
            series = row['series']
            sample_count = row['sample_count']
            
            # 判断是否为低样本量
            is_low_sample = sample_count < self.min_sample_threshold
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # 准备该车系的维度数据
            dimensions_data = []
            i_values = []
            p_values = []
            for dim in self.dimensions:
                i_value = row[f'I_{dim}']
                p_value = row[f'P_{dim}']
                i_values.append(i_value)
                p_values.append(p_value)
                dimensions_data.append({
                    'dimension': dim,
                    'name_cn': self.dimension_names_cn[dim],
                    'I': i_value,
                    'P': p_value,
                    'quadrant': self.classify_quadrant(i_value, p_value)
                })
            
            df_dims = pd.DataFrame(dimensions_data)
            
            # 为该车系单独计算坐标轴范围
            i_min_series = min(i_values)
            i_max_series = max(i_values)
            p_min_series = min(p_values)
            p_max_series = max(p_values)
            
            i_range = i_max_series - i_min_series
            p_range = p_max_series - p_min_series
            
            # 坐标轴起点：最小值 - 20%范围
            axis_i_min = max(0, i_min_series - i_range * 0.2) if i_range > 0 else max(0, i_min_series - 0.1)
            axis_p_min = max(0, p_min_series - p_range * 0.2) if p_range > 0 else max(0, p_min_series - 0.1)
            
            # 如果数据本身就很集中在高值区，强制提高起点
            if i_min_series > 0.7 and axis_i_min < 0.5:
                axis_i_min = 0.5
            if p_min_series > 0.5 and axis_p_min < 0.3:
                axis_p_min = 0.3
            
            # 上限始终为1.0
            axis_i_max = 1.0
            axis_p_max = 1.0
            
            # 绘制四象限分隔线
            ax.axhline(y=self.global_p_median, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
            ax.axvline(x=self.global_i_median, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
            
            # 添加象限背景色（使用该车系的坐标范围）
            ax.fill_between([axis_i_min, self.global_i_median], axis_p_min, self.global_p_median, 
                           alpha=0.1, color='blue')
            ax.fill_between([self.global_i_median, axis_i_max], axis_p_min, self.global_p_median, 
                           alpha=0.1, color='yellow')
            ax.fill_between([axis_i_min, self.global_i_median], self.global_p_median, axis_p_max, 
                           alpha=0.1, color='orange')
            ax.fill_between([self.global_i_median, axis_i_max], self.global_p_median, axis_p_max, 
                           alpha=0.1, color='green')
            
            # 绘制散点
            colors = {'Q1': 'green', 'Q2': 'red', 'Q3': 'blue', 'Q4': 'orange'}
            for quadrant in ['Q1', 'Q2', 'Q3', 'Q4']:
                subset = df_dims[df_dims['quadrant'] == quadrant]
                if len(subset) > 0:
                    ax.scatter(subset['I'], subset['P'], 
                             s=300, alpha=0.6, c=colors[quadrant], 
                             edgecolors='black', linewidths=2)
            
            # 添加标签
            for _, dim_row in df_dims.iterrows():
                ax.annotate(dim_row['name_cn'], 
                           xy=(dim_row['I'], dim_row['P']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
            
            # 设置标题和标签
            ax.set_xlabel('重要度 (Importance)', fontsize=14, fontweight='bold')
            ax.set_ylabel('满意度 (Performance)', fontsize=14, fontweight='bold')
            
            # 根据样本量添加不同的标题
            if is_low_sample:
                title = f'{brand} - {series}\nIPA四象限分析图 (样本量: {sample_count})\n⚠ 警告：样本量过小，结果存在误差，请谨慎使用'
                title_color = 'red'
            else:
                title = f'{brand} - {series}\nIPA四象限分析图 (样本量: {sample_count})'
                title_color = 'black'
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color=title_color)
            
            # 设置坐标轴范围（使用该车系单独计算的范围）
            ax.set_xlim(axis_i_min, axis_i_max)
            ax.set_ylim(axis_p_min, axis_p_max)
            
            # 添加网格
            ax.grid(True, alpha=0.3, linestyle=':')
            
            # 如果是低样本量，添加水印警告
            if is_low_sample:
                ax.text(0.5, 0.5, '⚠ 低样本量\n结果仅供参考', 
                       transform=ax.transAxes, fontsize=40, color='red',
                       alpha=0.15, ha='center', va='center', rotation=30)
            
            plt.tight_layout()
            
            # 保存图表（文件名处理特殊字符）
            safe_filename = f"{brand}_{series}".replace('/', '_').replace(' ', '_')
            output_path = self.charts_dir / f"series_{safe_filename}_ipa.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        print(Fore.GREEN + f"✓ 已生成 {len(top_series)} 个车系的IPA图")
        
        return dimensions_data
    
    def generate_dimension_analysis_report(self):
        """生成维度分析报告"""
        print(Fore.CYAN + "\n正在生成维度分析报告...")
        
        # 准备整体维度数据
        dimensions_data = []
        for dim in self.dimensions:
            i_mean = self.stats[dim]['I_mean']
            p_mean = self.stats[dim]['P_mean']
            dimensions_data.append({
                'dimension': dim,
                'name_cn': self.dimension_names_cn[dim],
                'I': i_mean,
                'P': p_mean,
                'quadrant': self.classify_quadrant(i_mean, p_mean)
            })
        
        df_dims = pd.DataFrame(dimensions_data)
        
        report_lines = []
        report_lines.append("# IPA 维度分析报告\n")
        report_lines.append("## 整体维度表现分析\n")
        report_lines.append(f"**分析基础**: 基于 {len(self.df)} 个车系的用户评论数据\n")
        report_lines.append(f"**全局中位数**: I = {self.global_i_median:.4f}, P = {self.global_p_median:.4f}\n")
        
        # 添加低样本量警告
        if len(self.low_sample_series) > 0:
            report_lines.append(f"\n**⚠ 数据质量说明**: 其中 {len(self.low_sample_series)} 个车系样本量少于 {self.min_sample_threshold} 条，分析结果可能存在误差。\n")
        
        report_lines.append("\n---\n")
        
        # 按象限分组
        for quadrant in ['Q1', 'Q2', 'Q3', 'Q4']:
            dims_in_q = df_dims[df_dims['quadrant'] == quadrant]
            if len(dims_in_q) == 0:
                continue
            
            report_lines.append(f"\n### {self.quadrant_names[quadrant]}\n")
            
            if quadrant == 'Q1':
                report_lines.append("**策略建议**: 保持现有优势，继续巩固\n")
            elif quadrant == 'Q2':
                report_lines.append("**策略建议**: 重点改进，用户高度关注但满意度低\n")
            elif quadrant == 'Q3':
                report_lines.append("**策略建议**: 低优先级，可适度优化\n")
            elif quadrant == 'Q4':
                report_lines.append("**策略建议**: 可能存在过度投入，考虑资源重新分配\n")
            
            report_lines.append("\n| 维度 | 重要度(I) | 满意度(P) | 排名 |\n")
            report_lines.append("|------|-----------|-----------|------|\n")
            
            for _, row in dims_in_q.iterrows():
                dim = row['dimension']
                i_rank = df_dims.sort_values('I', ascending=False).index.get_loc(row.name) + 1
                p_rank = df_dims.sort_values('P', ascending=False).index.get_loc(row.name) + 1
                report_lines.append(
                    f"| {row['name_cn']} | {row['I']:.4f} | {row['P']:.4f} | "
                    f"I排名{i_rank}/7, P排名{p_rank}/7 |\n"
                )
        
        report_lines.append("\n---\n")
        report_lines.append("\n## 各维度详细统计\n")
        report_lines.append("\n| 维度 | I均值 | I中位数 | I标准差 | P均值 | P中位数 | P标准差 |\n")
        report_lines.append("|------|-------|---------|---------|-------|---------|--------|\n")
        
        for dim in self.dimensions:
            stats = self.stats[dim]
            report_lines.append(
                f"| {self.dimension_names_cn[dim]} | "
                f"{stats['I_mean']:.4f} | {stats['I_median']:.4f} | {stats['I_std']:.4f} | "
                f"{stats['P_mean']:.4f} | {stats['P_median']:.4f} | {stats['P_std']:.4f} |\n"
            )
        
        # 保存报告
        report_path = self.output_dir / "dimension_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)
        
        print(Fore.GREEN + f"✓ 维度分析报告已保存: {report_path}")
    
    def generate_series_analysis_report(self, top_n=20):
        """生成车系分析报告"""
        print(Fore.CYAN + f"\n正在生成TOP {top_n} 车系分析报告...")
        
        # 先获取top_n车系
        top_series = self.df.nlargest(top_n, 'sample_count')
        
        report_lines = []
        report_lines.append(f"# TOP {top_n} 车系IPA分析报告\n")
        report_lines.append(f"**分析说明**: 按样本量排序的前{top_n}个车系\n")
        
        # 添加低样本量警告
        low_sample_in_top = top_series[top_series['sample_count'] < self.min_sample_threshold]
        if len(low_sample_in_top) > 0:
            report_lines.append(f"\n**⚠ 警告**: 其中 {len(low_sample_in_top)} 个车系样本量少于 {self.min_sample_threshold} 条，分析结果仅供参考。\n")
        
        report_lines.append("\n---\n")
        
        for idx, (_, row) in enumerate(top_series.iterrows(), 1):
            brand = row['brand']
            series = row['series']
            sample_count = row['sample_count']
            is_low_sample = sample_count < self.min_sample_threshold
            
            report_lines.append(f"\n## {idx}. {brand} - {series}\n")
            report_lines.append(f"**样本量**: {sample_count}")
            
            # 添加低样本量警告标识
            if is_low_sample:
                report_lines.append(f" ⚠ **(警告：样本量过小，结果仅供参考)**")
            
            report_lines.append("\n\n")
            
            # 计算该车系各维度的象限分布
            dims_data = []
            for dim in self.dimensions:
                i_value = row[f'I_{dim}']
                p_value = row[f'P_{dim}']
                quadrant = self.classify_quadrant(i_value, p_value)
                dims_data.append({
                    'dim': self.dimension_names_cn[dim],
                    'I': i_value,
                    'P': p_value,
                    'Q': quadrant
                })
            
            # 按象限分组
            report_lines.append("\n### 维度表现\n")
            report_lines.append("\n| 维度 | 重要度(I) | 满意度(P) | 所属象限 |\n")
            report_lines.append("|------|-----------|-----------|----------|\n")
            
            for dim_info in dims_data:
                q_name = self.quadrant_names[dim_info['Q']].split('（')[0]
                report_lines.append(
                    f"| {dim_info['dim']} | {dim_info['I']:.4f} | {dim_info['P']:.4f} | {q_name} |\n"
                )
            
            # 优劣势分析
            q_counts = {}
            for dim_info in dims_data:
                q = dim_info['Q']
                q_counts[q] = q_counts.get(q, 0) + 1
            
            report_lines.append("\n### 综合评价\n")
            
            if q_counts.get('Q1', 0) > 0:
                q1_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q1']
                report_lines.append(f"- **优势维度** ({len(q1_dims)}个): {', '.join(q1_dims)}\n")
            
            if q_counts.get('Q2', 0) > 0:
                q2_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q2']
                report_lines.append(f"- **需改进维度** ({len(q2_dims)}个): {', '.join(q2_dims)}\n")
            
            if q_counts.get('Q4', 0) > 0:
                q4_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q4']
                report_lines.append(f"- **过度投入维度** ({len(q4_dims)}个): {', '.join(q4_dims)}\n")
            
            report_lines.append("\n---\n")
        
        # 保存报告
        report_path = self.output_dir / f"top{top_n}_series_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)
        
        print(Fore.GREEN + f"✓ 车系分析报告已保存: {report_path}")
    
    def aggregate_brand_data(self):
        """聚合品牌级别的IPA数据"""
        print(Fore.CYAN + "\n正在聚合品牌级别数据...")
        
        brand_data = []
        for brand in self.df['brand'].unique():
            brand_series = self.df[self.df['brand'] == brand]
            
            # 计算该品牌的总样本量
            total_samples = brand_series['sample_count'].sum()
            
            # 加权平均计算品牌级别的I和P
            brand_row = {
                'brand': brand,
                'series_count': len(brand_series),
                'total_samples': total_samples
            }
            
            for dim in self.dimensions:
                # 使用样本量加权平均
                weights = brand_series['sample_count'].values
                i_values = brand_series[f'I_{dim}'].values
                p_values = brand_series[f'P_{dim}'].values
                
                brand_row[f'I_{dim}'] = np.average(i_values, weights=weights)
                brand_row[f'P_{dim}'] = np.average(p_values, weights=weights)
            
            brand_data.append(brand_row)
        
        self.df_brands = pd.DataFrame(brand_data)
        print(Fore.GREEN + f"✓ 成功聚合 {len(self.df_brands)} 个品牌的数据")
    
    def plot_brand_ipa_charts(self):
        """绘制品牌级别的IPA散点图"""
        print(Fore.CYAN + f"\n正在绘制 {len(self.df_brands)} 个品牌的IPA散点图...")
        
        for idx, row in self.df_brands.iterrows():
            brand = row['brand']
            series_count = row['series_count']
            total_samples = row['total_samples']
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # 准备该品牌的维度数据
            dimensions_data = []
            i_values = []
            p_values = []
            for dim in self.dimensions:
                i_value = row[f'I_{dim}']
                p_value = row[f'P_{dim}']
                i_values.append(i_value)
                p_values.append(p_value)
                dimensions_data.append({
                    'dimension': dim,
                    'name_cn': self.dimension_names_cn[dim],
                    'I': i_value,
                    'P': p_value,
                    'quadrant': self.classify_quadrant(i_value, p_value)
                })
            
            df_dims = pd.DataFrame(dimensions_data)
            
            # 为该品牌单独计算坐标轴范围
            i_min_brand = min(i_values)
            i_max_brand = max(i_values)
            p_min_brand = min(p_values)
            p_max_brand = max(p_values)
            
            i_range = i_max_brand - i_min_brand
            p_range = p_max_brand - p_min_brand
            
            # 坐标轴起点
            axis_i_min = max(0, i_min_brand - i_range * 0.2) if i_range > 0 else max(0, i_min_brand - 0.1)
            axis_p_min = max(0, p_min_brand - p_range * 0.2) if p_range > 0 else max(0, p_min_brand - 0.1)
            
            if i_min_brand > 0.7 and axis_i_min < 0.5:
                axis_i_min = 0.5
            if p_min_brand > 0.5 and axis_p_min < 0.3:
                axis_p_min = 0.3
            
            axis_i_max = 1.0
            axis_p_max = 1.0
            
            # 绘制四象限分隔线
            ax.axhline(y=self.global_p_median, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
            ax.axvline(x=self.global_i_median, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
            
            # 添加象限背景色
            ax.fill_between([axis_i_min, self.global_i_median], axis_p_min, self.global_p_median, 
                           alpha=0.1, color='blue')
            ax.fill_between([self.global_i_median, axis_i_max], axis_p_min, self.global_p_median, 
                           alpha=0.1, color='yellow')
            ax.fill_between([axis_i_min, self.global_i_median], self.global_p_median, axis_p_max, 
                           alpha=0.1, color='orange')
            ax.fill_between([self.global_i_median, axis_i_max], self.global_p_median, axis_p_max, 
                           alpha=0.1, color='green')
            
            # 绘制散点
            colors = {'Q1': 'green', 'Q2': 'red', 'Q3': 'blue', 'Q4': 'orange'}
            for quadrant in ['Q1', 'Q2', 'Q3', 'Q4']:
                subset = df_dims[df_dims['quadrant'] == quadrant]
                if len(subset) > 0:
                    ax.scatter(subset['I'], subset['P'], 
                             s=300, alpha=0.6, c=colors[quadrant], 
                             edgecolors='black', linewidths=2)
            
            # 添加标签
            for _, dim_row in df_dims.iterrows():
                ax.annotate(dim_row['name_cn'], 
                           xy=(dim_row['I'], dim_row['P']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
            
            # 设置标题和标签
            ax.set_xlabel('重要度 (Importance)', fontsize=14, fontweight='bold')
            ax.set_ylabel('满意度 (Performance)', fontsize=14, fontweight='bold')
            title = f'{brand}\nIPA四象限分析图 (车系数: {series_count}, 总样本量: {total_samples})'
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # 设置坐标轴范围
            ax.set_xlim(axis_i_min, axis_i_max)
            ax.set_ylim(axis_p_min, axis_p_max)
            
            # 添加网格
            ax.grid(True, alpha=0.3, linestyle=':')
            
            plt.tight_layout()
            
            # 保存图表
            safe_filename = brand.replace('/', '_').replace(' ', '_')
            output_path = self.brands_charts_dir / f"brand_{safe_filename}_ipa.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        print(Fore.GREEN + f"✓ 已生成 {len(self.df_brands)} 个品牌的IPA图")
    
    def generate_brand_analysis_report(self):
        """生成品牌级别分析报告"""
        print(Fore.CYAN + "\n正在生成品牌级别分析报告...")
        
        report_lines = []
        report_lines.append("# 品牌级别IPA分析报告\n\n")
        report_lines.append("**分析说明**: 基于各品牌旗下所有车系的加权平均数据\n")
        report_lines.append(f"**品牌总数**: {len(self.df_brands)}\n\n")
        report_lines.append("---\n\n")
        
        # 按总样本量排序
        df_brands_sorted = self.df_brands.sort_values('total_samples', ascending=False)
        
        for idx, (_, row) in enumerate(df_brands_sorted.iterrows(), 1):
            brand = row['brand']
            series_count = row['series_count']
            total_samples = row['total_samples']
            
            report_lines.append(f"## {idx}. {brand}\n\n")
            report_lines.append(f"**车系数**: {series_count} | **总样本量**: {total_samples}\n\n")
            
            # 计算该品牌各维度的象限分布
            dims_data = []
            for dim in self.dimensions:
                i_value = row[f'I_{dim}']
                p_value = row[f'P_{dim}']
                quadrant = self.classify_quadrant(i_value, p_value)
                dims_data.append({
                    'dim': self.dimension_names_cn[dim],
                    'I': i_value,
                    'P': p_value,
                    'Q': quadrant
                })
            
            # 维度表现表格
            report_lines.append("### 维度表现\n\n")
            report_lines.append("| 维度 | 重要度(I) | 满意度(P) | 所属象限 |\n")
            report_lines.append("|------|-----------|-----------|----------|\n")
            
            for dim_info in dims_data:
                q_name = self.quadrant_names[dim_info['Q']].split('（')[0]
                report_lines.append(
                    f"| {dim_info['dim']} | {dim_info['I']:.4f} | {dim_info['P']:.4f} | {q_name} |\n"
                )
            
            # 优劣势分析
            q_counts = {}
            for dim_info in dims_data:
                q = dim_info['Q']
                q_counts[q] = q_counts.get(q, 0) + 1
            
            report_lines.append("\n### 综合评价\n\n")
            
            if q_counts.get('Q1', 0) > 0:
                q1_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q1']
                report_lines.append(f"- **优势维度** ({len(q1_dims)}个): {', '.join(q1_dims)}\n")
            
            if q_counts.get('Q2', 0) > 0:
                q2_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q2']
                report_lines.append(f"- **需改进维度** ({len(q2_dims)}个): {', '.join(q2_dims)}\n")
            
            if q_counts.get('Q4', 0) > 0:
                q4_dims = [d['dim'] for d in dims_data if d['Q'] == 'Q4']
                report_lines.append(f"- **过度投入维度** ({len(q4_dims)}个): {', '.join(q4_dims)}\n")
            
            report_lines.append("\n---\n\n")
        
        # 保存报告（直接保存到IPA目录下）
        report_path = self.base_path / "Data" / "Analyzed" / "IPA" / "brand_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)
        
        print(Fore.GREEN + f"✓ 品牌分析报告已保存: {report_path}")
    
    def run(self):
        """执行完整的报告生成流程"""
        print(Fore.CYAN + "="*80)
        print(Fore.CYAN + "IPA 分析图表和报告生成 - Step 2")
        print(Fore.CYAN + "="*80)
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 计算统计数据
        self.calculate_overall_statistics()
        
        # 3. 计算坐标轴范围
        self.calculate_axis_limits()
        
        # 4. 生成低样本量警告报告
        self.generate_low_sample_warning_report()
        
        # 5. 绘制所有车系IPA图
        self.plot_series_ipa_charts()
        
        # 6. 生成维度分析报告
        self.generate_dimension_analysis_report()
        
        # 7. 生成车系分析报告（前20个）
        self.generate_series_analysis_report(top_n=20)
        
        # 8. 聚合品牌数据
        self.aggregate_brand_data()
        
        # 9. 绘制品牌级别IPA图
        self.plot_brand_ipa_charts()
        
        # 10. 生成品牌分析报告
        self.generate_brand_analysis_report()
        
        print(Fore.CYAN + "\n" + "="*80)
        print(Fore.CYAN + "生成结果摘要")
        print(Fore.CYAN + "="*80)
        print(Fore.GREEN + f"车系图表路径: {self.charts_dir}")
        print(Fore.GREEN + f"品牌图表路径: {self.brands_charts_dir}")
        print(Fore.GREEN + f"报告保存路径: {self.output_dir}")
        print(Fore.GREEN + f"品牌报告路径: {self.base_path / 'Data' / 'Analyzed' / 'IPA' / 'brand_analysis_report.md'}")
        print(Fore.GREEN + "\n✓ IPA 分析图表和报告生成完成！")


def main():
    """主函数"""
    generator = IPAReportGenerator()
    generator.run()


if __name__ == '__main__':
    main()
