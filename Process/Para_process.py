import os
import json
import pandas as pd
import hashlib
from pathlib import Path
from colorama import Fore, init

# 初始化colorama
init(autoreset=True)


class ParaProcessor:
    def __init__(self):
        self.raw_folder = Path(__file__).parent.parent / "Data" / "Raw" / "Para Raw"
        self.output_folder = Path(__file__).parent.parent / "Data" / "Processed"
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # 字段映射规则（原始字段名 -> 标准字段名）
        self.field_mapping = {
            # 身份与基础
            '厂商': ['厂商', '品牌'],
            '系列': ['车系', '系列'],
            '车型': ['车型名称', '车型'],
            '级别': ['级别', '车辆级别'],
            '长*宽*高(mm)': ['长*宽*高(mm)', '长宽高(mm)', '车身尺寸(mm)'],
            '轴距(mm)': ['轴距(mm)', '轴距'],
            '厂商指导价(元)': ['厂商指导价(元)', '官方指导价(元)', '指导价(元)'],
            '座位数': ['座位数(个)', '座位数', '座椅数', '座位'],
            
            # 核心性能
            '官方0-100km/h加速(s)': ['官方0-100km/h加速(s)', '0-100km/h加速时间(s)', '百公里加速(s)'],
            '电池能量(kWh)': ['电池能量(kWh)', '电池容量(kWh)', '动力电池容量(kWh)'],
            
            # 驱动方式
            'CLTC纯电续航里程(km)': ['CLTC纯电续航里程(km)', '纯电续航里程(km)', 'CLTC续航(km)', 'WLTC纯电续航里程(km)'],
            '电池类型': ['电池类型', '动力电池类型'],
            
            # 底盘与操控
            '前悬架类型': ['前悬架类型', '前悬挂类型'],
            '后悬架类型': ['后悬架类型', '后悬挂类型'],
            
            # 智能
            '座舱芯片': ['座舱芯片', '芯片品牌'],
            '智驾芯片': ['智驾芯片', '自动驾驶芯片'],
            '中控屏幕尺寸': ['中控屏幕尺寸', '中控液晶屏尺寸', '中控屏尺寸'],
            '激光雷达数量': ['激光雷达数量', '激光雷达'],
            
            # 新增：智能座舱
            '车机智能芯片': ['车机智能芯片', '座舱芯片', '中控芯片'],
            '车载智能系统': ['车载智能系统', '车机系统', '智能网联系统'],
            
            # 新增：智能驾驶
            '辅助驾驶芯片': ['辅助驾驶芯片', '自动驾驶芯片', 'ADAS芯片'],
            '辅助驾驶系统': ['辅助驾驶系统', '智能驾驶辅助系统', '自动驾驶系统'],
        }
        
        # 标准字段列表
        self.standard_fields = [
            'ID', '厂商', '系列', '车型', '级别', 
            '长*宽*高(mm)', '轴距(mm)', '厂商指导价(元)', '座位数',
            '官方0-100km/h加速(s)', '电池能量(kWh)',
            'CLTC纯电续航里程(km)', '电池类型',
            '前悬架类型', '后悬架类型',
            '座舱芯片', '智驾芯片', '中控屏幕尺寸', '激光雷达数量',
            '雷达数量'
        ]
    
    def generate_id(self, brand, series, model):
        """生成唯一ID"""
        unique_str = f"{brand}_{series}_{model}"
        return hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:16]
    
    def clean_numeric_value(self, value_str, value_type='float'):
        """清洗并转换数值类型数据"""
        if value_str == 'unknown' or not value_str:
            return 0 if value_type in ['int', 'float', 'price'] else 'Unknown'
        
        import re
        value_str = str(value_str).strip()
        
        if value_type == 'price':
            numbers = re.findall(r'[\d.]+', value_str)
            if numbers:
                return float(numbers[0])
            return 0
        
        elif value_type == 'int':
            numbers = re.findall(r'\d+', value_str)
            if numbers:
                return int(numbers[0])
            return 0
        
        elif value_type == 'float':
            numbers = re.findall(r'[\d.]+', value_str)
            if numbers:
                return float(numbers[0])
            return 0
        
        return 0
    
    def clean_string_value(self, value_str):
        """清洗字符串值"""
        if value_str == 'unknown' or not value_str or value_str.strip() == '':
            return 'Unknown'
        return value_str.strip()
    
    def standardize_vehicle_data(self, raw_data):
        """将原始数据标准化为嵌套结构和正确的数据类型"""
        return {
            # 基础信息
            'id': raw_data['ID'],
            'brand': raw_data['厂商'],
            'series': raw_data['系列'],
            'model': raw_data['车型'],
            'level': self.clean_string_value(raw_data['级别']),
            
            # 价格与座位
            'price': self.clean_numeric_value(raw_data['厂商指导价(元)'], 'price'),
            'seats': self.clean_numeric_value(raw_data['座位数'], 'int'),
            
            # 尺寸
            'dimensions': {
                'length_width_height': self.clean_string_value(raw_data['长*宽*高(mm)']),
                'wheelbase': self.clean_numeric_value(raw_data['轴距(mm)'], 'int')
            },
            
            # 性能
            'performance': {
                'acceleration_0_100': self.clean_numeric_value(raw_data['官方0-100km/h加速(s)'], 'float')
            },
            
            # 电池与续航
            'battery': {
                'capacity': self.clean_numeric_value(raw_data['电池能量(kWh)'], 'float'),
                'type': self.clean_string_value(raw_data['电池类型']),
                'range_cltc': self.clean_numeric_value(raw_data['CLTC纯电续航里程(km)'], 'int')
            },
            
            # 底盘
            'chassis': {
                'front_suspension': self.clean_string_value(raw_data['前悬架类型']),
                'rear_suspension': self.clean_string_value(raw_data['后悬架类型'])
            },
            
            # 智能化
            'intelligence': {
                # 智能座舱 (Cockpit)
                'cockpit': {
                    'chip': self.clean_string_value(raw_data['车机智能芯片']),
                    'system': self.clean_string_value(raw_data['车载智能系统']),
                    'screen_size': self.clean_numeric_value(raw_data['中控屏幕尺寸'], 'float')
                },
                # 智能驾驶 (ADAS)
                'adas': {
                    'chip': self.clean_string_value(raw_data['辅助驾驶芯片']),
                    'system': self.clean_string_value(raw_data['辅助驾驶系统']),
                    'lidar_count': self.clean_numeric_value(raw_data['激光雷达数量'], 'int'),
                    'radar_info': self.clean_string_value(raw_data['雷达数量'])
                }
            }
        }
    
    def find_field_value(self, df, field_name):
        """根据字段映射规则查找字段值"""
        possible_names = self.field_mapping.get(field_name, [field_name])
        
        for name in possible_names:
            if name in df.columns:
                if df[name].empty:
                    continue
                value = df[name].iloc[0]
                # 转换为Python原生类型
                if pd.isna(value) or str(value).strip() in ['-', '', 'nan']:
                    continue
                return str(value).strip()
        
        return 'unknown'
    
    def parse_radar_info(self, df):
        """解析雷达信息"""
        # 查找雷达相关字段
        radar_fields = {
            'ultrasonic': ['超声波雷达数量', '超声波雷达', '倒车雷达'],
            'millimeter': ['毫米波雷达数量', '毫米波雷达'],
            'laser': ['激光雷达数量', '激光雷达']
        }
        
        radar_counts = {'U': 0, 'M': 0, 'L': 0}
        
        # 超声波雷达
        for field in radar_fields['ultrasonic']:
            if field in df.columns:
                value = str(df[field].iloc[0])
                if value and value != 'nan' and value != '-':
                    # 提取数字
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        radar_counts['U'] = int(numbers[0])
                    break
        
        # 毫米波雷达
        for field in radar_fields['millimeter']:
            if field in df.columns:
                value = str(df[field].iloc[0])
                if value and value != 'nan' and value != '-':
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        radar_counts['M'] = int(numbers[0])
                    break
        
        # 激光雷达
        for field in radar_fields['laser']:
            if field in df.columns:
                value = str(df[field].iloc[0])
                if value and value != 'nan' and value != '-':
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        radar_counts['L'] = int(numbers[0])
                    break
        
        # 格式化输出
        if any(radar_counts.values()):
            return f"{radar_counts['U']}U+{radar_counts['M']}M+{radar_counts['L']}L"
        else:
            return 'unknown'
    
    def process_excel_file(self, file_path, brand):
        """处理单个Excel文件"""
        try:
            df_raw = pd.read_excel(file_path, header=None)
            df_raw = df_raw.set_index(0)
            
            results = []
            for col_idx in df_raw.columns:
                try:
                    series = file_path.stem.replace(f"{brand}_", "").replace("_配置", "")
                    
                    if '车型名称' not in df_raw.index:
                        continue
                    
                    model = df_raw.loc['车型名称', col_idx]
                    if pd.isna(model):
                        continue
                    
                    model = str(model).strip()
                    if not model or model == 'nan' or model == 'unknown':
                        continue
                    
                    vehicle_id = self.generate_id(brand, series, model)
                    
                    vehicle_data = {
                        'ID': vehicle_id,
                        '厂商': brand,
                        '系列': series,
                        '车型': model,
                        '级别': self.get_value_from_df(df_raw, '级别', col_idx),
                        '长*宽*高(mm)': self.get_value_from_df(df_raw, '长*宽*高(mm)', col_idx),
                        '轴距(mm)': self.get_value_from_df(df_raw, '轴距(mm)', col_idx),
                        '厂商指导价(元)': self.get_value_from_df(df_raw, '厂商指导价(元)', col_idx),
                        '座位数': self.get_value_from_df(df_raw, '座位数', col_idx),
                        '官方0-100km/h加速(s)': self.get_value_from_df(df_raw, '官方0-100km/h加速(s)', col_idx),
                        '电池能量(kWh)': self.get_value_from_df(df_raw, '电池能量(kWh)', col_idx),
                        'CLTC纯电续航里程(km)': self.get_value_from_df(df_raw, 'CLTC纯电续航里程(km)', col_idx),
                        '电池类型': self.get_value_from_df(df_raw, '电池类型', col_idx),
                        '前悬架类型': self.get_value_from_df(df_raw, '前悬架类型', col_idx),
                        '后悬架类型': self.get_value_from_df(df_raw, '后悬架类型', col_idx),
                        '座舱芯片': self.get_value_from_df(df_raw, '座舱芯片', col_idx),
                        '智驾芯片': self.get_value_from_df(df_raw, '智驾芯片', col_idx),
                        '中控屏幕尺寸': self.get_value_from_df(df_raw, '中控屏幕尺寸', col_idx),
                        '激光雷达数量': self.get_value_from_df(df_raw, '激光雷达数量', col_idx),
                        '雷达数量': self.parse_radar_from_df(df_raw, col_idx),
                        '车机智能芯片': self.get_value_from_df(df_raw, '车机智能芯片', col_idx),
                        '车载智能系统': self.get_value_from_df(df_raw, '车载智能系统', col_idx),
                        '辅助驾驶芯片': self.get_value_from_df(df_raw, '辅助驾驶芯片', col_idx),
                        '辅助驾驶系统': self.get_value_from_df(df_raw, '辅助驾驶系统', col_idx),
                    }
                    
                    results.append(vehicle_data)
                    
                except Exception as e:
                    print(Fore.YELLOW + f"    列{col_idx}处理失败: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(Fore.RED + f"处理文件失败 {file_path.name}: {str(e)}")
            return None
    
    def get_value_from_df(self, df, field_name, col_idx):
        """从DataFrame中获取指定列的字段值"""
        possible_names = self.field_mapping.get(field_name, [field_name])
        
        for name in possible_names:
            if name in df.index:
                value = df.loc[name, col_idx]
                
                if isinstance(value, pd.Series):
                    for v in value:
                        if not pd.isna(v) and str(v).strip() not in ['-', '', 'nan', '暂无数据']:
                            clean_value = str(v).strip().replace('●', '').strip()
                            return clean_value if clean_value else 'unknown'
                    continue
                
                elif isinstance(value, pd.DataFrame):
                    for idx in range(len(value)):
                        v = value.iloc[idx, 0] if value.shape[1] > 0 else None
                        if not pd.isna(v) and str(v).strip() not in ['-', '', 'nan', '暂无数据']:
                            clean_value = str(v).strip().replace('●', '').strip()
                            return clean_value if clean_value else 'unknown'
                    continue
                
                if pd.isna(value) or str(value).strip() in ['-', '', 'nan', '暂无数据']:
                    continue
                clean_value = str(value).strip().replace('●', '').strip()
                return clean_value if clean_value else 'unknown'
        
        return 'unknown'
    
    def parse_radar_from_df(self, df, col_idx):
        """从DataFrame中解析指定列的雷达信息"""
        radar_fields = {
            'ultrasonic': ['超声波雷达数量', '超声波雷达', '倒车雷达'],
            'millimeter': ['毫米波雷达数量', '毫米波雷达'],
            'laser': ['激光雷达数量', '激光雷达']
        }
        
        radar_counts = {'U': 0, 'M': 0, 'L': 0}
        import re
        
        for field in radar_fields['ultrasonic']:
            if field in df.index:
                value = df.loc[field, col_idx]
                if isinstance(value, pd.Series):
                    value = value.iloc[0] if len(value) > 0 else None
                
                value_str = str(value).replace('●', '').strip() if not pd.isna(value) else ''
                if value_str and value_str != 'nan' and value_str != '-':
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        radar_counts['U'] = int(numbers[0])
                    break
        
        for field in radar_fields['millimeter']:
            if field in df.index:
                value = df.loc[field, col_idx]
                if isinstance(value, pd.Series):
                    value = value.iloc[0] if len(value) > 0 else None
                
                value_str = str(value).replace('●', '').strip() if not pd.isna(value) else ''
                if value_str and value_str != 'nan' and value_str != '-':
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        radar_counts['M'] = int(numbers[0])
                    break
        
        for field in radar_fields['laser']:
            if field in df.index:
                value = df.loc[field, col_idx]
                if isinstance(value, pd.Series):
                    value = value.iloc[0] if len(value) > 0 else None
                
                value_str = str(value).replace('●', '').strip() if not pd.isna(value) else ''
                if value_str and value_str != 'nan' and value_str != '-':
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        radar_counts['L'] = int(numbers[0])
                    break
        
        if any(radar_counts.values()):
            return f"{radar_counts['U']}U+{radar_counts['M']}M+{radar_counts['L']}L"
        else:
            return 'unknown'
    
    def run(self):
        """运行处理流程"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "开始处理参数配置数据")
        print(Fore.CYAN + "=" * 70)
        
        all_vehicles = []
        total_files = 0
        success_count = 0
        fail_count = 0
        
        for brand_folder in self.raw_folder.iterdir():
            if not brand_folder.is_dir():
                continue
            
            brand_name = brand_folder.name
            print(Fore.GREEN + f"\n处理品牌: {brand_name}")
            
            excel_files = list(brand_folder.glob("*.xlsx")) + list(brand_folder.glob("*.xls"))
            
            for excel_file in excel_files:
                total_files += 1
                print(Fore.WHITE + f"  处理文件: {excel_file.name}")
                
                vehicles_data = self.process_excel_file(excel_file, brand_name)
                
                if vehicles_data:
                    all_vehicles.extend(vehicles_data)
                    success_count += 1
                    vehicle_names = [v['车型'] for v in vehicles_data]
                    print(Fore.GREEN + f"    成功: 提取 {len(vehicles_data)} 个车型 - {', '.join(vehicle_names[:3])}{' ...' if len(vehicles_data) > 3 else ''}")
                else:
                    fail_count += 1
                    print(Fore.RED + f"    失败")
        
        output_file_cn = self.output_folder / "vehicles_config_cn.json"
        output_file_en = self.output_folder / "vehicles_config.json"
        
        with open(output_file_cn, 'w', encoding='utf-8') as f:
            json.dump(all_vehicles, f, ensure_ascii=False, indent=2)
        
        standardized_vehicles = [self.standardize_vehicle_data(v) for v in all_vehicles]
        
        with open(output_file_en, 'w', encoding='utf-8') as f:
            json.dump(standardized_vehicles, f, ensure_ascii=False, indent=2)
        
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.GREEN + f"处理完成!")
        print(Fore.CYAN + f"总文件数: {total_files}")
        print(Fore.GREEN + f"成功: {success_count}")
        print(Fore.RED + f"失败: {fail_count}")
        print(Fore.CYAN + f"输出文件 (中文版): {output_file_cn}")
        print(Fore.CYAN + f"输出文件 (标准版): {output_file_en}")
        print(Fore.CYAN + f"{'=' * 70}")
        
        if all_vehicles:
            print(Fore.YELLOW + f"\n数据统计:")
            print(Fore.WHITE + f"  总车型数: {len(all_vehicles)}")
            
            brand_count = {}
            for vehicle in all_vehicles:
                brand = vehicle['厂商']
                brand_count[brand] = brand_count.get(brand, 0) + 1
            
            print(Fore.WHITE + f"\n  各品牌车型数:")
            for brand, count in sorted(brand_count.items(), key=lambda x: x[1], reverse=True):
                print(Fore.WHITE + f"    {brand}: {count} 个车型")
            
            print(Fore.YELLOW + f"\n示例数据 (第1个车型) - 中文版:")
            for key, value in all_vehicles[0].items():
                print(Fore.WHITE + f"  {key}: {value}")
            
            print(Fore.YELLOW + f"\n示例数据 (第1个车型) - 标准版 (嵌套结构):")
            import json as json_module
            print(Fore.WHITE + json_module.dumps(standardized_vehicles[0], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    processor = ParaProcessor()
    processor.run()
