"""
汽车之家UGC口碑爬虫 
功能:
1. 按厂商分类保存CSV文件
2. 从外部JSON配置文件读取车型ID
3. 智能验证车型ID匹配
4. 自动创建输出目录
"""

import json
import os
import csv
import time
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class CarReviewCrawler:
    
    # 评论分类
    COMMENT_CATEGORIES = ['空间', '驾驶感受', '续航', '外观', '内饰', '价格政策', '性价比', '智能化']
    
    def __init__(self, config_path='config/car_models.json', output_dir='../Data/Raw'):
        """
        初始化爬虫
        
        Args:
            config_path: 车型配置文件路径(相对于当前脚本)
            output_dir: 输出目录路径(相对于当前脚本)
        """
        self.script_dir = Path(__file__).parent
        self.config_path = self.script_dir / config_path
        self.output_dir = self.script_dir / output_dir
        
        # 加载配置
        self.car_models = self._load_config()
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.total_count = 0
        
    def _load_config(self):
        """加载车型配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 配置文件未找到 {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误 {e}")
            raise
    
    def _get_csv_filename(self, brand):
        """获取厂商对应的CSV文件名"""
        return self.output_dir / f"{brand}_口碑数据.csv"
    
    def scrape_review_detail(self, review_url, shopping_targets, model_name):
        """
        抓取单篇口碑详情页的数据
        
        Args:
            review_url: 口碑详情页URL
            shopping_targets: 对比车型列表
            model_name: 车型名称
            
        Returns:
            dict: 提取的口碑数据,失败返回None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(review_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 验证详情页
            title_div = soup.find('div', class_='subnav-title-name')
            if not title_div:
                return None
            
            title = title_div.text.strip()
            
            # 初始化数据字典
            car_data = {
                '抓取车型': model_name,
                '实际型号': title
            }
            
            # 1. 提取基本信息
            kb_con = soup.find('div', class_='kb-con')
            if kb_con:
                ul_items = kb_con.find('ul').find_all('li')
                basic_info = {
                    '行驶里程': None,
                    '春秋电耗': None,
                    '春秋续航': None,
                    '夏季电耗': None,
                    '夏季续航': None,
                    '冬季电耗': None,
                    '冬季续航': None,
                    '裸车购买价': None,
                    '购买时间': None,
                    '购买地点': None
                }
                
                for li_item in ul_items:
                    try:
                        header = li_item.find('div', class_='name').text.strip()
                        value = li_item.find('div', class_='key').text.strip()
                        if header in basic_info:
                            basic_info[header] = value
                    except AttributeError:
                        continue
                
                car_data.update(basic_info)
            
            # 2. 提取发布时间
            timeline = soup.find('div', class_='timeline-con')
            if timeline:
                comment_time = timeline.find('span').text.strip().split(' ')[0]
                car_data['评论发布时间'] = comment_time
            else:
                car_data['评论发布时间'] = '未知'
            
            # 3. 初始化评分字段
            for category in self.COMMENT_CATEGORIES:
                car_data[f'{category}评分评价'] = '暂无'
                car_data[f'{category}评分'] = '暂无'
            
            # 4. 提取评分和评价
            ratings = soup.find_all('div', class_='space kb-item')
            
            count = 0
            for rating in ratings:
                count += 1
                
                # 前两个是"最满意"和"最不满意"
                if count < 3:
                    review_text = rating.find('p', class_='kb-item-msg').text.strip()
                    key = '最满意' if count == 1 else '最不满意'
                    car_data[key] = review_text
                    continue
                
                # 后续是各个分类评分
                h1_tag = rating.find('h1')
                if not h1_tag:
                    continue
                
                cat_raw = h1_tag.text.strip().split()
                if not cat_raw or cat_raw[0] not in self.COMMENT_CATEGORIES:
                    continue
                
                cat_name = cat_raw[0]
                
                # 提取星级
                stars_span = rating.find('span', class_='star-num')
                stars = stars_span.text.strip() if stars_span else '0'
                car_data[f'{cat_name}评分'] = stars
                
                # 提取评价文本
                msg_p = rating.find('p', class_='kb-item-msg')
                review_text = msg_p.text.strip() if msg_p else ''
                car_data[f'{cat_name}评分评价'] = review_text
            
            # 5. 添加对比车型
            car_data['购物目标'] = shopping_targets
            
            return car_data
        
        except Exception as e:
            # print(f"详情页抓取异常: {e}")
            return None
    
    def save_to_csv(self, data, csv_file):
        """
        保存数据到CSV文件
        
        Args:
            data: 数据字典
            csv_file: CSV文件路径
        """
        if not data:
            return
        
        # 检查文件是否存在
        file_exists = csv_file.exists()
        
        with open(csv_file, mode='a', newline='', encoding='utf-8-sig') as f:
            fieldnames = list(data.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 如果是新文件,写入表头
            if not file_exists:
                writer.writeheader()
            
            # 处理列表类型的字段
            if isinstance(data.get('购物目标'), list):
                data['购物目标'] = ', '.join(data['购物目标'])
            
            writer.writerow(data)
    
    def verify_page_title(self, driver, model_name):
        """
        验证页面标题是否匹配车型
        
        Args:
            driver: Selenium WebDriver
            model_name: 车型名称
            
        Returns:
            bool: 是否匹配
        """
        current_title = driver.title
        print(f"当前网页标题: [{current_title}]")
        
        # 提取车名关键字(取下划线前的部分,再取前2个字)
        check_key = model_name.split('_')[0][:2]
        
        # 检查标题是否包含关键字
        if check_key not in current_title and "口碑" not in current_title:
            print(f"错误: 打开的是【{current_title}】,不是【{model_name}】")
            return False
        
        return True
    
    def handle_captcha(self, driver):
        """
        处理验证码
        
        Args:
            driver: Selenium WebDriver
            
        Returns:
            bool: 是否成功通过验证码
        """
        print("检测到验证码! 请在 20秒 内手动滑动验证!")
        time.sleep(20)
        
        try:
            wait = WebDriverWait(driver, 5)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'list_jump__ieH_F')))
            print("验证成功,继续抓取...")
            return True
        except TimeoutException:
            print("验证失败,跳过该车型")
            return False
    
    def scrape_model(self, brand, model_name, model_id, max_pages=200):
        """
        抓取单个车型的口碑数据
        
        Args:
            brand: 厂商名称
            model_name: 车型名称
            model_id: 车型ID
            max_pages: 最大抓取页数
        """
        print(f"\n{'='*50}")
        print(f"开始抓取: {brand} - {model_name} (ID: {model_id})")
        print(f"{'='*50}")
        
        driver = webdriver.Chrome()
        base_url = f'https://k.autohome.com.cn/{model_id}'
        csv_file = self._get_csv_filename(brand)
        
        model_count = 0
        
        try:
            # 打开首页
            driver.get(base_url)
            time.sleep(3)
            
            # 验证页面标题
            if not self.verify_page_title(driver, model_name):
                print(f"自动跳过该车型")
                return
            
            # 开始翻页抓取
            for page in range(1, max_pages + 1):
                page_url = f'{base_url}/index_{page}.html#listcontainer'
                print(f"进度: {model_name} - 第 {page} 页")
                
                try:
                    driver.get(page_url)
                    wait = WebDriverWait(driver, 5)
                    
                    try:
                        # 等待列表加载
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'list_jump__ieH_F')))
                    except TimeoutException:
                        print(f"列表加载超时")
                        
                        # 首页加载失败可能是验证码
                        if page == 1:
                            if not self.handle_captcha(driver):
                                break
                        else:
                            break
                    
                    # 解析页面
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    review_elements = soup.find_all('li', class_='clearfix')
                    
                    if not review_elements:
                        print("未找到口碑列表,可能已到最后一页")
                        break
                    
                    page_count = 0
                    for review_element in review_elements:
                        # 提取口碑详情链接
                        link_div = review_element.find('li', class_='list_jump__ieH_F')
                        if not link_div:
                            continue
                        
                        review_url = link_div.find('a')['href']
                        if not review_url.startswith('http'):
                            review_url = 'https:' + review_url
                        
                        # 提取对比车型
                        targets = [li.text for li in review_element.find_all('li', class_='list_target__76fWs')]
                        
                        # 抓取详情
                        car_data = self.scrape_review_detail(review_url, targets, model_name)
                        
                        if car_data:
                            self.save_to_csv(car_data, csv_file)
                            model_count += 1
                            self.total_count += 1
                            page_count += 1
                            print(f"  ✓ {car_data.get('实际型号')} | {car_data.get('评论发布时间')}")
                        
                        # 随机延迟,避免被封
                        time.sleep(random.uniform(0.5, 1.0))
                    
                    print(f"--- 本页抓取 {page_count} 条 ---")
                    time.sleep(random.uniform(1.5, 3.0))
                
                except Exception as e:
                    print(f"页面异常: {e}")
                    continue
        
        except Exception as e:
            print(f"车型抓取异常: {e}")
        
        finally:
            driver.quit()
            print(f"{model_name} 完成! 共抓取 {model_count} 条")
            print(f"休息 5 秒...")
            time.sleep(5)
    
    def run(self, brands=None, models=None):
        """
        运行爬虫
        
        Args:
            brands: 要抓取的厂商列表,None表示全部
            models: 要抓取的车型列表(格式: {"厂商": ["车型1", "车型2"]}),None表示全部
        """
        print(f"\n{'#'*60}")
        print(f"# 汽车之家UGC口碑爬虫启动")
        print(f"# 配置文件: {self.config_path}")
        print(f"# 输出目录: {self.output_dir}")
        print(f"{'#'*60}\n")
        
        # 筛选要抓取的厂商
        if brands:
            selected_brands = {k: v for k, v in self.car_models.items() if k in brands}
        else:
            selected_brands = self.car_models
        
        # 遍历厂商
        for brand, models_dict in selected_brands.items():
            print(f"\n{'='*60}")
            print(f"开始处理厂商: {brand}")
            print(f"车型数量: {len(models_dict)}")
            print(f"输出文件: {self._get_csv_filename(brand)}")
            print(f"{'='*60}")
            
            # 筛选要抓取的车型
            if models and brand in models:
                selected_models = {k: v for k, v in models_dict.items() if k in models[brand]}
            else:
                selected_models = models_dict
            
            # 遍历车型
            for model_name, model_id in selected_models.items():
                self.scrape_model(brand, model_name, model_id)
        
        print(f"\n{'#'*60}")
        print(f"# 所有任务完成!")
        print(f"# 总计抓取: {self.total_count} 条口碑")
        print(f"{'#'*60}\n")


def main():
    """主函数 - 可以在这里配置要抓取的厂商和车型"""
    
    crawler = CarReviewCrawler()
    
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
        crawler.run(
        brands=['比亚迪']
    )


if __name__ == "__main__":
    main()
