import scrapy
from gb_parse.loaders import VacancyLoader
from gb_parse.loaders import CompanyLoader


class HeadhunterSpider(scrapy.Spider):
    name = 'HeadHunter'
    allowed_domains = ['samara.hh.ru', 'hh.ru']
    start_urls = ['https://samara.hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    _selectors = {
        'pagination': '//div[contains(@class, "bloko-gap")]//a[@class="bloko-button"]/@href',
        'vacancy': '//div[contains(@class, "vacancy-serp-item")]//a[@class="bloko-link"]/@href',
        'company': '//div[contains(@class, "bloko-gap")]//a[@class="vacancy-company-name"]/@href',
        'vacancies_from_company': '//div[@class="employer-sidebar"]//'
                                  'a[@data-qa="employer-page__employer-vacancies-link"]/@href'
    }

    _vacancy_data_query = {
        'name': '//div[@class="vacancy-title"]/h1//text()',
        'salary': '//div[@class="vacancy-title"]/p[@class="vacancy-salary"]//text()',
        'experience': '//div[@class="vacancy-description"]//span[@data-qa="vacancy-experience"]//text()',
        'busyness': '//div[@class="vacancy-description"]//p[@data-qa="vacancy-view-employment-mode"]//text()',
        'description': '//div[@class="vacancy-section"]/div[@class="g-user-content"]',
        'skill': '//div[@class="vacancy-section"]//span[@data-qa="bloko-tag__text"]//text()',
        'author': '//div[@class="vacancy-company__details"]//a[@class="vacancy-company-name"]/@href',
    }

    _company_data_query = {
        'name': '//div[@class="company-header"]//span[@class="company-header-title-name"]/text()',
        'site': '//div[@class="employer-sidebar"]//a[@class="g-user-content"]/@href',
        'area': '//div[@class="employer-sidebar"]//div[@class="employer-sidebar-block"]/p/text()',
        'description': '//div[contains(@class, "bloko-gap")]//div[@class="company-description"]//text()',
    }

    def _get_follow(self, response, selector, callback, **kwargs):
        for link in response.xpath(selector):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, **kwargs):
        yield from self._get_follow(
            response, self._selectors["vacancy"], self.vacancy_parse,
        )
        yield from self._get_follow(
            response, self._selectors["pagination"], self.parse
        )

    def vacancy_parse(self, response):
        loader = VacancyLoader(response=response)
        loader.add_value("type", 'Vacancy')
        loader.add_value("url", response.url)
        for key, selector in self._vacancy_data_query.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
        yield from self._get_follow(
            response, self._selectors["company"], self.company_parse,
        )

    def company_parse(self, response):
        loader = CompanyLoader(response=response)
        loader.add_value("type", 'Company')
        loader.add_value("url", response.url)
        for key, selector in self._company_data_query.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
        yield from self._get_follow(
            response, self._selectors["vacancies_from_company"], self.parse,
        )
