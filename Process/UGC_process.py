#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UGC数据处理脚本 - 清洗和标准化用户口碑数据
将所有品牌的口碑数据合并为统一格式
"""

import pandas as pd
import re
import hashlib
from pathlib import Path
from datetime import datetime
from colorama import init, Fore

init(autoreset=True)


class UGCProcessor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.ugc_folder = self.base_path / "Data" / "Raw" / "UGC Raw"
        self.output_file = self.base_path / "Data" / "Processed" / "ugc.csv"
        
        # 最小文本长度阈值
        self.min_text_length = 10
        
        # 季节映射
        self.season_map = {
            '春秋': 'spring_autumn',
            '夏季': 'summer',
            '冬季': 'winter'
        }
    
    def generate_review_id(self, brand, model, review_date, most_satisfied, least_satisfied):
        """
        生成评论唯一ID - 基于关键字段的哈希值
        使用品牌、型号、评论日期和部分评论内容生成稳定的哈希ID
        """
        # 组合关键字段
        id_components = [
            str(brand or ''),
            str(model or ''),
            str(review_date or ''),
            str(most_satisfied or '')[:50],  # 取前50字符
            str(least_satisfied or '')[:50]   # 取前50字符
        ]
        
        # 生成唯一字符串
        id_string = '|'.join(id_components)
        
        # 计算MD5哈希值（取前12位作为ID）
        hash_object = hashlib.md5(id_string.encode('utf-8'))
        review_id = hash_object.hexdigest()[:12]
        
        return review_id
    
    def extract_brand_series_model(self, scraped_model, actual_model, file_brand=None):
        """从车型名称中提取品牌、车系、具体型号"""
        if pd.notna(actual_model) and actual_model.strip():
            model_text = actual_model.strip()
        else:
            model_text = scraped_model.strip() if pd.notna(scraped_model) else ""
        
        if not model_text:
            return None, None, None
        
        brand_map = {
            'AITO 问界': 'AITO 问界',
            '问界': 'AITO 问界',
            '小米汽车': '小米汽车',
            '理想汽车': '理想汽车',
            '比亚迪': '比亚迪',
            '蔚来': '蔚来',
            '理想': '理想汽车',
            '小鹏': '小鹏',
            '极氪': '极氪',
            '特斯拉': '特斯拉',
            '奔驰': '奔驰',
            '宝马': '宝马',
            '奥迪': '奥迪',
            '沃尔沃': '沃尔沃',
            '小米': '小米汽车'
        }
        
        brand = None
        for key, value in brand_map.items():
            if key in model_text:
                brand = value
                break
        
        if not brand and file_brand:
            brand = brand_map.get(file_brand, file_brand)
        
        series = self.extract_series_from_model(model_text, brand)
        model = model_text
        
        return brand, series, model
    
    def extract_series_from_model(self, model_text, brand):
        """从完整型号中智能提取车系名称"""
        if not model_text or not brand:
            return None
        
        series_text = model_text
        for brand_key in ['奔驰', '宝马', '奥迪', '沃尔沃', '比亚迪', '蔚来', '理想', '小鹏', '极氪', '特斯拉', '小米', '问界', 'AITO', 'Model', 'BMW']:
            series_text = series_text.replace(brand_key, '')
        
        import re
        
        match = re.match(r'^\s*(.+?)\s+\d{4}款', model_text)
        if match:
            series_candidate = match.group(1).strip()
            # 移除品牌前缀
            for brand_prefix in ['奔驰', '宝马', '奥迪', '沃尔沃', '比亚迪', '蔚来', '理想', '小鹏', '极氪', '特斯拉', '小米', 'AITO ']:
                if series_candidate.startswith(brand_prefix):
                    series_candidate = series_candidate[len(brand_prefix):].strip()
            
            # 处理特殊情况
            if series_candidate:
                # 统一某些车系名称
                series_map = {
                    '宋PLUS_': '宋PLUS_新能源',
                    '宋Pro_': '宋Pro_新能源',
                    '宋MAX': '宋MAX新能源',
                    '唐_': '唐_新能源',
                    '秦': '秦',
                    '汉': '汉',
                    'C级': 'C级新能源',
                    'E级': 'E级新能源',
                    'GLC': 'GLC新能源',
                    'GLE': 'GLE新能源',
                    'G级': 'G级新能源',
                    'CLA': 'CLA新能源'
                }
                
                for key, value in series_map.items():
                    if key in series_candidate:
                        return value
                
                if '新能源' in series_candidate:
                    return series_candidate
                
                if brand in ['比亚迪']:
                    if series_candidate in ['汉', '唐', '秦', '宋', '元', '夏']:
                        return series_candidate
                    if series_candidate.startswith('海'):
                        return series_candidate
                    if any(x in series_candidate for x in ['PLUS', 'Pro', 'MAX', 'DM-i', 'EV']):
                        base = series_candidate.split()[0] if ' ' in series_candidate else series_candidate.split('_')[0]
                        return base
                    if re.match(r'^[eM]\d+', series_candidate):
                        return series_candidate.split()[0]
                
                return series_candidate
        
        if 'Model' in model_text:
            match = re.search(r'Model\s+[A-Z0-9]+', model_text)
            if match:
                return match.group(0)
        
        if brand == 'AITO 问界':
            match = re.search(r'M\d+', model_text)
            if match:
                return '问界' + match.group(0)
        
        if brand == '理想汽车':
            if 'MEGA' in model_text:
                return '理想MEGA'
            match = re.search(r'[iL]\d+', model_text)
            if match:
                return '理想' + match.group(0)
        
        # 对于小鹏：P7、G6等
        if brand == '小鹏':
            match = re.search(r'[PGX]\d+', model_text)
            if match:
                return '小鹏' + match.group(0)
            if 'MONA' in model_text:
                return '小鹏MONA M03'
        
        # 对于极氪：001、007等
        if brand == '极氪':
            match = re.search(r'\d{3}', model_text)
            if match:
                return '极氪' + match.group(0)
            if 'MIX' in model_text:
                return '极氪MIX'
            match = re.search(r'[79]X', model_text)
            if match:
                return '极氪' + match.group(0)
        
        # 对于蔚来：ES6、ET5等
        if brand == '蔚来':
            match = re.search(r'E[SCT]\d+', model_text)
            if match:
                return match.group(0)
        
        # 对于宝马：i5、iX等
        if brand == '宝马':
            match = re.search(r'i[X0-9]+', model_text)
            if match:
                return match.group(0)
            if 'XM' in model_text:
                return 'XM'
            if 'M5' in model_text:
                return 'M5新能源'
        
        # 对于奥迪：Q5 e-tron等
        if brand == '奥迪':
            match = re.search(r'Q\d+[L]?\s*e-tron', model_text)
            if match:
                return match.group(0).replace(' ', ' ')
        
        # 对于沃尔沃
        if brand == '沃尔沃':
            if 'EX' in model_text:
                match = re.search(r'EX\d+', model_text)
                if match:
                    return match.group(0)
            if 'EM' in model_text:
                return 'EM90'
            match = re.search(r'[SX]C?\d+', model_text)
            if match:
                return match.group(0) + '插电式混动'
        
        # 对于小米
        if brand == '小米汽车':
            if 'SU7' in model_text:
                return '小米SU7'
            if 'YU7' in model_text:
                return '小米YU7'
        
        return None
    
    def extract_number(self, text):
        """从文本中提取数字"""
        if pd.isna(text) or text == '':
            return None
        
        text = str(text).strip()
        
        # 提取所有数字（包括小数）
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        return None
    
    def parse_date(self, date_str):
        """解析日期字符串"""
        if pd.isna(date_str) or date_str == '':
            return None
        
        date_str = str(date_str).strip()
        
        # 尝试不同的日期格式
        formats = ['%Y-%m-%d', '%Y-%m', '%Y/%m/%d', '%Y/%m']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except:
                continue
        
        return None
    
    def clean_text(self, text, min_length=None):
        """清洗文本内容 - 增强版emoji和特殊字符清理"""
        if pd.isna(text) or text == '' or text == '暂无':
            return None
        
        text = str(text).strip()
        
        # 1. 去除所有emoji表情（使用精确的Unicode范围，避免误删中文）
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 表情符号 Emoticons
            "\U0001F300-\U0001F5FF"  # 符号和象形文字 Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # 交通和地图符号 Transport & Map
            "\U0001F700-\U0001F77F"  # 炼金术符号 Alchemical Symbols
            "\U0001F780-\U0001F7FF"  # 几何图形扩展 Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # 补充箭头C Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # 补充符号和象形文字 Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # 象形文字扩展A Extended-A
            "\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展A Symbols and Pictographs Extended-A
            "\U00002600-\U000026FF"  # 杂项符号 Miscellaneous Symbols
            "\U00002700-\U000027BF"  # 装饰符号 Dingbats
            "\U0001F1E0-\U0001F1FF"  # 旗帜 Flags (iOS)
            "\u200d"                 # 零宽连接符 Zero Width Joiner
            "\ufe0f"                 # 变体选择符-16 Variation Selector
            "\u2640-\u2642"          # 性别符号 Gender symbols
            "\u2600-\u2B55"          # 各种符号
            "\u23cf"                 # 弹出符号
            "\u23e9-\u23ef"          # 三角形符号
            "\u23f0-\u23f3"          # 时钟
            "\u23f8-\u23fa"          # 媒体控制
            "]+", 
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # 2. 去除特殊符号和图形字符（保留中文标点）
        text = re.sub(r'[⭐★☆●○■□▲△▼▽◆◇♦♢✓✔✕✖✗✘♥♡❤💗💓💕💖💙💚💛💜🖤💝💞💟❣]', '', text)
        
        # 3. 去除特殊空格和格式字符（但不包括中文标点区域）
        text = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F]', '', text)
        
        # 4. 去除控制字符
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # 5. 统一全角空格为半角空格，去除换行符和制表符
        text = text.replace('\u3000', ' ')  # 全角空格
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 6. 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 7. 再次清理首尾空白
        text = text.strip()
        
        # 8. 检查长度
        if min_length is None:
            min_length = self.min_text_length
        
        if len(text) < min_length:
            return None
        
        return text
    
    def parse_mileage_consumption(self, row, season_prefix):
        """解析续航和电耗数据"""
        consumption_col = f'{season_prefix}电耗'
        mileage_col = f'{season_prefix}续航'
        
        consumption = self.extract_number(row.get(consumption_col, None))
        mileage_text = row.get(mileage_col, None)
        mileage = self.extract_number(mileage_text)
        
        return consumption, mileage
    
    def process_file(self, file_path):
        """处理单个CSV文件"""
        print(Fore.GREEN + f"\n处理文件: {file_path.name}")
        
        # 从文件名提取品牌
        file_brand = file_path.stem.replace('_口碑数据', '')
        
        # 读取CSV
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            df = pd.read_csv(file_path, encoding='gbk')
        
        print(Fore.WHITE + f"  原始数据: {len(df)} 条")
        
        processed_data = []
        
        for idx, row in df.iterrows():
            # 提取品牌、车系、型号
            brand, series, model = self.extract_brand_series_model(
                row.get('抓取车型', None),
                row.get('实际型号', None),
                file_brand  # 传入文件品牌作为后备
            )
            
            if not brand or not model:
                continue
            
            # 基本信息
            record = {
                'brand': brand,
                'series': series if series else 'Unknown',
                'model': model,
                'mileage': self.extract_number(row.get('行驶里程', None)),
                'purchase_price': self.extract_number(row.get('裸车购买价', None)),
                'purchase_date': self.parse_date(row.get('购买时间', None)),
                'purchase_location': str(row.get('购买地点', '')).strip() if pd.notna(row.get('购买地点', None)) else None,
                'review_date': self.parse_date(row.get('评论发布时间', None))
            }
            
            # 处理续航和电耗数据 - 按优先级合并：冬季 > 夏季 > 春秋
            # 只保留一个季节的数据
            real_range = None
            energy_consumption = None
            season_type = None
            
            # 优先级顺序：冬季 -> 夏季 -> 春秋
            priority_order = [('冬季', 'winter'), ('夏季', 'summer'), ('春秋', 'spring_autumn')]
            
            for season_cn, season_en in priority_order:
                consumption, mileage = self.parse_mileage_consumption(row, season_cn)
                if mileage is not None:  # 如果这个季节有续航数据
                    real_range = mileage
                    energy_consumption = consumption
                    season_type = season_en
                    break  # 找到第一个有数据的就停止
            
            record['real_range'] = real_range
            record['energy_consumption'] = energy_consumption
            record['season_type'] = season_type
            
            # 评分数据
            score_fields = {
                'space_score': '空间评分',
                'driving_score': '驾驶感受评分',
                'range_score': '续航评分',
                'appearance_score': '外观评分',
                'interior_score': '内饰评分',
                'value_score': '性价比评分',
                'intelligence_score': '智能化评分'
            }
            
            for en_field, cn_field in score_fields.items():
                score = row.get(cn_field, None)
                if pd.notna(score):
                    try:
                        record[en_field] = int(score)
                    except:
                        record[en_field] = None
                else:
                    record[en_field] = None
            
            # 评论文本（清洗过短内容）
            review_fields = {
                'space_review': '空间评分评价',
                'driving_review': '驾驶感受评分评价',
                'range_review': '续航评分评价',
                'appearance_review': '外观评分评价',
                'interior_review': '内饰评分评价',
                'value_review': '性价比评分评价',
                'intelligence_review': '智能化评分评价',
                'most_satisfied': '最满意',
                'least_satisfied': '最不满意'
            }
            
            for en_field, cn_field in review_fields.items():
                text = row.get(cn_field, None)
                record[en_field] = self.clean_text(text)
            
            # 生成唯一评论ID
            record['review_id'] = self.generate_review_id(
                brand, 
                model, 
                record['review_date'],
                record.get('most_satisfied'),
                record.get('least_satisfied')
            )
            
            processed_data.append(record)
        
        print(Fore.WHITE + f"  处理后数据: {len(processed_data)} 条 (保留率: {len(processed_data)/len(df)*100:.1f}%)")
        
        return processed_data
    
    def merge_all_files(self):
        """合并所有UGC文件"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "开始处理UGC数据")
        print(Fore.CYAN + "=" * 70)
        
        all_data = []
        
        # 遍历所有CSV文件
        csv_files = sorted(self.ugc_folder.glob("*_口碑数据.csv"))
        
        for file_path in csv_files:
            data = self.process_file(file_path)
            all_data.extend(data)
        
        # 创建DataFrame
        df_final = pd.DataFrame(all_data)
        
        # 调整列顺序
        column_order = [
            'review_id',
            'brand', 'series', 'model',
            'mileage', 'purchase_price', 'purchase_date', 'purchase_location', 'review_date',
            'real_range', 'energy_consumption', 'season_type',
            'space_score', 'space_review',
            'driving_score', 'driving_review',
            'range_score', 'range_review',
            'appearance_score', 'appearance_review',
            'interior_score', 'interior_review',
            'value_score', 'value_review',
            'intelligence_score', 'intelligence_review',
            'most_satisfied', 'least_satisfied'
        ]
        
        # 确保所有列都存在
        for col in column_order:
            if col not in df_final.columns:
                df_final[col] = None
        
        df_final = df_final[column_order]
        
        # 保存结果
        df_final.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        
        # 统计信息
        self.print_statistics(df_final, csv_files)
        
        return df_final
    
    def print_statistics(self, df, csv_files):
        """打印统计信息"""
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.GREEN + "UGC数据处理完成!")
        print(Fore.CYAN + f"{'=' * 70}")
        
        print(Fore.YELLOW + f"\n统计信息:")
        print(Fore.WHITE + f"  处理文件数: {len(csv_files)}")
        print(Fore.WHITE + f"  总评论数: {len(df)}")
        print(Fore.WHITE + f"  品牌数: {df['brand'].nunique()}")
        print(Fore.WHITE + f"  车系数: {df['series'].nunique()}")
        print(Fore.WHITE + f"  车型数: {df['model'].nunique()}")
        
        print(Fore.YELLOW + f"\n各品牌评论数:")
        brand_counts = df['brand'].value_counts()
        for brand, count in brand_counts.items():
            print(Fore.WHITE + f"  {brand}: {count}条")
        
        print(Fore.YELLOW + f"\n数据完整性:")
        print(Fore.WHITE + f"  有购买价格: {df['purchase_price'].notna().sum()}条 ({df['purchase_price'].notna().sum()/len(df)*100:.1f}%)")
        print(Fore.WHITE + f"  有行驶里程: {df['mileage'].notna().sum()}条 ({df['mileage'].notna().sum()/len(df)*100:.1f}%)")
        print(Fore.WHITE + f"  有续航数据: {df['real_range'].notna().sum()}条 ({df['real_range'].notna().sum()/len(df)*100:.1f}%)")
        
        # 统计各季节数据分布
        if 'season_type' in df.columns:
            season_counts = df['season_type'].value_counts()
            print(Fore.WHITE + f"  季节分布:")
            for season, count in season_counts.items():
                season_names = {'winter': '冬季', 'summer': '夏季', 'spring_autumn': '春秋'}
                print(Fore.WHITE + f"    {season_names.get(season, season)}: {count}条")
        
        print(Fore.WHITE + f"  有最满意评价: {df['most_satisfied'].notna().sum()}条 ({df['most_satisfied'].notna().sum()/len(df)*100:.1f}%)")
        print(Fore.WHITE + f"  有最不满意评价: {df['least_satisfied'].notna().sum()}条 ({df['least_satisfied'].notna().sum()/len(df)*100:.1f}%)")
        
        print(Fore.YELLOW + f"\n平均评分:")
        score_fields = ['space_score', 'driving_score', 'range_score', 'appearance_score', 
                       'interior_score', 'value_score', 'intelligence_score']
        score_names = {'space_score': '空间', 'driving_score': '驾驶', 'range_score': '续航',
                      'appearance_score': '外观', 'interior_score': '内饰', 'value_score': '性价比',
                      'intelligence_score': '智能化'}
        
        for field in score_fields:
            avg_score = df[field].mean()
            if pd.notna(avg_score):
                print(Fore.WHITE + f"  {score_names[field]}: {avg_score:.2f}/5")
        
        print(Fore.CYAN + f"\n输出文件: {self.output_file}")
        print(Fore.GREEN + f"文件大小: {self.output_file.stat().st_size / 1024:.1f} KB")
        print(Fore.CYAN + f"{'=' * 70}")
        
        # 打印示例数据
        if len(df) > 0:
            print(Fore.YELLOW + f"\n示例数据 (第1条):")
            sample = df.iloc[0]
            print(Fore.WHITE + f"  评论ID: {sample['review_id']}")
            print(Fore.WHITE + f"  品牌: {sample['brand']}")
            print(Fore.WHITE + f"  车系: {sample['series']}")
            print(Fore.WHITE + f"  型号: {sample['model']}")
            print(Fore.WHITE + f"  里程: {sample['mileage']}km")
            print(Fore.WHITE + f"  购买价: {sample['purchase_price']}万")
            if pd.notna(sample['most_satisfied']) and sample['most_satisfied']:
                satisfied_text = str(sample['most_satisfied'])
                print(Fore.WHITE + f"  最满意: {satisfied_text[:100]}...")


def main():
    processor = UGCProcessor()
    processor.merge_all_files()


if __name__ == '__main__':
    main()
