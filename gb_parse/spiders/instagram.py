import datetime
import json

import scrapy


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _login_url = '/accounts/login/ajax/'
    _tags_path = '/explore/tags/'

    def __init__(self, login, password, tags, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = tags
        super().__init__(*args, **kwargs)

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                response.urljoin(self._login_url),
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={
                    'X-CSRFToken': js_data['config']['csrf_token']
                }
            )
        except AttributeError:
            if response.json()['authenticated']:
                for tag in self.tags:
                    yield response.follow(f'{self._tags_path}{tag}/', callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        js_data = self.js_data_extract(response)
        lines = js_data['entry_data']['TagPage'][0]['data']['recent']['sections']
        for line in lines:
            medias = line['layout_content']['medias']
            for media in medias:
                data = {
                    'datetime': datetime.datetime.utcnow(),
                    'data': media['media'],
                    'photos': self.get_photos(media['media']),
                }
                yield data

    def js_data_extract(self, response):
        script = response.xpath(
            '//body/script[contains(text(), "window._sharedData = ")]/text()'
        ).extract_first()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])

    def get_photos(self, media_data):
        photos = []
        try:
            for media in media_data['carousel_media']:
                photos.append(media['image_versions2']['candidates'][0]['url'])
        except KeyError:
            photos.append(media_data['image_versions2']['candidates'][0]['url'])
        return photos
