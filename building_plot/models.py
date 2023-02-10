from __future__ import annotations

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

    @classmethod
    async def find_by_name(cls, location: str) -> Location | None:
        return await Location.find({"name": location}).first_or_none()


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

    @classmethod
    async def get_building_plots(
        cls, area_from: int, area_to: int, price_from: int, price_to: int
    ) -> list["BuildingPlot"]:
        return (
            await cls.find(
                {
                    "area": {"$gte": area_from, "$lte": area_to},
                    "price.value": {"$gte": price_from, "$lte": price_to},
                },
                projection_model=BuildingPlotView,
            )
            .sort([("price.value", 1), ("area", -1)])
            .to_list()
        )


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
