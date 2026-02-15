#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户画像分析 - 阶段四：合并外部属性
将聚类结果与外部属性（车型/里程/地域等）合并，生成完整用户画像
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from colorama import init, Fore
import warnings

warnings.filterwarnings('ignore')
init(autoreset=True)


class PersonaAttributeMerger:
    """用户画像外部属性合并器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        
        # 输入文件
        self.cluster_labels_file = self.base_path / "Data" / "Analyzed" / "Persona" / "final_clustering" / "step3_cluster_labels.csv"
        self.ugc_file = self.base_path / "Data" / "Processed" / "ugc.csv"
        self.geo_mapping_file = self.base_path / "Analysis" / "Persona" / "geo_mapping.json"
        
        # 输出文件
        self.output_file = self.base_path / "Data" / "Analyzed" / "Persona" / "step4_user_persona_full.csv"
        
        # 用户画像名称映射
        self.cluster_names = {
            0: '全能均衡派',
            1: '传统务实派',
            2: '品质体验派',
            3: '内饰舒适控',
            4: '极致空间党',
            5: '极致操控党',
            6: '颜值至上派',
            7: '续航焦虑党'
        }
        
        # 加载地理映射
        self.load_geo_mapping()
    
    def load_geo_mapping(self):
        """加载地理位置映射字典"""
        print(Fore.CYAN + "正在加载地理位置映射...")
        try:
            with open(self.geo_mapping_file, 'r', encoding='utf-8') as f:
                geo_data = json.load(f)
                self.city_to_province = geo_data['city_to_province']
                self.province_to_region = geo_data['province_to_region']
            print(Fore.GREEN + f"✓ 成功加载地理映射")
            print(Fore.GREEN + f"  城市数量: {len(self.city_to_province)}")
            print(Fore.GREEN + f"  省份数量: {len(self.province_to_region)}")
        except Exception as e:
            print(Fore.RED + f"✗ 加载地理映射失败: {e}")
            raise
    
    def map_city_to_province(self, city):
        """将城市映射到省份"""
        if pd.isna(city) or city is None:
            return None
        
        city = str(city).strip()
        
        # 直接匹配
        if city in self.city_to_province:
            return self.city_to_province[city]
        
        # 尝试去除"市"后缀
        city_without_suffix = city.replace('市', '')
        if city_without_suffix in self.city_to_province:
            return self.city_to_province[city_without_suffix]
        
        # 四个直辖市特殊处理
        if city in ['北京', '上海', '天津', '重庆']:
            return city + '市'
        
        return None
    
    def map_province_to_region(self, province):
        """将省份映射到大区"""
        if pd.isna(province) or province is None:
            return None
        
        return self.province_to_region.get(province, None)
    
    def calculate_usage_frequency(self, row):
        """计算用车频率 = 里程 / 用车天数"""
        try:
            mileage = row.get('mileage', None)
            purchase_date = row.get('purchase_date', None)
            review_date = row.get('review_date', None)
            
            # 检查必要字段
            if pd.isna(mileage) or pd.isna(purchase_date) or pd.isna(review_date):
                return None
            
            mileage = float(mileage)
            
            # 解析日期
            try:
                purchase_dt = pd.to_datetime(purchase_date)
                review_dt = pd.to_datetime(review_date)
            except:
                return None
            
            # 计算天数差
            days_diff = (review_dt - purchase_dt).days
            
            # 至少使用1天
            if days_diff < 1:
                days_diff = 1
            
            # 计算频率（公里/天）
            frequency = mileage / days_diff
            
            return round(frequency, 2)
            
        except Exception as e:
            return None
    
    def categorize_usage_frequency(self, frequency):
        """将用车频率分类"""
        if pd.isna(frequency) or frequency is None:
            return '未知'
        
        frequency = float(frequency)
        
        if frequency < 10:
            return '低频用车'
        elif frequency < 30:
            return '中频用车'
        elif frequency < 60:
            return '高频用车'
        else:
            return '超高频用车'
    
    def categorize_mileage(self, mileage):
        """里程分类"""
        if pd.isna(mileage) or mileage is None:
            return '未知'
        
        mileage = float(mileage)
        
        if mileage < 5000:
            return '新车期'
        elif mileage < 20000:
            return '磨合期'
        elif mileage < 50000:
            return '稳定期'
        elif mileage < 100000:
            return '成熟期'
        else:
            return '高里程'
    
    def categorize_price(self, price):
        """购车价格分类"""
        if pd.isna(price) or price is None:
            return '未知'
        
        price = float(price)
        
        if price < 15:
            return '15万以下'
        elif price < 25:
            return '15-25万'
        elif price < 35:
            return '25-35万'
        elif price < 50:
            return '35-50万'
        else:
            return '50万以上'
    
    def categorize_range(self, real_range):
        """实际续航分类"""
        if pd.isna(real_range) or real_range is None:
            return '未知'
        
        real_range = float(real_range)
        
        if real_range < 300:
            return '300km以下'
        elif real_range < 500:
            return '300-500km'
        elif real_range < 700:
            return '500-700km'
        else:
            return '700km以上'
    
    def categorize_energy_consumption(self, consumption):
        """能耗分类"""
        if pd.isna(consumption) or consumption is None:
            return '未知'
        
        consumption = float(consumption)
        
        if consumption < 15:
            return '低能耗'
        elif consumption < 20:
            return '中能耗'
        else:
            return '高能耗'
    
    def run(self):
        """执行完整的属性合并流程"""
        print(Fore.CYAN + "="*80)
        print(Fore.CYAN + "用户画像外部属性合并 - Step 4")
        print(Fore.CYAN + "="*80)
        
        # 1. 载入聚类标签（已包含注意力向量）
        print(Fore.CYAN + f"\n正在载入聚类标签和注意力向量: {self.cluster_labels_file}")
        df_clusters = pd.read_csv(self.cluster_labels_file)
        print(Fore.GREEN + f"✓ 成功载入 {len(df_clusters)} 条聚类标签（含注意力向量）")
        
        # 2. 载入UGC数据
        print(Fore.CYAN + f"\n正在载入UGC数据: {self.ugc_file}")
        df_ugc = pd.read_csv(self.ugc_file)
        print(Fore.GREEN + f"✓ 成功载入 {len(df_ugc)} 条评论数据")
        
        # 3. 合并数据
        print(Fore.CYAN + f"\n正在合并数据...")
        df_merged = pd.merge(df_clusters, df_ugc, on='review_id', how='left')
        print(Fore.GREEN + f"✓ 合并完成，共 {len(df_merged)} 条记录")
        
        # 4. 添加用户画像名称
        print(Fore.CYAN + f"\n正在添加用户画像名称...")
        df_merged['persona_name'] = df_merged['cluster'].map(self.cluster_names)
        print(Fore.GREEN + f"✓ 用户画像名称添加完成")
        
        # 5. 添加地理位置字段
        print(Fore.CYAN + f"\n正在处理地理位置映射...")
        df_merged['province'] = df_merged['purchase_location'].apply(self.map_city_to_province)
        df_merged['region'] = df_merged['province'].apply(self.map_province_to_region)
        
        # 统计映射成功率
        province_mapped = df_merged['province'].notna().sum()
        region_mapped = df_merged['region'].notna().sum()
        total = len(df_merged)
        print(Fore.GREEN + f"✓ 省份映射成功率: {province_mapped}/{total} ({province_mapped/total*100:.1f}%)")
        print(Fore.GREEN + f"✓ 大区映射成功率: {region_mapped}/{total} ({region_mapped/total*100:.1f}%)")
        
        # 6. 添加地理位置字段
        print(Fore.CYAN + f"\n正在处理地理位置映射...")
        df_merged['province'] = df_merged['purchase_location'].apply(self.map_city_to_province)
        df_merged['region'] = df_merged['province'].apply(self.map_province_to_region)
        
        # 统计映射成功率
        province_mapped = df_merged['province'].notna().sum()
        region_mapped = df_merged['region'].notna().sum()
        total = len(df_merged)
        print(Fore.GREEN + f"✓ 省份映射成功率: {province_mapped}/{total} ({province_mapped/total*100:.1f}%)")
        print(Fore.GREEN + f"✓ 大区映射成功率: {region_mapped}/{total} ({region_mapped/total*100:.1f}%)")
        
        # 6. 计算用车频率
        print(Fore.CYAN + f"\n正在计算用车频率...")
        df_merged['usage_frequency_km_per_day'] = df_merged.apply(
            self.calculate_usage_frequency, axis=1
        )
        df_merged['usage_frequency_category'] = df_merged['usage_frequency_km_per_day'].apply(
            self.categorize_usage_frequency
        )
        
        freq_calculated = df_merged['usage_frequency_km_per_day'].notna().sum()
        print(Fore.GREEN + f"✓ 用车频率计算成功: {freq_calculated}/{total} ({freq_calculated/total*100:.1f}%)")
        
        # 7. 添加其他分类字段
        print(Fore.CYAN + f"\n正在添加分类字段...")
        df_merged['mileage_category'] = df_merged['mileage'].apply(self.categorize_mileage)
        df_merged['price_category'] = df_merged['purchase_price'].apply(self.categorize_price)
        df_merged['range_category'] = df_merged['real_range'].apply(self.categorize_range)
        df_merged['energy_consumption_category'] = df_merged['energy_consumption'].apply(
            self.categorize_energy_consumption
        )
        
        # 8. 选择输出字段
        output_columns = [
            # 基础标识
            'review_id',
            'cluster',
            'persona_name',
            
            # 注意力向量（7个维度的attention权重）
            'w_appearance',
            'w_interior',
            'w_space',
            'w_intelligence',
            'w_driving',
            'w_range',
            'w_value',
            
            # 车辆信息
            'brand',
            'series',
            'model',
            
            # 购车与使用信息
            'mileage',
            'mileage_category',
            'purchase_price',
            'price_category',
            'purchase_date',
            'review_date',
            
            # 地理位置
            'purchase_location',
            'province',
            'region',
            
            # 性能数据
            'real_range',
            'range_category',
            'energy_consumption',
            'energy_consumption_category',
            'season_type',
            
            # 用车频率
            'usage_frequency_km_per_day',
            'usage_frequency_category',
            
            # 官方评分维度（保留原始评分）
            'space_score',
            'driving_score',
            'range_score',
            'appearance_score',
            'interior_score',
            'value_score',
            'intelligence_score'
        ]
        
        # 确保所有列都存在
        existing_columns = [col for col in output_columns if col in df_merged.columns]
        df_output = df_merged[existing_columns].copy()
        
        # 9. 保存结果
        print(Fore.CYAN + f"\n正在保存完整用户画像...")
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        df_output.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(Fore.GREEN + f"✓ 完整用户画像已保存: {self.output_file}")
        
        # 10. 输出统计信息
        print(Fore.CYAN + "\n" + "="*80)
        print(Fore.CYAN + "统计摘要")
        print(Fore.CYAN + "="*80)
        
        print(Fore.CYAN + "\n【聚类分布】")
        cluster_dist = df_output['cluster'].value_counts().sort_index()
        for cluster, count in cluster_dist.items():
            persona_name = self.cluster_names.get(cluster, '未知')
            print(f"  Cluster {cluster} ({persona_name:8s}): {count:6d} ({count/len(df_output)*100:5.2f}%)")
        
        print(Fore.CYAN + "\n【品牌分布】 (Top 10)")
        brand_dist = df_output['brand'].value_counts().head(10)
        for brand, count in brand_dist.items():
            print(f"  {brand:10s}: {count:5d}")
        
        print(Fore.CYAN + "\n【地区分布】")
        region_dist = df_output['region'].value_counts()
        for region, count in region_dist.items():
            if pd.notna(region):
                print(f"  {region:6s}: {count:5d} ({count/len(df_output)*100:5.2f}%)")
        
        print(Fore.CYAN + "\n【价格段分布】")
        price_dist = df_output['price_category'].value_counts()
        for category, count in price_dist.items():
            if category != '未知':
                print(f"  {category:10s}: {count:5d}")
        
        print(Fore.CYAN + "\n【用车频率分布】")
        freq_dist = df_output['usage_frequency_category'].value_counts()
        for category, count in freq_dist.items():
            print(f"  {category:12s}: {count:5d}")
        
        print(Fore.CYAN + "\n【里程分布】")
        mileage_dist = df_output['mileage_category'].value_counts()
        for category, count in mileage_dist.items():
            if category != '未知':
                print(f"  {category:8s}: {count:5d}")
        
        print(Fore.CYAN + "\n【续航分布】")
        range_dist = df_output['range_category'].value_counts()
        for category, count in range_dist.items():
            if category != '未知':
                print(f"  {category:12s}: {count:5d}")
        
        print(Fore.CYAN + "\n【季节分布】")
        season_dist = df_output['season_type'].value_counts()
        for season, count in season_dist.items():
            if pd.notna(season):
                print(f"  {season:15s}: {count:5d}")
        
        # 11. 输出数据质量报告
        print(Fore.CYAN + "\n【数据完整度】")
        key_fields = ['persona_name', 'w_appearance', 'w_interior', 'w_space', 'w_intelligence', 
                      'w_driving', 'w_range', 'w_value',
                      'mileage', 'purchase_price', 'province', 'real_range', 
                      'energy_consumption', 'usage_frequency_km_per_day']
        for field in key_fields:
            if field in df_output.columns:
                non_null_count = df_output[field].notna().sum()
                completeness = non_null_count / len(df_output) * 100
                print(f"  {field:30s}: {completeness:5.1f}%")
        
        # 12. 输出注意力向量统计
        print(Fore.CYAN + "\n【注意力向量统计】")
        attention_cols = ['w_appearance', 'w_interior', 'w_space', 'w_intelligence', 
                         'w_driving', 'w_range', 'w_value']
        if all(col in df_output.columns for col in attention_cols):
            print(Fore.CYAN + "  各维度平均注意力权重:")
            for col in attention_cols:
                mean_val = df_output[col].mean()
                print(f"    {col:20s}: {mean_val:.4f}")
        
        print(Fore.GREEN + "\n✓ 用户画像外部属性合并完成！")


def main():
    """主函数"""
    merger = PersonaAttributeMerger()
    merger.run()


if __name__ == '__main__':
    main()
