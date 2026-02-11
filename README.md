# EV PM DSS - 电动汽车产品管理决策支持系统

## 项目结构

```
EV PM DSS/
├── Crawler/          # 数据爬取模块
├── Process/          # 数据处理模块
├── Data/             # 数据存储目录
│   ├── Raw/         # 原始数据
│   └── Processed/   # 处理后的数据
├── venv/            # Python虚拟环境
└── requirements.txt # 项目依赖
```

## 环境配置

### 1. 创建虚拟环境（首次使用）

```powershell
# 在项目根目录下
python -m venv venv
```

### 2. 激活虚拟环境

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

## 使用说明

### 数据爬取

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行爬虫
python Crawler/Parameter_crawler.py
python Crawler/Picture_crawler.py
python Crawler/UGC_crawler.py
```

### 数据处理

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行数据处理脚本
python Process/UGC_process.py
python Process/Para_process.py
python Process/Pic_process.py
```

## 主要依赖

- **数据爬取**: requests, beautifulsoup4, selenium, lxml
- **数据处理**: pandas, openpyxl
- **工具库**: colorama, fake-useragent

## 注意事项

1. 虚拟环境文件夹 `venv/` 已添加到 `.gitignore`，不会被提交到版本控制
2. 所有Python脚本都应在激活虚拟环境后运行
3. 如需添加新依赖，请更新 `requirements.txt` 文件
