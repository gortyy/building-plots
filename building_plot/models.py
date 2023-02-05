from datetime import date, datetime

from beanie import Document
from pydantic import BaseModel
from pymongo import IndexModel


class Location(Document):
    name: str
    latitude: float
    longitude: float

    class Settings:
        name = "locations"
        indexes = [IndexModel([("name", 1)], unique=True, name="name_ascending")]


class Price(BaseModel):
    value: int
    currency: str


TODAY = date.today().isoformat().replace("-", "_")


class BuildingPlot(Document):
    title: str
    location: str
    area: int
    price: Price
    date_created: datetime
    distance: int | None = None

    class Settings:
        name = f"building_plots_{TODAY}"
        indexes = ["price", "area", "date_created"]


class BuildingPlotView(BaseModel):
    area: int
    price: int
    distance: int | None = None
    title: str
    location: str

    class Settings:
        projection = {
            "title": 1,
            "location": 1,
            "area": 1,
            "distance": 1,
            "price": "$price.value",
        }
