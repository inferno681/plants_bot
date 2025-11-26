from __future__ import annotations

from datetime import date

import pytest
from beanie import PydanticObjectId

import bot.scheduler as scheduler
from bot.models import (
    FrequencyType,
    MonthDay,
    Plant,
    WateringPeriod,
    WateringSchedule,
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


@pytest.mark.asyncio
async def test_send_watering_notification_without_id(monkeypatch):
    plant = Plant(user_id=5, name='Nameless')
    plant.fertilizing = None
    plant.next_fertilizing_at = None
    scheduler.bot = FakeBot()
    monkeypatch.setattr(scheduler, 'watering_kb', lambda **kwargs: kwargs)

    result = await scheduler.send_watering_notification(plant)

    assert result is False


@pytest.mark.asyncio
async def test_watering_notifications_empty_list(monkeypatch):
    async def _empty(cls):
        return []

    monkeypatch.setattr(
        scheduler.Plant, 'find_to_water_today', classmethod(_empty)
    )

    assert await scheduler.watering_notifications() is None


class DummyScheduler:
    def __init__(self, has_job: bool):
        self.running = False
        self.started = False
        self.added_jobs = []
        self.has_job = has_job

    def start(self):
        self.started = True
        self.running = True

    def get_job(self, job_id):
        return self.has_job

    def add_job(self, *args, **kwargs):
        self.added_jobs.append(kwargs)


@pytest.mark.asyncio
async def test_start_scheduler_adds_job(monkeypatch):
    dummy = DummyScheduler(has_job=False)
    monkeypatch.setattr(scheduler, 'scheduler', dummy)

    await scheduler.start_scheduler()

    assert dummy.started is True
    assert dummy.added_jobs and dummy.added_jobs[0]['id'] == scheduler.JOB_ID


@pytest.mark.asyncio
async def test_start_scheduler_when_job_exists(monkeypatch):
    dummy = DummyScheduler(has_job=True)
    monkeypatch.setattr(scheduler, 'scheduler', dummy)

    await scheduler.start_scheduler()

    assert dummy.added_jobs == []


@pytest.mark.asyncio
async def test_send_watering_notification_logs_error(monkeypatch):
    plant = build_plant(has_image=False)
    fake_bot = FakeBot()

    async def raise_send_message(**kwargs):
        raise RuntimeError('fail')

    fake_bot.send_message = raise_send_message  # type: ignore[assignment]
    scheduler.bot = fake_bot
    monkeypatch.setattr(scheduler, 'watering_kb', lambda **kwargs: kwargs)

    assert await scheduler.send_watering_notification(plant) is True


@pytest.mark.asyncio
async def test_start_scheduler_handles_exception(monkeypatch):
    class RaisingScheduler(DummyScheduler):
        def start(self):
            raise RuntimeError('boom')

    dummy = RaisingScheduler(has_job=False)
    monkeypatch.setattr(scheduler, 'scheduler', dummy)

    await scheduler.start_scheduler()


def test_set_bot_sets_global():
    scheduler.set_bot('bot')  # type: ignore[arg-type]
    assert scheduler.bot == 'bot'
