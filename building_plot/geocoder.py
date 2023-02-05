from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from pydantic import BaseModel
from structlog import get_logger

from building_plot.models import Location
from building_plot.repository import Repository

log = get_logger()


class LatLong(BaseModel):
    lat: float
    long: float

    def to_tuple(self) -> tuple[float, float]:
        return self.lat, self.long


class Geocoder:
    def __init__(self, geo_locator: Nominatim, repository: Repository):
        self._geo_locator = geo_locator
        self._repository = repository

    async def get_lat_long(self, location: str) -> LatLong | None:
        from_repository = await Location.find({"name": location}).first_or_none()
        if from_repository:
            await log.ainfo("fetched location from repo")
            return LatLong(lat=from_repository.latitude, long=from_repository.longitude)
        await log.ainfo("fetching location from API")
        fetched_location = self._geo_locator.geocode(location)
        if not fetched_location:
            return None

        location = Location(
            name=location,
            latitude=fetched_location.latitude,
            longitude=fetched_location.longitude,
        )
        await log.ainfo("saving location in database")
        await location.insert()

        return LatLong(lat=fetched_location.latitude, long=fetched_location.longitude)

    @classmethod
    def calculate_distance(cls, lat_long_from: LatLong, lat_long_to: LatLong):
        return geodesic(lat_long_from.to_tuple(), lat_long_to.to_tuple()).kilometers
