import time
import random
import csv
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.action_chains import ActionChains #模拟人的鼠标 / 键盘动作
from selenium.webdriver.common.by import By  #指定用什么方式查找元素
from selenium.webdriver.support.ui import WebDriverWait   #智能等待页面加载完成
from selenium.webdriver.support import expected_conditions as EC  #等待 “某个条件满足”
from selenium.common.exceptions import TimeoutException #等待超时异常

# 测试代码位置说明（基于当前行号，后续增删代码后行号会变化）
# 1) !!!  单次测试开关：第 27-28 行（TEST_ONE_CATEGORY）   !!!!
# 2) Men's Basketball 匹配函数：第 57 行（is_mens_basketball_link）
# 3) 仅悬停 Men's 的测试限制：第 81 行
# 4) 命中 Men's Basketball 后立即返回：第 122 行（判断）+ 第 124 行（命中日志）
# 5) 主流程中“只跑 1 个分类后结束”：第 257-258 行

#使用爬虫添加隐藏二级菜单中各个板块的链接
#列表用于存放链接
category_urls = []

# 排除没有下拉菜单的项,避免占位浪费时间
EXCLUDE = {"Releases", "FLX Rewards", ""}

# 按指定顺序悬停主导航
HOVER_ORDER = ["Men's", "Women's", "Kids'", "Brands", "Sale", "New & Trending"]

# 单次测试：找到 Men's Basketball 后立即结束分类采集
# TEST_ONE_CATEGORY = True  # 需要单次测试时再打开
TEST_ONE_CATEGORY = True  # 正式运行前请改回 False

#代理端口
proxy = "127.0.0.1:xxxx"    #请替换为你自己的代理端口  

#获取分类链接的函数，传入浏览器对象，返回分类链接列表
#获取分类链接的函数，传入浏览器对象，返回分类链接列表
def get_category_urls_by_hover(driver):
    global category_urls

    driver.get("https://www.footlocker.com/")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Main']"))
    )

    # 可能有 Cookie 弹窗，先尝试关闭，避免遮挡悬停
    try:
        cookie_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept All Cookies') or contains(., 'Accept')]"))
        )
        cookie_btn.click()
        time.sleep(0.8)
    except TimeoutException:
        pass
    except Exception:
        pass

    temp_urls = set()

    def is_mens_basketball_link(url, text):
        low_url = url.lower().replace("%27", "")
        low_text = text.lower().replace("’", "'")

        has_basketball = ("basketball" in low_url) or ("basketball" in low_text)
        has_mens = (
            ("mens" in low_url) or ("men's" in low_url) or ("gender:mens" in low_url)
            or ("mens" in low_text) or ("men's" in low_text)
        )
        return has_basketball and has_mens

    # 先抓主导航里可见文本 -> 元素映射，避免依赖易变 class
    nav_clickables = driver.find_elements(
        By.XPATH,
        "//nav[@aria-label='Main']//a[normalize-space()] | //nav[@aria-label='Main']//button[normalize-space()]"
    )
    nav_map = {}
    for node in nav_clickables:
        text = node.text.strip().replace("’", "'")
        if text and text not in nav_map:
            nav_map[text] = node

    # 按指定顺序悬停，自动跳过 Releases / FLX Rewards
    for nav_text in HOVER_ORDER:
        if TEST_ONE_CATEGORY and nav_text != "Men's":
            break

        if nav_text in EXCLUDE:
            continue

        item = nav_map.get(nav_text)
        if not item:
            # 兼容 New Trending / New & Trending 文案差异
            if nav_text == "New & Trending":
                item = nav_map.get("New Trending")
        if not item:
            print(f"未找到导航项：{nav_text}")
            continue

        print(f"正在悬停：{nav_text}")
        ActionChains(driver).move_to_element(item).pause(1).perform()
        time.sleep(1.2)

        # 读取当前页面所有可见链接，再筛选分类链接（避免依赖具体菜单 class 名）
        links = driver.find_elements(By.XPATH, "//a[@href]")
        for link in links:
            href = link.get_attribute("href")
            link_text = link.text.strip()

            if not href:
                continue
            if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("#"):
                continue

            full_href = urljoin("https://www.footlocker.com", href)
            parsed = urlparse(full_href)
            if not parsed.netloc.endswith("footlocker.com"):
                continue

            # 排除商品详情页，只保留分类/集合页
            if "/product/" in parsed.path:
                continue
            if ("/category/" in parsed.path) or ("/collection/" in parsed.path) or ("query=" in full_href):
                temp_urls.add(full_href)

                if TEST_ONE_CATEGORY and is_mens_basketball_link(full_href, link_text):
                    category_urls = [full_href]
                    print(f"单次测试命中 Men's Basketball：{full_href}")
                    print("已获取 1 个分类链接")
                    return

        # 控制分类链接规模在 50~100 之间
        if len(temp_urls) >= 100:
            break

    # 存入全局列表
    category_urls = list(temp_urls)[:100]
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

            if TEST_ONE_CATEGORY:
                print("单次测试模式：已完成 1 个分类，结束爬取")
                break

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