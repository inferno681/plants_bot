from __future__ import annotations

from datetime import date

import pytest
from beanie import PydanticObjectId

from bot.handlers.notifications import handle_watering_callback
from bot.keyboard import PlantActionCallback
from bot.models import (
    FertilizingPeriod,
    FertilizingType,
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
)


class FakeCallbackMessage:
    def __init__(self) -> None:
        self.captions: list[tuple[str, object]] = []

    async def edit_caption(self, caption: str, reply_markup=None):
        self.captions.append((caption, reply_markup))


class FakeCallback:
    def __init__(self, message: FakeCallbackMessage):
        self.message = message
        self.answers: list[dict[str, object]] = []

    async def answer(self, text: str = '', show_alert: bool = False):
        self.answers.append({'text': text, 'show_alert': show_alert})


async def create_detailed_plant(name: str) -> Plant:
    plant = Plant(
        user_id=999,
        name=name,
        warm_period=WateringPeriod(
            start=MonthDay(day=1, month=1),
            end=MonthDay(day=28, month=2),
            schedule=WateringSchedule(
                type=FrequencyType.weekly,
                weekday={0, 2},
            ),
        ),
        cold_period=WateringPeriod(
            start=MonthDay(day=1, month=3),
            end=MonthDay(day=31, month=12),
            schedule=WateringSchedule(
                type=FrequencyType.monthly,
                monthday=15,
            ),
        ),
        fertilizing=FertilizingPeriod(
            start=MonthDay(day=1, month=4),
            end=MonthDay(day=30, month=4),
            frequency=1,
            type=FertilizingType.months,
        ),
        last_watered_at=date(2024, 1, 1),
        last_fertilized_at=date(2024, 1, 1),
    )
    await plant.insert()
    return plant


@pytest.mark.asyncio
async def test_handle_watering_callback_updates_dates(monkeypatch):
    plant = await create_detailed_plant('Calathea')
    callback_data = PlantActionCallback(idx=str(plant.id), is_fertilized=False)
    fake_message = FakeCallbackMessage()
    callback = FakeCallback(fake_message)
    monkeypatch.setattr(
        'bot.handlers.notifications.require_message',
        lambda _: fake_message,
    )

    await handle_watering_callback(callback, callback_data)

    updated = await Plant.get(plant.id)
    assert updated.last_watered_at == date.today()
    assert updated.next_watering_at and updated.next_watering_at > date.today()
    assert fake_message.captions[0][0] == 'Растение Calathea полито'
    assert callback.answers[-1]['show_alert'] is False


@pytest.mark.asyncio
async def test_handle_watering_callback_handles_missing_plant(monkeypatch):
    callback_data = PlantActionCallback(
        idx=str(PydanticObjectId()),
        is_fertilized=False,
    )
    fake_message = FakeCallbackMessage()
    callback = FakeCallback(fake_message)
    monkeypatch.setattr(
        'bot.handlers.notifications.require_message',
        lambda _: fake_message,
    )

    await handle_watering_callback(callback, callback_data)

    assert callback.answers
    assert callback.answers[0]['show_alert'] is True
    assert not fake_message.captions


@pytest.mark.asyncio
async def test_handle_watering_callback_updates_fertilizing(monkeypatch):
    plant = await create_detailed_plant('Philodendron')
    callback_data = PlantActionCallback(idx=str(plant.id), is_fertilized=True)
    fake_message = FakeCallbackMessage()
    callback = FakeCallback(fake_message)
    monkeypatch.setattr(
        'bot.handlers.notifications.require_message',
        lambda _: fake_message,
    )

    await handle_watering_callback(callback, callback_data)

    updated = await Plant.get(plant.id)
    assert updated.last_fertilized_at == date.today()
    assert updated.next_fertilizing_at and updated.next_fertilizing_at > date.today()
