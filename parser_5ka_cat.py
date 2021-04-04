import time
import requests
import json
from pathlib import Path


class Parser5ka:
    headers = {
        'User-Agent': 'Phil K'
    }

    def __init__(self, start_url: str, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            try:
                response = requests.get(url, headers=self.headers)
            except requests.exceptions.HTTPError as err_http:
                print("Http Error:", err_http)
                return None
            except requests.exceptions.ConnectionError as err_connect:
                print("Error Connecting:", err_connect)
                return None
            except requests.exceptions.Timeout as err_timeout:
                print("Timeout Error:", err_timeout)
                return None
            except requests.exceptions.RequestException as err:
                print("Something Else", err)
                return None
            else:
                if response.status_code in [200, 300, 301, 302]:
                    return response
                time.sleep(1)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.save_path.joinpath(f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url: str):
        while url:
            response = self._get_response(url)
            if response:
                try:
                    data: dict = response.json(encoding='utf-8')
                    url = data["next"]
                    for product in data["results"]:
                        yield product
                except json.decoder.JSONDecodeError as err_json:
                    print('err_json:', err_json)
            else:
                return []

    def _save(self, data: dict, file_path: Path):
        try:
            file_path.write_text(json.dumps(data, ensure_ascii=False))
        except IOError as err_IO:
            print('err_IO:', err_IO)


class Parser5kaCat(Parser5ka):
    def __init__(self, categories_url, *args, **kwargs):
        self.categories_url = categories_url
        super().__init__(*args, **kwargs)

    def _get_categories(self):
        response = self._get_response(self.categories_url)
        if response:
            try:
                data = response.json()
                return data
            except json.decoder.JSONDecodeError as err_json:
                print(err_json)
                return []
        else:
            return []

    def run(self):
        for category in self._get_categories():
            category["products"] = []
            params = f"?categories={category['parent_group_code']}"
            url = f"{self.start_url}{params}"

            category["products"].extend(list(self._parse(url)))
            file_name = f"{category['parent_group_code']}.json"
            cat_path = self.save_path.joinpath(file_name)
            self._save(category, cat_path)


def get_save_path(dir_name):
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path


if __name__ == '__main__':
    url = "https://5ka.ru/api/v2/special_offers/"
    cat_url = "https://5ka.ru/api/v2/categories/"
    cat_parser = Parser5kaCat(cat_url, url, get_save_path("categories"))
    cat_parser.run()
