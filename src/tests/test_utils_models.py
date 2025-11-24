from datetime import date

import pytest

from bot.models import MonthDay, Plant
from bot.utils.models import (
    cold_period,
    _get_weekday_choice,
    _require_int,
    _require_mapping,
    _require_str,
    save_plant,
)


def test_require_mapping_accepts_mapping():
    payload = {'value': 1}
    assert _require_mapping(payload, 'payload') is payload


def test_require_mapping_rejects_non_mapping():
    with pytest.raises(ValueError):
        _require_mapping(123, 'payload')


def test_require_str_accepts_string():
    assert _require_str('text', 'field') == 'text'


def test_require_str_rejects_non_string():
    with pytest.raises(ValueError):
        _require_str(10, 'field')


def test_require_int_accepts_int():
    assert _require_int(5, 'field') == 5


def test_require_int_rejects_non_int():
    with pytest.raises(ValueError):
        _require_int('5', 'field')


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ({1, 2}, {1, 2}),
        ([1, 2], {1, 2}),
        (3, 3),
        (None, None),
    ],
)
def test_get_weekday_choice_valid_inputs(raw, expected):
    assert _get_weekday_choice(raw) == expected


def test_get_weekday_choice_rejects_invalid_input():
    with pytest.raises(ValueError):
        _get_weekday_choice('monday')


def build_plant_data() -> dict:
    return {
        'user_id': 301,
        'name': 'Integration',
        'description': 'Test plant',
        'image': 'file_id',
        'warm_start': {'day': 1, 'month': 4},
        'warm_end': {'day': 30, 'month': 9},
        'warm_freq_type': 'weekly',
        'warm_freq_days': {0, 2},
        'cold_freq_type': 'monthly',
        'cold_freq_day_of_month': 10,
        'fertilizing_start': {'day': 1, 'month': 5},
        'fertilizing_end': {'day': 31, 'month': 5},
        'fertilizing_frequency_type': 'weeks',
        'fertilizing_frequency': 1,
    }


def test_cold_period_cross_year():
    warm_start = _require_mapping({'day': 25, 'month': 12}, 'warm_start')
    warm_end = _require_mapping({'day': 5, 'month': 1}, 'warm_end')
    start, end = cold_period(
        MonthDay(**warm_start),
        MonthDay(**warm_end),
        2024,
    )
    assert start.month == 1 and end.month == 12


@pytest.mark.asyncio
async def test_save_plant_creates_document():
    data = build_plant_data()
    await save_plant(data, is_fert=True)
    stored = await Plant.find_one(Plant.name == 'Integration')
    assert stored is not None
    assert stored.warm_period.schedule.weekday == {0, 2}
    assert stored.last_watered_at == date.today()
