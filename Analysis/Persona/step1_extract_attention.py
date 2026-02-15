#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户画像分析 - 阶段一：基于注意力向量的用户关注维度分析
根据用户评论的七个维度（外观、内饰、空间、智能化、驾驶、续航、性价比）
计算每个用户在各维度的关注度向量
"""

import pandas as pd
import numpy as np
from pathlib import Path
from colorama import init, Fore
from transformers import AutoTokenizer
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)


class PersonaAttentionAnalyzer:
    """用户画像注意力分析器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.input_file = self.base_path / "Data" / "Processed" / "ugc.csv"
        self.output_file = self.base_path / "Data" / "Analyzed" / "Persona" / "step1_attention_vectors.csv"
        
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
        
        # 初始化tokenizer
        print(Fore.CYAN + "正在加载Tokenizer...")
        try:
            # 使用中文BERT tokenizer确保中文分词准确
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-chinese')
            print(Fore.GREEN + "✓ Tokenizer加载成功")
        except Exception as e:
            print(Fore.YELLOW + f"⚠ 无法加载bert-base-chinese，尝试使用备用方案...")
            try:
                # 备用方案：使用其他中文tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained('hfl/chinese-bert-wwm-ext')
                print(Fore.GREEN + "✓ 备用Tokenizer加载成功")
            except:
                print(Fore.RED + f"✗ Tokenizer加载失败: {e}")
                print(Fore.YELLOW + "将使用简单字符长度作为token长度估计")
                self.tokenizer = None
    
    def check_content_fill(self, text):
        """
        阶段一步骤1：判断是否有内容
        
        Args:
            text: 评论文本
            
        Returns:
            m_fill: 1 if 有内容, 0 if 为空
        """
        if pd.isna(text) or text is None or str(text).strip() == '':
            return 0
        return 1
    
    def calculate_token_length(self, text):
        """
        阶段一步骤2：计算文本的token长度
        
        Args:
            text: 评论文本
            
        Returns:
            token_len: token数量
        """
        if pd.isna(text) or text is None:
            return 0
        
        text = str(text).strip()
        if text == '':
            return 0
        
        try:
            if self.tokenizer is not None:
                # 使用tokenizer计算token长度
                tokens = self.tokenizer.tokenize(text)
                return len(tokens)
            else:
                # 备用方案：使用字符长度作为估计
                # 对于中文，一般字符长度约等于token长度
                return len(text)
        except Exception as e:
            # 如果tokenization失败，使用字符长度
            return len(text)
    
    def calculate_attention_raw(self, m_fill, token_len):
        """
        阶段一步骤3：计算原始attention值
        
        Args:
            m_fill: 内容填充标记 (0或1)
            token_len: token长度
            
        Returns:
            A: 原始attention值
        """
        return m_fill * token_len
    
    def normalize_attention_vector(self, attention_dict):
        """
        阶段一步骤4：归一化attention向量
        
        Args:
            attention_dict: 各维度的原始attention值字典
            
        Returns:
            normalized_dict: 归一化后的attention权重字典
        """
        # 计算总和
        total = sum(attention_dict.values())
        
        # 如果总和为0（所有维度都没有内容），返回均匀分布
        if total == 0:
            return {dim: 0.0 for dim in self.dimensions}
        
        # 归一化
        normalized_dict = {dim: attention_dict[dim] / total for dim in self.dimensions}
        
        return normalized_dict
    
    def process_single_review(self, row):
        """
        处理单条评论，计算attention向量
        
        Args:
            row: DataFrame的一行数据
            
        Returns:
            attention_vector: 包含review_id和各维度权重的字典
        """
        review_id = row['review_id']
        
        # 步骤1-3：计算各维度的原始attention值
        attention_raw = {}
        
        for dim in self.dimensions:
            # 获取该维度的评论文本
            review_col = f'{dim}_review'
            text = row.get(review_col, None)
            
            # 步骤1：判断内容是否存在
            m_fill = self.check_content_fill(text)
            
            # 步骤2：计算token长度
            token_len = self.calculate_token_length(text) if m_fill == 1 else 0
            
            # 步骤3：计算原始attention
            attention_raw[dim] = self.calculate_attention_raw(m_fill, token_len)
        
        # 步骤4：归一化
        attention_normalized = self.normalize_attention_vector(attention_raw)
        
        # 构建返回结果
        result = {'review_id': review_id}
        for dim in self.dimensions:
            result[f'w_{dim}'] = attention_normalized[dim]
        
        return result
    
    def analyze_all_reviews(self):
        """分析所有评论，生成persona向量"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "用户画像分析 - 阶段一：Attention向量计算")
        print(Fore.CYAN + "=" * 70)
        
        # 读取数据
        print(Fore.YELLOW + f"\n正在读取数据: {self.input_file.name}")
        df = pd.read_csv(self.input_file, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 成功读取 {len(df)} 条评论数据")
        
        # 处理每条评论
        print(Fore.YELLOW + f"\n开始计算attention向量...")
        results = []
        
        for idx, row in df.iterrows():
            result = self.process_single_review(row)
            results.append(result)
            
            # 每处理1000条显示进度
            if (idx + 1) % 1000 == 0:
                print(Fore.WHITE + f"  已处理: {idx + 1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")
        
        print(Fore.GREEN + f"✓ 全部处理完成")
        
        # 创建结果DataFrame
        df_results = pd.DataFrame(results)
        
        # 调整列顺序
        column_order = ['review_id'] + [f'w_{dim}' for dim in self.dimensions]
        df_results = df_results[column_order]
        
        # 保存结果
        print(Fore.YELLOW + f"\n正在保存结果...")
        df_results.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 结果已保存至: {self.output_file}")
        
        # 打印统计信息
        self.print_statistics(df_results)
        
        return df_results
    
    def print_statistics(self, df):
        """打印统计信息"""
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.GREEN + "分析完成!")
        print(Fore.CYAN + f"{'=' * 70}")
        
        print(Fore.YELLOW + f"\n基本信息:")
        print(Fore.WHITE + f"  总评论数: {len(df)}")
        print(Fore.WHITE + f"  维度数: {len(self.dimensions)}")
        
        print(Fore.YELLOW + f"\n各维度平均权重:")
        for dim in self.dimensions:
            col = f'w_{dim}'
            mean_weight = df[col].mean()
            std_weight = df[col].std()
            print(Fore.WHITE + f"  {self.dimension_names_cn[dim]:<6} (w_{dim}): "
                  f"均值={mean_weight:.4f}, 标准差={std_weight:.4f}")
        
        # 计算权重为0的比例（即该维度无评论的比例）
        print(Fore.YELLOW + f"\n各维度缺失率 (权重=0的比例):")
        for dim in self.dimensions:
            col = f'w_{dim}'
            zero_ratio = (df[col] == 0).sum() / len(df) * 100
            print(Fore.WHITE + f"  {self.dimension_names_cn[dim]:<6}: {zero_ratio:.2f}%")
        
        # 找出最受关注的维度
        print(Fore.YELLOW + f"\n最受关注的维度:")
        avg_weights = {dim: df[f'w_{dim}'].mean() for dim in self.dimensions}
        sorted_dims = sorted(avg_weights.items(), key=lambda x: x[1], reverse=True)
        for i, (dim, weight) in enumerate(sorted_dims, 1):
            print(Fore.WHITE + f"  {i}. {self.dimension_names_cn[dim]}: {weight:.4f}")
        
        # 示例数据
        print(Fore.YELLOW + f"\n示例数据 (前3条):")
        for idx in range(min(3, len(df))):
            row = df.iloc[idx]
            print(Fore.WHITE + f"\n  评论 {idx+1} (ID: {row['review_id']}):")
            for dim in self.dimensions:
                print(Fore.WHITE + f"    w_{dim}: {row[f'w_{dim}']:.4f}")
        
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.GREEN + f"文件大小: {self.output_file.stat().st_size / 1024:.1f} KB")
        print(Fore.CYAN + f"{'=' * 70}")


def main():
    """主函数"""
    analyzer = PersonaAttentionAnalyzer()
    analyzer.analyze_all_reviews()


if __name__ == '__main__':
    main()
