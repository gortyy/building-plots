import json
import random
import time
from itertools import count
from typing import Iterable

from requests_html import HTMLSession
from structlog import get_logger

log = get_logger()


class Scraper:
    def __init__(self, session: HTMLSession):
        self._session = session

    def scrape(self, url: str) -> Iterable[dict]:
        log.info(f"scraping {url}")
        for page in count(1):
            log.info(f"scraping page {page}")
            listings = self._scrape_single_page(url, page)
            if not listings:
                break
            yield from listings

    def _scrape_single_page(self, url: str, page: int) -> list[dict]:
        selector = "#__NEXT_DATA__"
        url = f"{url}&page={page}"
        try:
            element_contents = self._session.get(url).html.find(selector)[0].text
        except:
            return []
        parsed_contents = json.loads(element_contents)
        listings = parsed_contents["props"]["pageProps"]["data"]["searchAds"]["items"]

        time.sleep(random.randint(10, 20))

        return [self._process_listing(listing) for listing in listings]

    @staticmethod
    def _process_listing(listing: dict) -> dict:
        del listing["totalPrice"]["__typename"]
        return {
            "title": listing["title"],
            "location": listing["locationLabel"]["value"],
            "area": listing["areaInSquareMeters"],
            "price": listing["totalPrice"],
            "date_created": listing["dateCreated"],
        }
