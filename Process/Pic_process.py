#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片索引生成脚本 - 简化版
按车系分组：品牌_车系 -> {exterior: [], interior: [], detail: []}
"""

import json
from pathlib import Path
from colorama import init, Fore

init(autoreset=True)


class ImageMapGenerator:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.pic_folder = self.base_path / "Data" / "Raw" / "Pic Raw"
        self.processed_dir = self.base_path / "Data" / "Processed"
        
        # 图片分类映射
        self.category_map = {
            '车身外观': 'exterior',
            '中控方向盘': 'interior',
            '车厢座椅': 'interior',  # 合并到 interior
            '其它细节': 'detail'
        }
    
    def scan_images(self):
        """扫描所有图片文件"""
        image_map = {}
        stats = {
            'total_series': 0,
            'total_images': 0,
            'by_category': {'exterior': 0, 'interior': 0, 'detail': 0},
            'by_brand': {}
        }
        
        # 遍历品牌文件夹
        for brand_folder in sorted(self.pic_folder.iterdir()):
            if not brand_folder.is_dir():
                continue
            
            brand_name = brand_folder.name
            stats['by_brand'][brand_name] = 0
            
            print(Fore.GREEN + f"\n处理品牌: {brand_name}")
            
            # 遍历系列文件夹
            for series_folder in sorted(brand_folder.iterdir()):
                if not series_folder.is_dir():
                    continue
                
                series_name = series_folder.name
                series_key = f"{brand_name}_{series_name}"
                
                # 初始化该车系的图片列表
                image_map[series_key] = {
                    'exterior': [],
                    'interior': [],
                    'detail': []
                }
                
                series_img_count = 0
                
                # 遍历分类文件夹
                for category_folder in series_folder.iterdir():
                    if not category_folder.is_dir():
                        continue
                    
                    category_cn = category_folder.name
                    category_en = self.category_map.get(category_cn, 'detail')
                    
                    # 扫描图片文件
                    for img_file in sorted(category_folder.glob('*.jpg')):
                        relative_path = str(img_file.relative_to(self.base_path)).replace('\\', '/')
                        image_map[series_key][category_en].append(relative_path)
                        
                        stats['total_images'] += 1
                        stats['by_category'][category_en] += 1
                        stats['by_brand'][brand_name] += 1
                        series_img_count += 1
                
                if series_img_count > 0:
                    stats['total_series'] += 1
                    print(Fore.WHITE + f"  ✓ {series_key}: {series_img_count}张图片")
                else:
                    # 删除空的车系
                    del image_map[series_key]
        
        return image_map, stats
    
    def save_image_map(self, image_map):
        """保存图片索引"""
        output_file = self.processed_dir / "image_map.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(image_map, f, ensure_ascii=False, indent=2)
        return output_file
    
    def print_statistics(self, stats, output_file):
        """打印统计信息"""
        print(Fore.CYAN + f"\n{'=' * 70}")
        print(Fore.GREEN + "图片索引生成完成!")
        print(Fore.CYAN + f"{'=' * 70}")
        
        print(Fore.YELLOW + f"\n统计信息:")
        print(Fore.WHITE + f"  品牌数: {len(stats['by_brand'])}")
        print(Fore.WHITE + f"  系列数: {stats['total_series']}")
        print(Fore.WHITE + f"  总图片数: {stats['total_images']}")
        
        print(Fore.YELLOW + f"\n按分类统计:")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            print(Fore.WHITE + f"  {category}: {count}张")
        
        print(Fore.YELLOW + f"\n各品牌图片数:")
        for brand, count in sorted(stats['by_brand'].items(), key=lambda x: x[1], reverse=True):
            print(Fore.WHITE + f"  {brand}: {count}张")
        
        print(Fore.CYAN + f"\n输出文件: {output_file}")
        print(Fore.GREEN + f"文件大小: {output_file.stat().st_size / 1024:.1f} KB")
        print(Fore.CYAN + f"{'=' * 70}")
    
    def print_sample(self, image_map):
        """打印示例数据"""
        if not image_map:
            return
        
        sample_key = list(image_map.keys())[0]
        sample_data = image_map[sample_key]
        
        print(Fore.YELLOW + f"\n示例数据:")
        print(Fore.WHITE + f"  车系: {sample_key}")
        for category, paths in sample_data.items():
            if paths:
                print(Fore.WHITE + f"  {category}: {len(paths)}张")
                print(Fore.WHITE + f"    - {paths[0]}")
                if len(paths) > 1:
                    print(Fore.WHITE + f"    - {paths[1]}")
    
    def generate(self):
        """生成图片索引"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "开始扫描图片文件 (简化版)")
        print(Fore.CYAN + "=" * 70)
        
        # 扫描图片
        image_map, stats = self.scan_images()
        
        # 保存结果
        output_file = self.save_image_map(image_map)
        
        # 打印统计
        self.print_statistics(stats, output_file)
        
        # 打印示例
        self.print_sample(image_map)


def main():
    generator = ImageMapGenerator()
    generator.generate()


if __name__ == '__main__':
    main()
