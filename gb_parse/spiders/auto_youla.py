import re
from urllib.parse import urljoin

import scrapy
import pymongo
import base64


class AutoYoulaSpider(scrapy.Spider):
    name = 'auto_youla'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    _css_selectors = {
        'brands': 'div.ColumnItemList_container__5gTrc a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'car': '#serp article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu',
    }
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = db_client["gb_data_mining"]
    collection = db["auto_youla"]
    re_patterns = {
        'author': r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar",
        'phone': r"phone%22%2C%22([a-zA-Z|\d]+)%3D%3D%22%2C%22",
        'photos': r'%2F([a-zA-Z|\d]+.jpg)%22%[a-zA-Z|\d]+%22medium%',
    }

    @staticmethod
    def _get_follow(response, selector_css, callback):
        for link_selector in response.css(selector_css):
            yield response.follow(link_selector.attrib.get('href'), callback=callback)

    def parse(self, response, **kwargs):
        yield from self._get_follow(response, self._css_selectors['brands'], self.brand_parse)

    def brand_parse(self, response):
        yield from self._get_follow(response, self._css_selectors['pagination'], self.brand_parse)
        yield from self._get_follow(response, self._css_selectors['car'], self.car_parse)

    def car_parse(self, response):
        data = {
            'title': response.css('.AdvertCard_advertTitle__1S1Ak::text').extract_first(),
            'url': response.url,
            'description': response.css('.AdvertCard_descriptionInner__KnuRi::text').extract_first(),
            'data-target-id': response.css(
                'div.app_gridContentChildren__17ZMX .AdvertCard_pageContent__24SCy').attrib['data-target-id'],
            'photos': self.get_value(response, 'photos'),
            'characteristics': self._get_characteristics(response.css(
                'div.AdvertCard_specs__2FEHc div.AdvertSpecs_row__ljPcX')),
            'author': self.get_value(response, 'author'),
            'phone': self.get_value(response, 'phone'),
        }
        self.collection.insert_one(data)

    @staticmethod
    def get_value(resp, key):
        marker = "window.transitState = decodeURIComponent"
        for script in resp.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern = re.compile(AutoYoulaSpider.re_patterns[key])
                    result = re.findall(re_pattern, script.css("::text").extract_first())
                    if not result:
                        return None
                    if key == 'author':
                        return resp.urljoin(f"/user/{result[0]}").replace("auto.", "", 1)
                    if key == 'phone':
                        return base64.b64decode(base64.b64decode(result[0][:-2])).decode()
                    if key == 'photos':
                        return [f'{"https://static.am/automobile_m3/document/l/c/87/"}{str(item)}' for item in result]

            except TypeError:
                pass

    @staticmethod
    def _find_attrs(attr, selectors):
        result = []
        for selector in selectors:
            result.append(selector.attrib.get(attr))
        return result

    @staticmethod
    def _get_characteristics(selectors):
        result = dict()
        for selector in selectors:
            key = selector.css('div.AdvertSpecs_label__2JHnS::text').extract_first()
            if key in ['Год выпуска', 'Кузов']:
                value = selector.css('div.AdvertSpecs_data__xK2Qx a::text').extract_first()
            else:
                value = selector.css('div.AdvertSpecs_data__xK2Qx::text').extract_first()
            result[key] = value
        return result
