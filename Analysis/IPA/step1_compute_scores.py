#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IPA分析 - 阶段一：计算IPA得分矩阵
根据用户评论数据计算每个车系在各维度上的重要度(Importance)和满意度(Performance)
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from colorama import init, Fore
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)


class IPAScoreComputer:
    """IPA得分矩阵计算器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.input_file = self.base_path / "Data" / "Processed" / "ugc.csv"
        self.keywords_file = self.base_path / "Analysis" / "IPA" / "dim_keywords.json"
        self.output_file = self.base_path / "Data" / "Analyzed" / "IPA" / "step1_scores_matrix.csv"
        
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
        
        # 加载维度关键词词表
        self.load_keywords()
        
        # 初始化情感分析模型
        self.init_sentiment_model()
    
    def load_keywords(self):
        """加载维度关键词词表"""
        print(Fore.CYAN + "正在加载维度关键词词表...")
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                self.keyword_dict = json.load(f)
            print(Fore.GREEN + f"✓ 成功加载 {len(self.keyword_dict)} 个维度的关键词")
        except Exception as e:
            print(Fore.RED + f"✗ 加载关键词词表失败: {e}")
            raise
    
    def init_sentiment_model(self):
        """初始化情感分析模型"""
        print(Fore.CYAN + "正在加载情感分析模型...")
        try:
            # 使用中文情感分析模型
            model_name = "uer/roberta-base-finetuned-jd-binary-chinese"
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.sentiment_model.eval()
            
            # 检查是否有GPU
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.sentiment_model.to(self.device)
            
            print(Fore.GREEN + f"✓ 情感分析模型加载成功 (设备: {self.device})")
        except Exception as e:
            print(Fore.YELLOW + f"⚠ 情感分析模型加载失败: {e}")
            print(Fore.YELLOW + "将使用规则方法进行情感分析")
            self.sentiment_model = None
    
    def check_dimension_in_text(self, text, dimension):
        """检查文本中是否包含某维度的关键词"""
        if pd.isna(text) or text is None or str(text).strip() == '':
            return False
        
        text = str(text).lower()
        keywords = self.keyword_dict.get(dimension, [])
        
        for keyword in keywords:
            if keyword.lower() in text:
                return True
        return False
    
    def compute_sentiment_score(self, text):
        """计算文本情感得分 [0, 1]"""
        if pd.isna(text) or text is None or str(text).strip() == '':
            return None
        
        text = str(text).strip()
        
        # 如果模型可用，使用模型
        if self.sentiment_model is not None:
            try:
                # 分句处理（避免文本过长）
                sentences = re.split(r'[。！？\n]', text)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                if not sentences:
                    return None
                
                scores = []
                for sentence in sentences:
                    if len(sentence) < 5:  # 过短的句子跳过
                        continue
                    
                    # 截断过长的句子
                    if len(sentence) > 510:
                        sentence = sentence[:510]
                    
                    inputs = self.sentiment_tokenizer(
                        sentence,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=512
                    ).to(self.device)
                    
                    with torch.no_grad():
                        outputs = self.sentiment_model(**inputs)
                        logits = outputs.logits
                        probs = torch.softmax(logits, dim=-1)
                        # 假设模型输出 [负面, 正面]
                        positive_prob = probs[0][1].item()
                        scores.append(positive_prob)
                
                if scores:
                    return np.mean(scores)
                else:
                    return None
                    
            except Exception as e:
                print(Fore.YELLOW + f"⚠ 情感分析出错: {e}")
                return None
        
        # 降级方案：使用规则方法
        return self.compute_sentiment_rule_based(text)
    
    def compute_sentiment_rule_based(self, text):
        """基于规则的情感分析（降级方案）"""
        positive_words = ['好', '棒', '赞', '满意', '喜欢', '爱', '优秀', '完美', 
                          '舒服', '舒适', '漂亮', '帅', '美', '不错', '可以']
        negative_words = ['差', '烂', '糟', '不满意', '不喜欢', '讨厌', '失望', 
                          '后悔', '难受', '难看', '丑', '不好', '问题', '缺点']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.5  # 中性
        
        return pos_count / total
    
    def process_single_review(self, row):
        """处理单条评论，计算各维度指标"""
        result = {
            'review_id': row['review_id'],
            'brand': row['brand'],
            'series': row['series']
        }
        
        for dim in self.dimensions:
            # 1. 检查维度是否被提及 (m_fill)
            review_col = f'{dim}_review'
            score_col = f'{dim}_score'
            
            has_review = False
            if review_col in row and not pd.isna(row[review_col]) and str(row[review_col]).strip():
                has_review = True
            
            # 2. 检查最满意/最不满意
            in_most_satisfied = self.check_dimension_in_text(row.get('most_satisfied', ''), dim)
            in_least_satisfied = self.check_dimension_in_text(row.get('least_satisfied', ''), dim)
            
            # 3. 是否相关（用于计算 Importance）
            is_related = has_review or in_most_satisfied or in_least_satisfied
            result[f'm_fill_{dim}'] = 1 if has_review else 0
            result[f'in_most_{dim}'] = 1 if in_most_satisfied else 0
            result[f'in_least_{dim}'] = 1 if in_least_satisfied else 0
            result[f'is_related_{dim}'] = 1 if is_related else 0
            
            # 4. 计算官方评分 S_official (归一化到 [0,1])
            s_official = None
            if score_col in row and not pd.isna(row[score_col]):
                try:
                    official_score = float(row[score_col])
                    # 假设官方评分是 1-5 分制
                    s_official = (official_score - 1) / 4.0
                except:
                    s_official = None
            result[f's_official_{dim}'] = s_official
            
            # 5. 计算文本情感得分 S_bert
            s_bert = None
            if has_review:
                review_text = str(row[review_col])
                s_bert = self.compute_sentiment_score(review_text)
            result[f's_bert_{dim}'] = s_bert
            
            # 6. 计算强信号 S_strong
            s_strong = None
            if in_most_satisfied:
                s_strong = 1.0
            elif in_least_satisfied:
                s_strong = 0.0
            result[f's_strong_{dim}'] = s_strong
        
        return result
    
    def aggregate_to_series(self, df_processed):
        """聚合到车系级别，计算 I 和 P"""
        print(Fore.CYAN + "正在聚合到车系级别...")
        
        grouped = df_processed.groupby(['brand', 'series'])
        results = []
        
        for (brand, series), group in tqdm(grouped, desc="车系聚合"):
            row = {
                'brand': brand,
                'series': series,
                'sample_count': len(group)
            }
            
            for dim in self.dimensions:
                # 1. 计算 Importance (I_dim)
                num_related = group[f'is_related_{dim}'].sum()
                total = len(group)
                i_dim = num_related / total if total > 0 else 0
                row[f'I_{dim}'] = round(i_dim, 4)
                
                # 2. 计算各成分的平均值
                # S_official
                s_official_col = f's_official_{dim}'
                s_official_values = group[s_official_col].dropna()
                s_official_mean = s_official_values.mean() if len(s_official_values) > 0 else None
                
                # S_bert
                s_bert_col = f's_bert_{dim}'
                s_bert_values = group[s_bert_col].dropna()
                s_bert_mean = s_bert_values.mean() if len(s_bert_values) > 0 else None
                
                # S_strong
                s_strong_col = f's_strong_{dim}'
                s_strong_values = group[s_strong_col].dropna()
                s_strong_mean = s_strong_values.mean() if len(s_strong_values) > 0 else None
                has_strong = len(s_strong_values) > 0
                
                # 3. 计算 Performance (P_dim) 使用加权组合
                if has_strong and s_strong_mean is not None:
                    # 有强信号: w1=0.2, w2=0.2, w3=0.6
                    components = []
                    weights = []
                    
                    if s_official_mean is not None:
                        components.append(s_official_mean)
                        weights.append(0.2)
                    
                    if s_bert_mean is not None:
                        components.append(s_bert_mean)
                        weights.append(0.2)
                    
                    components.append(s_strong_mean)
                    weights.append(0.6)
                    
                    # 归一化权重
                    total_weight = sum(weights)
                    weights = [w / total_weight for w in weights]
                    
                    p_dim = sum(c * w for c, w in zip(components, weights))
                else:
                    # 无强信号: w1=0.6, w2=0.4
                    components = []
                    weights = []
                    
                    if s_official_mean is not None:
                        components.append(s_official_mean)
                        weights.append(0.6)
                    
                    if s_bert_mean is not None:
                        components.append(s_bert_mean)
                        weights.append(0.4)
                    
                    if components:
                        # 归一化权重
                        total_weight = sum(weights)
                        weights = [w / total_weight for w in weights]
                        p_dim = sum(c * w for c, w in zip(components, weights))
                    else:
                        # 没有任何数据，使用默认值
                        p_dim = 0.5
                
                row[f'P_{dim}'] = round(p_dim, 4)
            
            results.append(row)
        
        df_result = pd.DataFrame(results)
        return df_result
    
    def run(self):
        """执行完整的IPA得分计算流程"""
        print(Fore.CYAN + "="*80)
        print(Fore.CYAN + "IPA 得分矩阵计算 - Step 1")
        print(Fore.CYAN + "="*80)
        
        # 1. 载入数据
        print(Fore.CYAN + f"\n正在载入数据: {self.input_file}")
        df = pd.read_csv(self.input_file)
        print(Fore.GREEN + f"✓ 成功载入 {len(df)} 条评论数据")
        print(Fore.GREEN + f"  涉及品牌: {df['brand'].nunique()} 个")
        print(Fore.GREEN + f"  涉及车系: {df['series'].nunique()} 个")
        
        # 2. 处理每条评论
        print(Fore.CYAN + f"\n正在处理每条评论的维度指标...")
        processed_rows = []
        
        # 使用tqdm显示进度
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理评论"):
            processed_row = self.process_single_review(row)
            processed_rows.append(processed_row)
        
        df_processed = pd.DataFrame(processed_rows)
        print(Fore.GREEN + f"✓ 完成评论级别处理")
        
        # 3. 聚合到车系级别
        df_scores = self.aggregate_to_series(df_processed)
        
        # 4. 输出结果
        print(Fore.CYAN + f"\n正在保存得分矩阵...")
        
        # 确保输出目录存在
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 按照指定格式输出列
        output_columns = ['brand', 'series', 'sample_count']
        for dim in self.dimensions:
            output_columns.extend([f'I_{dim}', f'P_{dim}'])
        
        df_scores[output_columns].to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 得分矩阵已保存: {self.output_file}")
        
        # 5. 输出统计信息
        print(Fore.CYAN + "\n" + "="*80)
        print(Fore.CYAN + "统计摘要")
        print(Fore.CYAN + "="*80)
        print(f"车系总数: {len(df_scores)}")
        print(f"样本量范围: {df_scores['sample_count'].min()} - {df_scores['sample_count'].max()}")
        print(f"平均样本量: {df_scores['sample_count'].mean():.1f}")
        
        print(Fore.CYAN + "\n各维度重要度(I)均值:")
        for dim in self.dimensions:
            i_mean = df_scores[f'I_{dim}'].mean()
            print(f"  {self.dimension_names_cn[dim]:6s}: {i_mean:.4f}")
        
        print(Fore.CYAN + "\n各维度满意度(P)均值:")
        for dim in self.dimensions:
            p_mean = df_scores[f'P_{dim}'].mean()
            print(f"  {self.dimension_names_cn[dim]:6s}: {p_mean:.4f}")
        
        print(Fore.CYAN + "\n前10个车系示例:")
        display_cols = ['brand', 'series', 'sample_count'] + [f'I_{self.dimensions[0]}', f'P_{self.dimensions[0]}']
        print(df_scores[display_cols].head(10).to_string(index=False))
        
        print(Fore.GREEN + "\n✓ IPA 得分矩阵计算完成！")


def main():
    """主函数"""
    computer = IPAScoreComputer()
    computer.run()


if __name__ == '__main__':
    main()
