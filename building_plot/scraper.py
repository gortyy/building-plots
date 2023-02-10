import asyncio
import json
import random
from itertools import count
from typing import Iterable

from requests_html import HTMLSession
from structlog import get_logger

log = get_logger()


class Scraper:
    def __init__(self, session: HTMLSession):
        self._session = session

    async def scrape(self, url: str) -> Iterable[dict]:
        log.info(f"scraping {url}")
        for page in count(1):
            log.info(f"scraping page {page}")
            listings = await self._scrape_single_page(url, page)
            if not listings:
                break
            for listing in listings:
                yield listing

    async def _scrape_single_page(self, url: str, page: int) -> list[dict]:
        url = f"{url}&page={page}"
        parsed_contents = await self._get_parsed_contents(url)
        if not parsed_contents:
            return []

        listings = parsed_contents["props"]["pageProps"]["data"]["searchAds"]["items"]
        await asyncio.sleep(random.randint(10, 20))
        return [self._process_listing(listing) for listing in listings]

    async def _get_parsed_contents(self, url: str) -> dict | None:
        loop = asyncio.get_running_loop()
        selector = "#__NEXT_DATA__"
        try:
            response = await loop.run_in_executor(None, self._session.get, url)
            element_contents = response.html.find(selector)[0].text
        except Exception as exc:
            await log.aerror("error", exc=str(exc))
            return None
        else:
            return json.loads(element_contents)

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
