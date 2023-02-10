import asyncio

from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from pydantic import BaseModel
from structlog import get_logger

from building_plot.models import Location

log = get_logger()


class LatLong(BaseModel):
    lat: float
    long: float

    def to_tuple(self) -> tuple[float, float]:
        return self.lat, self.long


class Geocoder:
    def __init__(self, geo_locator: Nominatim):
        self._geo_locator = geo_locator

    @classmethod
    def calculate_distance(cls, lat_long_from: LatLong, lat_long_to: LatLong):
        return geodesic(lat_long_from.to_tuple(), lat_long_to.to_tuple()).kilometers

    async def get_location_lat_long(self, location: str) -> LatLong | None:
        from_repository = await self._get_lat_long_from_db(location)
        if from_repository:
            return from_repository

        await log.ainfo("fetching location from API", location=location)

        lat_long = await self._get_lat_long_from_api(location)

        if not lat_long:
            await log.awarn("unable to fetch location", location=location)
            location = Location(
                name=location, latitude=float("nan"), longitude=float("nan")
            )
        else:
            location = Location(
                name=location,
                latitude=lat_long.lat,
                longitude=lat_long.long,
            )

        await log.ainfo("saving location in database")
        await location.insert()

        return lat_long

    @classmethod
    async def _get_lat_long_from_db(cls, location: str) -> LatLong | None:
        _location = await Location.find({"name": location}).first_or_none()
        if _location:
            await log.ainfo("fetched location from repo")
            return LatLong(lat=_location.latitude, long=_location.longitude)

        return None

    async def _get_lat_long_from_api(self, location: str) -> LatLong | None:
        loop = asyncio.get_running_loop()

        try:
            fetched_location = await loop.run_in_executor(
                None, self._geo_locator.geocode, location
            )
            if fetched_location is None:
                return None
        except Exception as exc:
            await log.aerror(
                f"error fetching location of `{location}`",
                exc=str(exc),
            )
        else:
            await log.ainfo(
                "fetched location from api",
                fetched_location=str(fetched_location),
            )
            return LatLong(
                lat=fetched_location.latitude, long=fetched_location.longitude
            )

        return None


async def main():
    from building_plot.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie

    client = AsyncIOMotorClient(settings.mongo_connection_string)
    await init_beanie(client.building_plots, document_models=[Location])
    geocoder = Geocoder(Nominatim(user_agent="building-plots"))
    return await geocoder.get_location_lat_long("Kraków, Swoszowice, ul. Warowna")


if __name__ == "__main__":
    asyncio.run(main())
