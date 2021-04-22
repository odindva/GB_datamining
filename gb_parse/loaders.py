import re
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, Join, TakeFirst


def get_author_url(author):
    user_link = None
    try:
        if author:
            if str(author).startswith('https:'):
                user_link = author
            else:
                user_link = f"https://www.avito.ru{author}"
    except IndexError:
        pass
    return user_link


class AdLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_out = TakeFirst()
    address_out = TakeFirst()
    parameters_out = Join('')
    author_in = MapCompose(get_author_url)
    author_out = TakeFirst()
