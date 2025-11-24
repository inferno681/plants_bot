from __future__ import annotations

from datetime import date

import pytest

import bot.scheduler as scheduler
from beanie import PydanticObjectId

from bot.models import (
    Plant,
    WateringPeriod,
    MonthDay,
    WateringSchedule,
    FrequencyType,
)


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_photo(self, **kwargs):
        self.sent.append(('photo', kwargs))

    async def send_message(self, **kwargs):
        self.sent.append(('message', kwargs))


@pytest.mark.asyncio
async def test_send_watering_notification_without_bot():
    plant = Plant(user_id=1, name='Empty')
    scheduler.bot = None
    result = await scheduler.send_watering_notification(plant)
    assert result is False


def build_plant(has_image: bool) -> Plant:
    period = WateringPeriod(
        start=MonthDay(day=1, month=1),
        end=MonthDay(day=31, month=12),
        schedule=WateringSchedule(type=FrequencyType.weekly, weekday=0),
    )
    plant = Plant(
        user_id=5,
        name='Plant',
        warm_period=period,
        cold_period=period,
        next_watering_at=date.today(),
    )
    plant.id = PydanticObjectId()
    plant.fertilizing = None
    plant.next_fertilizing_at = None
    if has_image:
        plant.image = 'http://image'
    return plant


@pytest.mark.asyncio
async def test_send_watering_notification_message_branch(monkeypatch):
    plant = build_plant(has_image=False)
    fake_bot = FakeBot()
    scheduler.bot = fake_bot
    monkeypatch.setattr(scheduler, 'watering_kb', lambda **kwargs: kwargs)

    result = await scheduler.send_watering_notification(plant)

    assert result is True
    assert fake_bot.sent[0][0] == 'message'


@pytest.mark.asyncio
async def test_send_watering_notification_photo_branch(monkeypatch):
    plant = build_plant(has_image=True)
    fake_bot = FakeBot()
    scheduler.bot = fake_bot
    monkeypatch.setattr(scheduler, 'watering_kb', lambda **kwargs: kwargs)

    result = await scheduler.send_watering_notification(plant)

    assert result is True
    assert fake_bot.sent[0][0] == 'photo'


@pytest.mark.asyncio
async def test_watering_notifications(monkeypatch):
    plant = build_plant(has_image=False)

    async def fake_find(cls):
        return [plant]

    async def fake_send(instance):
        return True

    monkeypatch.setattr(
        scheduler.Plant, 'find_to_water_today', classmethod(fake_find)
    )
    monkeypatch.setattr(scheduler, 'send_watering_notification', fake_send)

    await scheduler.watering_notifications()
