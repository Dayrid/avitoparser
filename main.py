import asyncio
import aiohttp
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


async def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options, executable_path=r"E:\ChromeDriver\chromedriver.exe")
    return driver


async def fetch_url(driver, url):
    driver.get(url)
    page_source = driver.page_source
    return page_source


async def get_soup(driver, url):
    html_text = await fetch_url(driver, url)
    soup = BeautifulSoup(html_text, "lxml")
    return soup


async def parse(url):
    items = []
    ads = []
    driver = await init_driver()
    pages = await parse_pages(driver, url)
    first_page_soup = await get_soup(driver, url)
    ads += first_page_soup.find_all(itemtype="http://schema.org/Product")
    for i in range(2, pages):
        print(i)
        i_page_soup = await get_soup(driver, url + "?p=" + str(i))
        ads += i_page_soup.find_all(itemtype="http://schema.org/Product")
    for ad in ads:
        url = "https://www.avito.ru" + ad.find("a", itemprop="url").get("href")
        full_name = ad.find("h3", itemprop="name").text.split(",")
        name = full_name[0]
        year = int(full_name[1])
        price = ad.find("meta", itemprop="price").get("content")
        damaged = ad.find("div", class_="iva-item-text-Ge6dR").find("span", class_="iva-item-autoParamsHighlight-zok6C") is not None
        complex = ad.find("div", class_="iva-item-text-Ge6dR").text.split(",")
        mileage, engine, body, drive, fuel = None, None, None, None, None
        for param in complex:
            if "л.с." in param:
                engine = param
            elif "хетчбэк" in param or "седан" in param or "универсал" in param:
                body = param
            elif "передний" in param or "задний" in param or "полный" in param:
                drive = param
            elif "бензин" in param or "газ" in "param":
                fuel = param
            elif "км" in param:
                mileage = int("".join(re.findall("[0-9]+", param)))

        items.append({
            "name": name,
            "year": year,
            "price": price,
            "mileage": mileage,
            "body": body,
            "drive": drive,
            "engine": engine,
            "fuel": fuel,
            "url": url
        })
    df = pd.DataFrame(items)
    df.to_excel("output.xlsx")
    driver.quit()


async def parse_pages(driver, url):
    soup = await get_soup(driver, url)
    return int(soup.find_all("span", class_="pagination-item-JJq_j")[-2].text)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(parse(
        'https://www.avito.ru/ufa/avtomobili/vaz_lada/2114_samara-ASgBAgICAkTgtg3GmSjitg3emig?radius=200&searchRadius=200'))
