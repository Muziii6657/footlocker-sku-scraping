import time
import random
import csv
from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

#手动添加先试验是否能成功访问目标网站
category_urls = [
    "https://www.footlocker.com/",
    "https://www.footlocker.com/en/category/shoes/hoka/bondi",
    "https://www.footlocker.com/category/sport/performance-running?query=performancerunning%3Arelevance%3Agender%3AMen%27s",
    "https://www.footlocker.com/category/collection/low-profile.html?query=lowprofile%3Arelevance%3Agender%3AWomen%27s"
]


#代理端口(科学上网)
proxy = "127.0.0.1:xxxx"  #请替换为你自己的代理端口

#创建浏览器对象
def create_driver(proxy):
     #创建谷歌配置对象
     options = wd.ChromeOptions() # type: ignore
     #给配置对象设置代理
     options.add_argument(f'--proxy-server={proxy}')
     #配置请求头（伪装）
     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
     options.add_argument(f"user-agent={user_agent}")

     #创建浏览器对象
     driver = wd.Chrome(service=Service(ChromeDriverManager().install()), options=options) # type: ignore

     return driver

#滚动加载页面所有内容
def scroll_load(driver):
    #浏览器执行JS，并获取当前页面高度保存为当前高度
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(5):  # 滚动5次，加载足够多商品
        #让浏览器滚到最底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #等待网页刷新商品
        time.sleep(random.uniform(2, 4))
        #获取新高度（可能因为滚动加载变高
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height: #如果高度没变，说明加载到底
            break
        last_height = new_height

# 从页面提取SKU数据，单个页面！
def extract_products(html):
    #创建BS对象，解析HTML
    soup = BeautifulSoup(html, "html.parser")
    #找到网页中所有带链接的 a 标签，存储在列表中
    products = soup.find_all("a", href=True)

    result = [] #存放数据
    for a in products:
        #过滤出商品链接，要求包含 /product/ 且以 .html 结尾
        href = str(a["href"]) # type: ignore
        if "/product/" in href and href.endswith(".html"):
            #提取sku
            try:
                #把链接按 / 切开，取最后一部分，去掉 .html，获取SKU
                sku = href.split("/")[-1].replace(".html", "")

                #商品名称，用类名查找
                name_elem = a.find("span", class_="ProductName-primary") # type: ignore
                name = name_elem.text.strip() if name_elem else "Name Not Found"

                #价格
                price_elem = a.find("div", class_="ProductPrice") # type: ignore
                price = price_elem.text.strip() if price_elem else "Price Not Found"

                #完整链接
                full_url = f"https://www.footlocker.com{href}"
                
                #字典形式保存
                result.append({
                    "sku": sku,
                    "name": name,
                    "price": price,
                    "url": full_url
                })
            except:#如果过程中发生错误，先跳过继续下一个
                continue
    return result


# 此处传入字典列表，返回去重后的列表（之前返回的result）
def deduplicate(results):
    #创建集合，添加时去重
    seen = set()
    new_list = []
    for p in results:  
        #判断sku是否已经见过seen，如果没有见过就添加到集合和新列表中
        if p["sku"] not in seen:
            seen.add(p["sku"])   #集合只存SKU字符串
            new_list.append(p)   #列表存商品字典
    return new_list


# 保存CSV
def save_csv(data, filename="footlocker_skus.csv"):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "name", "price", "url"])
        writer.writeheader()       #写入表头
        writer.writerows(data)     #写入数据行


# 主函数
def main():
    #启动浏览器（配置好代理+请求头）
    driver = create_driver(proxy)
    #空列表存放商品,所有页面！
    all_data = []

    for url in category_urls:
        try:
            print(f"正在爬取：{url}")
            driver.get(url)
            time.sleep(random.uniform(3, 5))

            #滚动加载全部
            scroll_load(driver)

            #提取商品
            products = extract_products(driver.page_source)
            print(f"本次爬取 {len(products)} 个商品")

            #将每次爬取的商品添加到总列表中
            all_data.extend(products)

            #分类间隔延迟
            time.sleep(random.uniform(5, 8))

        except Exception as e:
            print(f"爬取失败：{url}，错误：{e}")
            continue
     #关闭浏览器
    driver.quit()

    #去重
    all_data = deduplicate(all_data)
    #保存
    save_csv(all_data)
    print(f"\n 爬取完成! 总SKU数量:{len(all_data)}")
    print("文件已保存为: footlocker_skus.csv")


if __name__ == "__main__":
    main()