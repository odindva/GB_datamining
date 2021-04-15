import re
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, Join, TakeFirst


def get_author_url(author):
    user_link = None
    try:
        if author:
            user_link = f"https://samara.hh.ru{author}"
    except IndexError:
        pass
    return user_link


def clear_salary(salary):
    try:
        result = salary.replace("\xa0", "")
    except ValueError:
        return salary
    return result


class VacancyLoader(ItemLoader):
    default_item_class = dict
    type_out = TakeFirst()
    url_out = TakeFirst()
    name_out = TakeFirst()
    salary_in = MapCompose(clear_salary)
    salary_out = Join('')
    experience_out = TakeFirst()
    busyness_out = Join('')
    description_out = TakeFirst()
    author_in = MapCompose(get_author_url)
    author_out = TakeFirst()


class CompanyLoader(ItemLoader):
    default_item_class = dict
    type_out = TakeFirst()
    url_out = TakeFirst()
    name_out = TakeFirst()
    site_out = TakeFirst()
    area_in = Join(', ')
    description_out = TakeFirst()
