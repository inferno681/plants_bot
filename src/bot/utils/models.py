from datetime import date, timedelta

from bot.models import (
    FertilizingPeriod,
    FertilizingType,
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
)


def cold_period(warm_start: MonthDay, warm_end: MonthDay, year: int):
    """Cold period from warm period."""
    warm_start_date = warm_start.as_date(year)
    warm_end_date = warm_end.as_date(year)

    cold_start = warm_end_date + timedelta(days=1)
    cold_end = warm_start_date - timedelta(days=1)

    if warm_start_date > warm_end_date:
        cold_start = warm_end_date + timedelta(days=1)
        cold_end = warm_start_date - timedelta(days=1)
    else:
        cold_end = cold_end.replace(year=year + 1)

    return (
        MonthDay(day=cold_start.day, month=cold_start.month),
        MonthDay(day=cold_end.day, month=cold_end.month),
    )


async def save_plant(plant_data: dict, is_fert: bool):
    """Plant save method."""
    today = date.today()
    cold_start, cold_end = cold_period(
        warm_start=MonthDay(**plant_data.get('warm_start')),
        warm_end=MonthDay(**plant_data.get('warm_end')),
        year=today.year,
    )
    plant = Plant(
        user_id=plant_data.get('user_id'),
        name=plant_data.get('name'),
        description=plant_data.get('description'),
        image=plant_data.get('image'),
        warm_period=WateringPeriod(
            start=MonthDay(**plant_data.get('warm_start')),
            end=MonthDay(**plant_data.get('warm_end')),
            schedule=WateringSchedule(
                type=FrequencyType(plant_data.get('warm_freq_type')),
                weekday=plant_data.get("warm_freq_days")
                or plant_data.get("warm_freq_day"),
                monthday=plant_data.get("warm_freq_day_of_month"),
            ),
        ),
        cold_period=WateringPeriod(
            start=cold_start,
            end=cold_end,
            schedule=WateringSchedule(
                type=FrequencyType(plant_data.get('cold_freq_type')),
                weekday=plant_data.get("cold_freq_days")
                or plant_data.get("cold_freq_day"),
                monthday=plant_data.get("cold_freq_day_of_month"),
            ),
        ),
        fertilizing=None,
        last_watered_at=today,
    )
    if is_fert:
        plant.fertilizing = FertilizingPeriod(
            start=MonthDay(**plant_data.get('fertilizing_start')),
            end=MonthDay(**plant_data.get('fertilizing_end')),
            type=FertilizingType(plant_data.get('fertilizing_frequency_type')),
            frequency=plant_data.get('fertilizing_frequency'),
        )
        start_fert, end_fert = plant.fertilizing.as_period()
        if start_fert <= today <= end_fert:
            plant.last_fertilized_at = today
        plant.next_fertilizing_date()

    plant.next_watering_date()
    await plant.insert()
