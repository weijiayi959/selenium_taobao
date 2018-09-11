import re

import pymongo
from isort import SortImports
from lxml import etree

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SortImports("selenium_taobao.py")

client = pymongo.MongoClient('localhost', 27017)
db = client['taobao']
collection = db['prodaction']

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)

# browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)


# EC传入的是一个元组
def search():
    try:
        browser.get('https://www.taobao.com/')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        input.clear()
        input.send_keys('美食')
        submit.click()

        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')
        ))
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
        )
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist > div > div'))
    )
    html = browser.page_source
    response = etree.HTML(html)
    items = response.xpath('//div[@id="mainsrp-itemlist"]/div[@class="m-itemlist"]/div[@class="grid g-clearfix"]/div[@class="items"][1]')
    for item in items:
        title = item.xpath('.//img[contains(@id,"J_Itemlist_Pic_")]/@alt')
        price = item.xpath('.//div[contains(@class,"price g_price g_price-highlight")]/strong/text()')
        deal = item.xpath('.//div[contains(@class,"deal-cnt")]/text()')
        local = item.xpath('.//div[contains(@class,"location")]/text()')
        store = item.xpath('.//a[@class="shopname J_MouseEneterLeave J_ShopInfo"]/span[2]/text()')
        img = item.xpath('.//img[contains(@id,"J_Itemlist_Pic_")]/@src')
        href = item.xpath('.//div[@class="row row-2 title"]/a/@href')
        for item in range(len(title)):
            yield {
                'title': title[item],
                'price': price[item],
                'deal': deal[item],
                'local': local[item],
                'store': store[item],
                'img': img[item],
                'href': href[item]
            }


def main():
    try:
        total = search()
        total = int(re.search('(\d+)', total).group(1))
        for page_number in range(2, total+1):
            next_page(page_number)
            for item in get_products():
                collection.insert(item)
    finally:
        browser.close()

# close()关闭一个标签页
# quit()关闭浏览器


if __name__ == "__main__":
    main()
