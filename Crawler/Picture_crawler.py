import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
from colorama import Fore, init
import re
import requests
import json
import os

# 初始化colorama
init(autoreset=True)


class PictureCrawler:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "config", "car_models.json")
        self.pic_raw_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Raw","Pic Raw")
        self.car_models = self.load_config()
        
        # 图片分类映射 (URL中的数字 -> 中文名称)
        self.category_map = {
            '1': '车身外观',
            '10': '中控方向盘',
            '3': '车厢座椅',
            '12': '其它细节'
        }
    
    def load_config(self):
        """加载car_models.json配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(Fore.RED + f"加载配置文件失败: {str(e)}")
            return {}
    
    def run(self, brands=None, models=None):
        """
        运行爬虫
        :param brands: 要抓取的品牌列表，None表示抓取所有品牌
        :param models: 字典，指定每个品牌要抓取的车型，格式 {'品牌': ['车型1', '车型2']}
        """
        if brands is None:
            brands = list(self.car_models.keys())
        
        print(Fore.CYAN + f"=" * 60)
        print(Fore.CYAN + f"开始下载图片，共 {len(brands)} 个品牌")
        print(Fore.CYAN + f"=" * 60)
        
        for brand in brands:
            if brand not in self.car_models:
                print(Fore.YELLOW + f"警告: 品牌 '{brand}' 不在配置文件中，跳过")
                continue
            
            brand_models = self.car_models[brand]
            
            # 如果指定了特定车型，则只抓取指定的车型
            if models and brand in models:
                target_models = {k: v for k, v in brand_models.items() if k in models[brand]}
            else:
                target_models = brand_models
            
            if not target_models:
                print(Fore.YELLOW + f"品牌 '{brand}' 没有要下载的车型，跳过")
                continue
            
            print(Fore.GREEN + f"\n{'=' * 60}")
            print(Fore.GREEN + f"品牌: {brand}，共 {len(target_models)} 个车型")
            print(Fore.GREEN + f"{'=' * 60}")
            
            for idx, (model_name, series_id) in enumerate(target_models.items(), 1):
                print(Fore.YELLOW + f"\n[{idx}/{len(target_models)}] 正在下载: {brand} - {model_name} (ID: {series_id})")
                try:
                    self.download_model_images(brand, model_name, series_id)
                except Exception as e:
                    print(Fore.RED + f"下载失败: {str(e)}")
                    continue
        
        print(Fore.CYAN + f"\n{'=' * 60}")
        print(Fore.CYAN + "所有下载任务完成！")
        print(Fore.CYAN + f"{'=' * 60}")
    
    def download_model_images(self, brand, model_name, series_id):
        """下载指定车型的所有图片"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.autohome.com.cn/cars/"
        }
        
        # 访问基础URL获取图片页面链接
        base_url = f"https://car.autohome.com.cn/pic/series/{series_id}.html"
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(Fore.RED + f"  页面访问失败，状态码: {response.status_code}")
                return
            
            # 解析页面获取各分类的图片链接
            all_images = self.parse_main_page(response.text, series_id)
            
            if not all_images:
                print(Fore.YELLOW + "  未找到图片")
                return
            
            # 创建保存目录
            folder_path = os.path.join(self.pic_raw_folder, brand, model_name)
            os.makedirs(folder_path, exist_ok=True)
            print(Fore.CYAN + f"  保存路径: {folder_path}")
            
            # 下载所有分类的图片
            total_success = 0
            total_skip = 0
            total_fail = 0
            
            for category, images in all_images.items():
                print(Fore.CYAN + f"\n  正在下载: {category} (共 {len(images)} 张)")
                success, skip, fail = self.download_category_images(images, folder_path, category)
                total_success += success
                total_skip += skip
                total_fail += fail
            
            print(Fore.GREEN + f"\n  总计 - 成功:{total_success}, 跳过:{total_skip}, 失败:{total_fail}")
            
        except Exception as e:
            print(Fore.RED + f"  错误: {str(e)}")
    
    def parse_main_page(self, html_content, series_id):
        """解析主页面获取各分类的图片链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        all_images = {}
        
        # 尝试按分类链接提取图片
        for category_id, category_name in self.category_map.items():
            # 查找该分类的链接
            category_url = f"https://car.autohome.com.cn/pic/series/{series_id}-{category_id}.html"
            
            try:
                headers = {
                    "User-Agent": UserAgent().random,
                    "Referer": "https://www.autohome.com.cn/cars/"
                }
                response = requests.get(category_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # 匹配格式: //car2.autoimg.cn/cardfs/product/g31/M08/EA/81/480x360_0_q95_c42_autohomecar__ChtlyGet8LWAbBPDACaN7q7J4Es934.jpg
                    # 需要提取为: cardfs/product/g31/M08/EA/81/ChxpVml62RuAQGEvAB2TGuXSfcA358.jpg (去掉尺寸质量参数)
                    
                    # 方法1: 提取完整路径再清洗
                    pattern = re.compile(r'//car\d+\.autoimg\.cn/cardfs/product/([^"]+?)\.jpg')
                    matches = pattern.findall(response.text)
                    
                    # 清洗图片路径: 去掉 480x360_0_q95_c42_autohomecar__ 这样的前缀
                    cleaned_images = []
                    for match in matches:
                        # 分离路径部分和文件名部分
                        # 例如: g31/M08/EA/81/480x360_0_q95_c42_autohomecar__ChtlyGet8LWAbBPDACaN7q7J4Es934
                        parts = match.split('/')
                        if len(parts) >= 5:
                            # 获取目录部分: g31/M08/EA/81
                            path_parts = parts[:4]
                            # 获取文件名部分并清理
                            filename = parts[-1]
                            # 去掉尺寸和质量参数 (格式: 480x360_0_q95_c42_autohomecar__)
                            cleaned_filename = re.sub(r'^\d+x\d+_\d+_q\d+_c\d+_autohomecar__', '', filename)
                            
                            # 重组完整路径
                            clean_path = '/'.join(path_parts) + '/' + cleaned_filename
                            cleaned_images.append(clean_path)
                    
                    # 去重并限制为8张
                    unique_images = list(dict.fromkeys(cleaned_images))[:8]
                    
                    if unique_images:
                        all_images[category_name] = unique_images
                        print(Fore.WHITE + f"  {category_name}: 找到 {len(unique_images)} 张图片")
                    
                    time.sleep(random.uniform(1, 2))
            
            except Exception as e:
                print(Fore.YELLOW + f"  {category_name} 解析失败: {str(e)}")
                continue
        
        return all_images
    
    def download_category_images(self, image_paths, folder_path, category):
        """下载某个分类的图片"""
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        # 创建分类文件夹
        category_folder = os.path.join(folder_path, category)
        os.makedirs(category_folder, exist_ok=True)
        
        for idx, img_path in enumerate(image_paths, 1):
            # 构造原图URL
            # img_path 格式: g31/M08/EA/81/ChtlyGet8LWAbBPDACaN7q7J4Es934
            # 需要构造: https://car2.autoimg.cn/cardfs/product/g31/M08/EA/81/ChtlyGet8LWAbBPDACaN7q7J4Es934.jpg
            img_url = f"https://car2.autoimg.cn/cardfs/product/{img_path}.jpg"
            
            # 生成文件名: 分类_序号.jpg
            filename = f"{category}_{idx:02d}.jpg"
            file_path = os.path.join(category_folder, filename)
            
            # 检查是否已存在
            if os.path.exists(file_path):
                skip_count += 1
                continue
            
            # 下载图片
            try:
                headers = {"User-Agent": UserAgent().random}
                response = requests.get(img_url, headers=headers, stream=True, timeout=10)
                
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    success_count += 1
                    print(Fore.WHITE + f"    [{idx}/{len(image_paths)}] 下载成功: {filename}")
                else:
                    fail_count += 1
                    print(Fore.RED + f"    [{idx}/{len(image_paths)}] 下载失败: {filename} (状态码:{response.status_code})")
                
                time.sleep(random.uniform(0.5, 1.5))
            
            except Exception as e:
                fail_count += 1
                print(Fore.RED + f"    [{idx}/{len(image_paths)}] 下载失败: {filename} ({str(e)})")
        
        return success_count, skip_count, fail_count


if __name__ == '__main__':
    crawler = PictureCrawler()
    
    # 示例1: 抓取所有厂商的所有车型
    # crawler.run()
    
    # 示例2: 只抓取指定厂商
    # crawler.run(brands=['比亚迪', '问界'])
    
    # 示例3: 只抓取指定厂商的指定车型
    # crawler.run(
    #     brands=['比亚迪'],
    #     models={
    #         '比亚迪': ['唐_新能源', '元PLUS']  
    #     }
    # )
    
    # 默认执行: 抓取比亚迪品牌的所有车型
    crawler.run(brands=['奥迪'])