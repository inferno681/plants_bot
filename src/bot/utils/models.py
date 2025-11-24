from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from bot.models import (
    FertilizingPeriod,
    FertilizingType,
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
)

WARM_START_KEY = 'warm_start'
WARM_END_KEY = 'warm_end'


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


def _require_mapping(raw_value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw_value, Mapping):
        raise ValueError(f'Field "{field_name}" must be a mapping.')
    return raw_value


def _require_str(raw_value: Any, field_name: str) -> str:
    if not isinstance(raw_value, str):
        raise ValueError(f'Field "{field_name}" must be a string.')
    return raw_value


def _require_int(raw_value: Any, field_name: str) -> int:
    if not isinstance(raw_value, int):
        raise ValueError(f'Field "{field_name}" must be an int.')
    return raw_value


def _get_weekday_choice(raw_choice: Any) -> set[int] | int | None:
    if raw_choice is None:
        return None
    if isinstance(raw_choice, set):
        return {int(day) for day in raw_choice}
    if isinstance(raw_choice, list):
        return {int(day) for day in raw_choice}
    if isinstance(raw_choice, int):
        return raw_choice
    raise ValueError('Weekday choice has unexpected format.')


async def save_plant(plant_data: Mapping[str, Any], is_fert: bool):
    """Plant save method."""
    today = date.today()
    cold_start, cold_end = cold_period(
        warm_start=MonthDay(
            **_require_mapping(
                plant_data.get(WARM_START_KEY),
                WARM_START_KEY,
            )
        ),
        warm_end=MonthDay(
            **_require_mapping(
                plant_data.get(WARM_END_KEY),
                WARM_END_KEY,
            )
        ),
        year=today.year,
    )
    plant = Plant(
        user_id=_require_int(plant_data.get('user_id'), 'user_id'),
        name=_require_str(plant_data.get('name'), 'name'),
        description=plant_data.get('description'),
        image=plant_data.get('image'),
        warm_period=WateringPeriod(
            start=MonthDay(
                **_require_mapping(
                    plant_data.get(WARM_START_KEY),
                    WARM_START_KEY,
                )
            ),
            end=MonthDay(
                **_require_mapping(
                    plant_data.get(WARM_END_KEY),
                    WARM_END_KEY,
                )
            ),
            schedule=WateringSchedule(
                type=FrequencyType(
                    _require_str(
                        plant_data.get('warm_freq_type'), 'warm_freq_type'
                    )
                ),
                weekday=_get_weekday_choice(
                    plant_data.get("warm_freq_days")
                    or plant_data.get("warm_freq_day")
                ),
                monthday=plant_data.get("warm_freq_day_of_month"),
            ),
        ),
        cold_period=WateringPeriod(
            start=cold_start,
            end=cold_end,
            schedule=WateringSchedule(
                type=FrequencyType(
                    _require_str(
                        plant_data.get('cold_freq_type'), 'cold_freq_type'
                    )
                ),
                weekday=_get_weekday_choice(
                    plant_data.get("cold_freq_days")
                    or plant_data.get("cold_freq_day")
                ),
                monthday=plant_data.get("cold_freq_day_of_month"),
            ),
        ),
        fertilizing=None,
        last_watered_at=today,
    )
    if is_fert:
        plant.fertilizing = FertilizingPeriod(
            start=MonthDay(
                **_require_mapping(
                    plant_data.get('fertilizing_start'), 'fertilizing_start'
                )
            ),
            end=MonthDay(
                **_require_mapping(
                    plant_data.get('fertilizing_end'), 'fertilizing_end'
                )
            ),
            type=FertilizingType(
                _require_str(
                    plant_data.get('fertilizing_frequency_type'),
                    'fertilizing_frequency_type',
                )
            ),
            frequency=_require_int(
                plant_data.get('fertilizing_frequency'),
                'fertilizing_frequency',
            ),
        )
        start_fert, end_fert = plant.fertilizing.as_period()
        if start_fert <= today <= end_fert:
            plant.last_fertilized_at = today
        plant.next_fertilizing_date()

    plant.next_watering_date()
    await plant.insert()
