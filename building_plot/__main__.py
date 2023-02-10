import asyncio
from math import isnan

from beanie import init_beanie
from geopy.geocoders import Nominatim
from motor.motor_asyncio import AsyncIOMotorClient
from requests_html import HTMLSession
from rich import print
from tabulate import tabulate
from typer import Typer

from building_plot.geocoder import Geocoder, LatLong
from building_plot.models import BuildingPlot, Location
from building_plot.scraper import Scraper
from building_plot.settings import settings

app = Typer()


@app.command()
def scrape(url: str):
    async def _scrape():
        session = HTMLSession(mock_browser=True)
        scraper = Scraper(session)
        await init_db()
        geocoder = Geocoder(Nominatim(user_agent="building-plots"))

        plots = []
        async for listing in scraper.scrape(url):
            location = listing["location"]
            lat_long = await geocoder.get_location_lat_long(location)
            if (
                lat_long is not None
                and not isnan(lat_long.lat)
                and not isnan(lat_long.long)
            ):
                distance = geocoder.calculate_distance(
                    lat_long, LatLong(lat=50.0619474, long=19.9368564)
                )
                listing["distance"] = distance
            try:
                plots.append(BuildingPlot.parse_obj(listing))
            except:
                pass

            if len(plots) % 100 == 0:
                await BuildingPlot.insert_many(plots)
                plots.clear()

        await BuildingPlot.insert_many(plots)

    asyncio.run(_scrape())


@app.command()
def list_all():
    async def _list():
        await init_db()
        plots = await BuildingPlot.get_building_plots(
            area_from=0, area_to=10_000, price_from=0, price_to=200_000
        )

        plots = [p.dict() for p in plots]

        print(tabulate(plots, headers="keys"))

    asyncio.run(_list())


async def init_db():
    client = AsyncIOMotorClient(settings.mongo_connection_string)
    await init_beanie(client.building_plots, document_models=[Location, BuildingPlot])


if __name__ == "__main__":
    app()
