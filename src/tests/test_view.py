from __future__ import annotations

from datetime import date

from bot.models import (
    FertilizingPeriod,
    FertilizingType,
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
)
from bot.view import (
    format_date,
    format_fertilizing,
    format_period,
    format_plant_message_html,
    format_schedule,
)


def test_format_date():
    assert format_date(date(2024, 1, 2)) == '02.01.2024'
    assert format_date(None) == '—'


def build_plant() -> Plant:
    warm_period = WateringPeriod(
        start=MonthDay(day=1, month=1),
        end=MonthDay(day=31, month=3),
        schedule=WateringSchedule(
            type=FrequencyType.weekly, weekday={0, 2}, note='Warm note'
        ),
    )
    cold_period = WateringPeriod(
        start=MonthDay(day=1, month=4),
        end=MonthDay(day=30, month=6),
        schedule=WateringSchedule(
            type=FrequencyType.monthly,
            monthday=10,
        ),
    )
    fertilizing = FertilizingPeriod(
        start=MonthDay(day=1, month=5),
        end=MonthDay(day=31, month=5),
        frequency=1,
        type=FertilizingType.weeks,
        note='Use organic',
    )
    return Plant(
        user_id=1,
        name='Test',
        scientific_name='Latin name',
        description='Desc',
        warm_period=warm_period,
        cold_period=cold_period,
        fertilizing=fertilizing,
        last_watered_at=date(2024, 1, 1),
        next_watering_at=date(2024, 1, 7),
        last_fertilized_at=date(2024, 1, 1),
        next_fertilizing_at=date(2024, 1, 30),
    )


def test_format_schedule_and_period():
    plant = build_plant()
    schedule = format_schedule(plant.warm_period.schedule)
    assert 'Тип' in schedule and 'Дни недели' in schedule
    assert format_period(plant.warm_period).startswith('01.01')


def test_format_fertilizing():
    plant = build_plant()
    text = format_fertilizing(plant.fertilizing)
    assert 'Частота' in text
    plant.fertilizing.frequency = None
    text = format_fertilizing(plant.fertilizing)
    assert 'Тип' in text


def test_format_plant_message_html():
    plant = build_plant()
    html = format_plant_message_html(plant)
    assert '\U0001f33f <b>Test</b>' in html
    assert '\U0001f33c <b>Удобрение:</b>' in html


def test_format_schedule_with_single_day_and_empty_fertilizing():
    schedule = WateringSchedule(type=FrequencyType.weekly, weekday=0)
    assert 'День недели' in format_schedule(schedule)
    assert format_fertilizing(None) == '—'
