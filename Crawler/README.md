# Crawler 模块 - 数据采集

## 功能说明

负责从汽车之家平台采集电动汽车相关数据，包括车型参数、图片和用户口碑评论。

## 核心脚本

### 1. Parameter_crawler.py
- 采集车型基本参数和配置信息
- 输出：`Data/Raw/Para Raw/{品牌}/{车系}.json`

### 2. UGC_crawler.py
- 采集用户口碑评论（User Generated Content）
- 包含评分、评论文本、购车信息等
- 输出：`Data/Raw/UGC Raw/{品牌}_口碑数据.csv`

### 3. Picture_crawler.py
- 采集车型外观和内饰图片
- 输出：`Data/Raw/Pic Raw/{品牌}/`

## 配置文件

`config/car_models.json` - 定义要采集的品牌和车系列表

## 使用方法

```bash
# 采集车型参数
python Crawler/Parameter_crawler.py

# 采集用户评论
python Crawler/UGC_crawler.py

# 采集车型图片
python Crawler/Picture_crawler.py
```

## 注意事项

- 请遵守目标网站的 robots.txt 和使用条款
- 建议添加适当的请求间隔，避免给服务器造成压力
- 本模块仅供学习研究使用
