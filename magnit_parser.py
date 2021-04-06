import time

import requests
from urllib.parse import urljoin
import bs4
import pymongo
from datetime import datetime, date


class MagnitParser:
    def __init__(self, start_url, db_client):
        self.start_url = start_url
        db = db_client["gb_data_mining"]
        self.collection = db["magnit"]

    def _get_response(self, url, *args, **kwargs):
        try:
            count = 60 * 10  # 10 минут
            while count:
                response = requests.get(url, *args, **kwargs)
                if response.status_code in [200, 201, 202, 300, 301, 302]:
                    return response
                time.sleep(1)
                count -= 1
        except Exception as exc:
            print(exc)
        return None

    def _get_soup(self, url, *args, **kwargs):
        try:
            return bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, "lxml")
        except Exception as exc:
            print(exc)
        return None

    def run(self):
        for product in self._parse(self.start_url):
            self._save(product)

    @property
    def _template(self):
        return {
            "url": lambda tag: urljoin(self.start_url, tag.attrs.get("href", "")),
            "promo_name": lambda tag: tag.find('div', attrs={'class': 'card-sale__header'}).text,
            "product_name": lambda tag: tag.find("div", attrs={"class": "card-sale__title"}).text,
            "old_price": lambda tag: float(tag.find('div', attrs={'class': 'label__price_old'}).
                                           find('span', attrs={'class': 'label__price-integer'}).text) +
                                     float(tag.find('div', attrs={'class': 'label__price_old'}).
                                           find('span', attrs={'class': 'label__price-decimal'}).text) / 100,
            "new_price": lambda tag: float(tag.find('div', attrs={'class': 'label__price_new'}).
                                           find('span', attrs={'class': 'label__price-integer'}).text) +
                                     float(tag.find('div', attrs={'class': 'label__price_new'}).
                                           find('span', attrs={'class': 'label__price-decimal'}).text) / 100,
            "image_url": lambda tag: urljoin(self.start_url,
                                             tag.find('img', attrs={'class': 'lazy'}).get('data-src', '')),
            "date_from": lambda tag: self._get_datetime(
                tag.find('div', attrs={'class': 'card-sale__date'}).text.split('\n')[1]),
            "date_to": lambda tag: self._get_datetime(
                tag.find('div', attrs={'class': 'card-sale__date'}).text.split('\n')[2])
        }

    @staticmethod
    def _get_datetime(string_datetime):
        if not string_datetime:
            return None
        months = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        strings_datetime = string_datetime.split()
        if not strings_datetime[-1].lower() in months:
            return None
        day = int(strings_datetime[-2])
        month = months[strings_datetime[-1]]
        year = datetime.now().timetuple()[0]
        return datetime(year, month, day)

    def _parse(self, url):
        soup = self._get_soup(url)
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        product_tags = catalog_main.find_all("a", recursive=False)
        for product_tag in product_tags:
            product = {}
            for key, funk in self._template.items():
                try:
                    product[key] = funk(product_tag)
                except Exception:
                    product[key] = None
            yield product

    def _save(self, data):
        self.collection.insert_one(data)


if __name__ == "__main__":
    url = "https://magnit.ru/promo/"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParser(url, db_client)
    parser.run()
