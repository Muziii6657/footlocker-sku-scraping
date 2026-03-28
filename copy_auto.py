import time
import random
import csv
from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.action_chains import ActionChains #模拟人的鼠标 / 键盘动作
from selenium.webdriver.common.by import By  #指定用什么方式查找元素
from selenium.webdriver.support.ui import WebDriverWait   #智能等待页面加载完成
from selenium.webdriver.support import expected_conditions as EC  #等待 “某个条件满足”
from selenium.common.exceptions import TimeoutException #等待超时异常

#使用爬虫添加隐藏二级菜单中各个板块的链接
#列表用于存放链接
category_urls = []

# 排除没有下拉菜单的项,避免占位浪费时间
EXCLUDE = {"Releases", "FLX Rewards", ""}

#代理端口
proxy = "127.0.0.1:7897"  

#获取分类链接的函数，传入浏览器对象，返回分类链接列表
#获取分类链接的函数，传入浏览器对象，返回分类链接列表
def get_category_urls_by_hover(driver):
    driver.get("https://www.footlocker.com/")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Main']"))
    )

    temp_urls = set()

    # 只定位中间主导航栏的导航项，排除右上角功能按钮
    nav_items = driver.find_elements(By.XPATH, "//nav[@aria-label='Main']//li[contains(@class, 'headerNavigationItem')]")

    # 遍历每个导航，悬停
    for item in nav_items:
        text = item.text.strip()
        if text in EXCLUDE:  #排除字段不再等待
            continue

        print(f"正在悬停：{text}")
        ActionChains(driver).move_to_element(item).pause(1).perform()
        time.sleep(1.5)

        # 提取所有下拉里的链接,使用xpath匹配所有包含dropdown的下拉菜单容器，兼容不同模块的 class
        links = driver.find_elements(By.XPATH, "//div[contains(@class,'NavigationMenu--viewport')]//a[@href]")
        for link in links:
            href = link.get_attribute("href")
            #排除商品链接
            if href and "footlocker.com" in href and "/product/" not in href:
                temp_urls.add(href)

    # 存入全局列表
    global category_urls
    category_urls = list(temp_urls)
    print(f"已获取 {len(category_urls)} 个分类链接")


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
def save_csv(data, filename="footlocker_all_skus.csv"):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "name", "price", "url"])
        writer.writeheader()       #写入表头
        writer.writerows(data)     #写入数据行


# 主函数
def main():
    #启动浏览器（配置好代理+请求头）
    driver = create_driver(proxy)
    #获取链接
    get_category_urls_by_hover(driver)

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
    print("文件已保存为: footlocker_all_skus.csv")


if __name__ == "__main__":
    main()