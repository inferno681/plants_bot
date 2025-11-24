import pytest

from bot.models.plant import (
    FertilizingPeriod,
    WateringPeriod,
    WateringSchedule,
    _require_fertilizing_period,
    _require_watering_period,
    _require_watering_schedule,
)


def test_require_watering_period_returns_same_instance():
    period = WateringPeriod()
    assert _require_watering_period(period) is period


def test_require_watering_period_raises_on_none():
    with pytest.raises(ValueError):
        _require_watering_period(None)


def test_require_watering_schedule_returns_same_instance():
    schedule = WateringSchedule()
    assert _require_watering_schedule(schedule) is schedule


def test_require_watering_schedule_raises_on_none():
    with pytest.raises(ValueError):
        _require_watering_schedule(None)


def test_require_fertilizing_period_returns_same_instance():
    period = FertilizingPeriod()
    assert _require_fertilizing_period(period) is period


def test_require_fertilizing_period_raises_on_none():
    with pytest.raises(ValueError):
        _require_fertilizing_period(None)
