from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from bot.models.plant import (
    FertilizingPeriod,
    FertilizingType,
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
    _require_watering_schedule,
)


def build_watering_periods():
    warm = WateringPeriod(
        start=MonthDay(day=3, month=3),
        end=MonthDay(day=10, month=10),
        schedule=WateringSchedule(type=FrequencyType.weekly, weekday=0),
    )
    cold = WateringPeriod(
        start=MonthDay(day=11, month=10),
        end=MonthDay(day=28, month=2),
        schedule=WateringSchedule(type=FrequencyType.monthly, monthday=5),
    )
    return warm, cold


def build_plant() -> Plant:
    warm, cold = build_watering_periods()
    fertilizing = FertilizingPeriod(
        start=MonthDay(day=1, month=4),
        end=MonthDay(day=30, month=4),
        frequency=1,
        type=FertilizingType.weeks,
    )
    return Plant(
        user_id=401,
        name='Coverage',
        warm_period=warm,
        cold_period=cold,
        fertilizing=fertilizing,
        last_watered_at=date.today(),
        last_fertilized_at=date.today(),
    )


def test_next_watering_date_switches_period():
    plant = build_plant()
    plant.last_watered_at = date(date.today().year, 12, 1)
    next_date = plant.next_watering_date()
    assert isinstance(next_date, date)
    assert plant.next_watering_at == next_date


def test_next_fertilizing_date_rollover():
    plant = build_plant()
    plant.fertilizing.frequency = 2
    next_date = plant.next_fertilizing_date()
    assert isinstance(next_date, date)
    plant.fertilizing.frequency = None
    with pytest.raises(ValueError):
        plant.next_fertilizing_date()


def test_build_rrule_monthly():
    plant = build_plant()
    schedule = WateringSchedule(
        type=FrequencyType.monthly,
        monthday=20,
    )
    rule = plant._build_rrule(schedule, datetime.now())
    assert rule._freq == 1  # MONTHLY


def test_require_watering_schedule_raises():
    with pytest.raises(ValueError):
        _require_watering_schedule(None)


def test_sync_watering_and_fertilizing():
    plant = build_plant()
    plant.next_watering_at = date.today()
    plant.next_fertilizing_at = date.today()
    assert plant.sync_watering_and_fertilizing() is True


def test_month_day_and_period_helpers():
    month_day = MonthDay(day=15, month=8)
    assert month_day.as_date(date.today().year).month == 8
    period = WateringPeriod(
        start=MonthDay(day=30, month=12),
        end=MonthDay(day=10, month=1),
    )
    start, end = period.as_period()
    assert start <= end


def test_fertilizing_period_wraparound():
    period = FertilizingPeriod(
        start=MonthDay(day=25, month=12),
        end=MonthDay(day=5, month=1),
    )
    start, end = period.as_period()
    assert start < end


def test_frequency_type_helpers():
    texts, callbacks = FrequencyType.get_texts_and_callbacks()
    assert len(texts) == len(callbacks)
    assert 'weekly' in FrequencyType.get_names()


def test_build_rrule_invalid_schedule():
    plant = build_plant()
    schedule = SimpleNamespace(
        type=FrequencyType.weekly,
        weekday='invalid',
        monthday=None,
        note=None,
    )
    with pytest.raises(ValueError):
        plant._build_rrule(schedule, datetime.now())


def test_next_watering_date_crosses_period():
    warm = WateringPeriod(
        start=MonthDay(day=1, month=1),
        end=MonthDay(day=5, month=1),
        schedule=WateringSchedule(type=FrequencyType.weekly, weekday=0),
    )
    cold = WateringPeriod(
        start=MonthDay(day=6, month=1),
        end=MonthDay(day=31, month=12),
        schedule=WateringSchedule(type=FrequencyType.monthly, monthday=10),
    )
    plant = build_plant()
    plant.warm_period = warm
    plant.cold_period = cold
    plant.last_watered_at = date(date.today().year, 1, 5)
    next_date = plant.next_watering_date()
    assert isinstance(next_date, date)


def test_next_fertilizing_branches():
    plant = build_plant()
    plant.fertilizing.type = FertilizingType.months
    plant.fertilizing.frequency = 1
    assert isinstance(plant.next_fertilizing_date(), date)
