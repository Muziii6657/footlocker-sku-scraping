# Footlocker SKU 爬虫

[TOC]

## 项目需求

- 尽量抓所有的sku

## 项目说明
- 本项目是一个基于 Selenium 模拟浏览器操作的 FootLocker 网站爬虫，核心实现主导航悬停获取隐藏分类链接、分类页商品爬取、数据去重与 CSV 导出功能，支持代理配置、反爬友好的延迟策略，且提供单次测试模式便于调试。

## 技术栈
- Python  3.x
- Selenium        ：模拟浏览器操作（悬停、滚动、元素定位），处理动态加载页面
- BeautifulSoup   ：解析页面 HTML，提取商品数据
- WebDriverManager：自动管理 ChromeDriver 版本，无需手动下载配置


## 开始项目

### 下载依赖

pip install selenium

pip install beautifulsoup4

pip install webdriver-manager

## 核心函数说明
- 1 create_driver(proxy) - 浏览器对象创建
功能：初始化 Chrome 浏览器对象，配置代理、自定义 User-Agent 伪装请求头

- 2 get_category_urls_by_hover(driver) - 悬停获取分类链接
功能：模拟鼠标悬停主导航项，提取下拉菜单中的分类 / 集合页链接（排除商品详情页）

- 3 is_mens_basketball_link(url, text) - 分类匹配辅助函数
功能：测试模式核心匹配逻辑

- 4 scroll_load(driver) - 页面滚动加载
功能：模拟滚动页面到底部，循环 5 次滚动，每次滚动后等待 2-4 秒，若页面高度无变化则终止（已加载到底）

- 5 extract_products(html) - 商品数据提取
功能：解析页面 HTML，提取商品 SKU、名称、价格、完整链接

- 6 deduplicate(results) - 数据去重
功能：基于 SKU 对爬取的商品数据去重（SKU 为商品唯一标识）

- 7 save_csv(data, filename) - 数据导出
功能：将去重后的商品数据（sku、name、price、url）写入 CSV 文件，编码为 UTF-8 避免乱码

- 8 main() - 主流程函数
功能：串联所有核心逻辑，完成全流程爬取


### 运行项目

- 1.代理端口填写

proxy = "127.0.0.1:xxxx"填充为自己的代理端口  

- 2.运行程序

- 当前目录终端下，python auto_scrapy.py

- 运行后请将窗口最大化打开，避免因为找不到组件而导致爬取为0
---
注：

test 为测试用例，手动添加url进行爬取sku，检查爬虫功能是否实现

![image-20260328103030229](Readme.assets/image-20260328103030229.png)

并保存至csv文件，包含信息sku，name，price，url

在test基础上，设计了copy_auto.py 初步实现爬取思路

- 使用爬虫添加隐藏二级菜单中各个板块的链接

优化悬停逻辑实现链接获取和爬取，在auto_scrapy.py中实现sku尽可能爬取

category_urls = []  列表用于存放链接



![image-20260328113007049](Readme.assets/image-20260328113007049.png)

