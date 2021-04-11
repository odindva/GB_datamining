import typing
import requests
import bs4
from urllib.parse import urljoin
from database.database import Database
from datetime import datetime


class GbBlogParse:
    def __init__(self, start_url, db):
        self.db = db
        self.start_url = start_url
        self.tasks = []
        self.done_urls = set()

    def get_task(self, url, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            try:
                return callback(url, soup)
            except Exception:
                return lambda: None

        if url not in self.done_urls:
            self.done_urls.add(url)
            return task

        return lambda: None

    def _get_response(self, url) -> requests.Response:
        return requests.get(url)

    def _get_soup(self, url) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(self._get_response(url).text, "lxml")

    def parse_feed(self, url, soup):
        pag_ul = soup.find("ul", attrs={"class": "gb__pagination"})
        pag_urls = set(
            urljoin(url, pag_a.attrs["href"])
            for pag_a in pag_ul.find_all("a")
            if pag_a.attrs.get("href")
        )
        for pag_url in pag_urls:
            if pag_url not in self.done_urls:
                self.tasks.append(self.get_task(pag_url, self.parse_feed))
        post_items = soup.find("div", attrs={"class": "post-items-wrapper"})
        posts = set(
            urljoin(url, post_a.attrs.get("href"))
            for post_a in post_items.find_all("a", attrs={"class": "post-item__title"})
            if post_a.attrs.get("href")
        )

        for post_url in posts:
            try:
                if post_url not in self.done_urls:
                    self.tasks.append(self.get_task(post_url, self.parse_post))
            except Exception:
                pass

    def parse_post(self, url, soup):
        try:
            dates = soup.find("div",
                              attrs={"class": "blogpost-date-views"}).find("time").get("datetime")[:10].split('-')
            data = {
                "post_data": {
                    "id": soup.find("comments").attrs.get("commentable-id"),
                    "url": url,
                    "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                    "image": soup.find("div", attrs={"class": "blogpost-content"}).find("img").get("src"),
                    "date_post": datetime(int(dates[0]), int(dates[1]), int(dates[2])),
                },
                "writer_data": {
                    "url": urljoin(
                        url, soup.find("div", attrs={"itemprop": "author"}).parent.attrs.get("href")
                    ),
                    "name": soup.find("div", attrs={"itemprop": "author"}).text,
                },
                "tags_data": [
                    {"url": urljoin(url, tag.attrs.get("href")), "name": tag.text}
                    for tag in soup.find_all("a", attrs={"class": "small"})
                ],
                "comments_data": self.add_comments(soup)
            }
        except Exception as exc:
            print(exc)
            return None
        return data

    def add_comments(self, soup):
        data_minifiable_id = soup.find(
            "div", attrs={"class": "referrals-social-buttons-small-wrapper"}).get("data-minifiable-id")
        json_url = f"https://gb.ru/api/v2/comments?commentable_type=Post&commentable_id=" \
                   f"{data_minifiable_id}&order=desc"
        json_response = self._get_response(json_url)
        return json_response.json()

    def run(self):
        self.tasks.append(self.get_task(self.start_url, self.parse_feed))
        for task in self.tasks:
            try:
                task_result = task()
            except Exception:
                task_result = None
            if task_result:
                self.save(task_result)

    def save(self, data):
        if data:
            self.db.create_post(data)


if __name__ == "__main__":
    db = Database("sqlite:///gb_blog.db")
    parser = GbBlogParse("https://gb.ru/posts", db)
    parser.run()
