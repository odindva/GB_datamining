import math

import scrapy
from scrapy import Selector

from gb_parse.loaders import AdLoader


class AvitoKvartirySpider(scrapy.Spider):
    name = 'avito_kvartiry'
    allowed_domains = ['www.avito.ru']
    start_urls = ['https://www.avito.ru/krasnodar/kvartiry?cd=2']

    _selectors = {
        'pagination': '//div[contains(@class, "index-center")]//span[contains(@class, "page-title-count")]/text()',
        'ad': '//div[contains(@class, "iva-item-body")]//a[contains(@class, "link-link")]/@href',
        'author': '//div[contains(@class, "item-view-seller-info")]//a[contains(@class, "seller-info-name")]/@href',
    }

    _data_query = {
        'title': '//div[@class="title-info-main"]//span[@class="title-info-title-text"]/text()',
        'price': '//div[@class="item-price"]//span[@class="js-item-price"]/text()',
        'address': '//div[@class="item-address"]//span[@class="item-address__string"]/text()',
        'parameters': '//div[@class="item-params"]//li[@class="item-params-list-item"]//text()',
        # 'photos': '//div[@class="vacancy-section"]/div[@class="g-user-content"]',
        'author': '//div[contains(@class, "item-view-seller-info")]'
                  '//div[contains(@class, "seller-info-prop js-seller-info-prop_seller-name")]'
                  '//div[@data-marker="seller-info/name"]/a/@href',
    }

    def _get_follow(self, response, selector, callback, **kwargs):
        for link in response.xpath(selector):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def _get_pagination(self, response, selector, callback, **kwargs):
        count_ads = int(response.xpath(selector).extract_first().replace('\xa0', ''))
        count_pages = math.ceil(count_ads / 70)
        count_pages = 100 if count_pages > 100 else count_pages
        url_params = response.url.split('&p=')
        next_url = url_params[0]
        next_page = None
        try:
            next_page = (int(url_params[1].split('&')[0]) + 1) if len(url_params) > 1 else 2
            if int(next_page) > count_pages:
                yield None
        except ValueError:
            yield None
        next_url = f'{next_url}&p={next_page}'
        yield response.follow(next_url, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, **kwargs):
        yield from self._get_follow(
            response, self._selectors["ad"], self.ad_parse,
        )
        yield from self._get_pagination(
            response, self._selectors["pagination"], self.parse
        )

    def ad_parse(self, response):
        loader = AdLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self._data_query.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
