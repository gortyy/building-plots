from building_plot.models import BuildingPlot, BuildingPlotView, Location


class Repository:
    @classmethod
    async def get_location(cls, location: str) -> Location | None:
        return await Location.find({"name": location}).first_or_none()

    @classmethod
    async def add_location(cls, location: Location):
        if await cls.get_location(location.name) is not None:
            await location.insert()

    @classmethod
    async def get_building_plots(
        cls, area_from: int, area_to: int, price_from: int, price_to: int
    ) -> list[BuildingPlot]:
        return (
            await BuildingPlot.find(
                {
                    "area": {"$gte": area_from, "$lte": area_to},
                    "price.value": {"$gte": price_from, "$lte": price_to},
                },
                projection_model=BuildingPlotView,
            )
            .sort([("price.value", 1), ("area", -1)])
            .to_list()
        )

    @classmethod
    async def add_building_plot(cls, building_plot: BuildingPlot):
        await building_plot.insert()
