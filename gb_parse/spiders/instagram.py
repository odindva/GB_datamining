import datetime
import json

import scrapy


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com', 'i.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _login_url = '/accounts/login/ajax/'
    _tags_path = '/explore/tags/'
    _csrf_token = None

    def __init__(self, login, password, tags, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = tags
        super().__init__(*args, **kwargs)

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            if self._csrf_token is None:
                self._csrf_token = js_data['config']['csrf_token']
            yield scrapy.FormRequest(
                response.urljoin(self._login_url),
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={
                    'X-CSRFToken': self._csrf_token
                }
            )
        except AttributeError:
            if response.json()['authenticated']:
                for tag in self.tags:
                    yield response.follow(f'{self._tags_path}{tag}/', callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        try:
            recent = response.json()
        except json.decoder.JSONDecodeError:
            js_data = self.js_data_extract(response)
            recent = js_data['entry_data']['TagPage'][0]['data']['recent']
        lines = recent['sections']
        for line in lines:
            medias = line['layout_content']['medias']
            for media in medias:
                data = {
                    'datetime': datetime.datetime.utcnow(),
                    'data': media['media'],
                    'photos': self.get_photos(media['media']),
                }
                yield data
        yield scrapy.FormRequest(
            f'https://i.instagram.com/api/v1/tags/python/sections/',
            method='POST',
            callback=self.tag_page_parse,
            formdata={
                'include_persistent': '0',
                'max_id': recent['next_max_id'],
                'page': str(recent['next_page']),
                'surface': 'grid',
                'tab': 'recent'
            },
            headers={
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Content-Length': '183',
                'TE': 'Trailers',
                'Host': 'i.instagram.com',
                'Original': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/',
                'Cookie': 'mid=YILnHAALAAGzukoanEVxMVFopg0m; ig_did=29550BA7-08A7-4A21-AD57-9C8A4DA74FBF; ig_nrcb=1; shbid=523; shbts=1619251671.079559; csrftoken=6jXjwzmF2bxaHQHoxDUZTOhIiBjIwBA2; fbm_124024574287414=base_domain=.instagram.com; ds_user_id=7488362233; sessionid=7488362233%3AYRQlFtSRc0K5Rz%3A21; rur=ATN; fbsr_124024574287414=emlQDj8EBFxghJDgm9gz0FIHwItHCbASodd9G0G8l58.eyJ1c2VyX2lkIjoiMTAwMDAyMjQ4MDExODI3IiwiY29kZSI6IkFRQW5NeFU3NHdudHJCUjZfcTU4eVJnWGxYUEtISHo3dG9XYzdsZURkOE5Ccno0V2xoOVpJV1Nma1YyR2dGNlRZLXRtQS03MjhZeXhIN…QXkxRVpsOVVTaTFNTVlNLUJ0TlVSLVNKMk1sZ0xhdlhEOUc2bXhaUHlBd2EtUzJWdFQ1YmY4NldlLXMxaVR0Y1ZBZEhoQUNfNHozZlVJYXc1WjBmazhjSGd6aTB2Uk9tWjN3bEtpaS12NnUyWU1ubGRSaHp6ZEtyaTIzeVNveUFRVXFLIiwib2F1dGhfdG9rZW4iOiJFQUFCd3pMaXhuallCQUN1NFpCcmVMR2J2alpBSXBWemltM09DbGNNTEVDNWdUemJHSTR0QzFwaWdjbUVhbDZGbkozbHg5bnhaQmptNnphN0p1SWNHUUVmM1pCazdGRjBoZHhDcERoUGszblpBRk5QSzg1Y2ZOVjBEdzRhOFlWR093NXhNYU9rN2VveWVFUTRHdDJxblVuaWZ4ZDRvQTN6WkN3Qzk3NmNWOEpxWTdlNTRuVnl4bm0iLCJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImlzc3VlZF9hdCI6MTYxOTM2MTkwNn0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': self._csrf_token,
                'X-IG-App-ID': '936619743392459',
                'X-IG-WWW-Claim': 'hmac.AR2GeVsuxOBUEnSn_FbWknvSMCL0rVZ2vCohTuvt20O-8fq8',
                'X-Instagram-AJAX': '822bad258fea'
            }
        )

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
