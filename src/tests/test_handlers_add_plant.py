from __future__ import annotations

from types import SimpleNamespace

import pytest

from bot.constants import NO_POSITIVE_INT_MSG
from bot.constants import add_plant as add_const
from bot.handlers import add_plant
from bot.models import Plant
from bot.states import AddPlant
from tests.fakes import FakeFSMContext, FakeMessage, make_user


@pytest.mark.asyncio
async def test_add_plant_entry_sets_state():
    state = FakeFSMContext()
    message = FakeMessage()

    await add_plant.add_plat_handler(message, state)

    assert await state.get_state() == AddPlant.name.state
    assert message.answers[-1][0] == add_const.ASK_NAME_MSG


@pytest.mark.asyncio
async def test_process_plant_name_duplicate(monkeypatch):
    user = make_user(user_id=42)
    await Plant(user_id=user.id, name='Monstera').insert()
    state = FakeFSMContext()
    message = FakeMessage(user=user, text='Monstera')

    await add_plant.process_plant_name(message, state)

    assert add_const.NOT_UNIQUE_NAME_MSG in message.answers[-1][0]
    assert await state.get_state() is None


@pytest.mark.asyncio
async def test_process_plant_name_success():
    user = make_user(user_id=43)
    state = FakeFSMContext()
    message = FakeMessage(user=user, text='Ficus')

    await add_plant.process_plant_name(message, state)

    assert state.data['name'] == 'Ficus'
    assert await state.get_state() == AddPlant.description.state


@pytest.mark.asyncio
async def test_process_description_and_photo(monkeypatch):
    state = FakeFSMContext()
    await state.update_data({'name': 'Peperomia'})
    desc_message = FakeMessage(text='Easy plant')
    await add_plant.process_plant_description(desc_message, state)
    assert state.data['description'] == 'Easy plant'
    assert await state.get_state() == AddPlant.image.state

    photo = SimpleNamespace(file_id='file123')
    photo_message = FakeMessage(photo=[photo])
    async def _fake_upload(*args, **kwargs):
        return 's3/key'

    monkeypatch.setattr(
        add_plant.storage_service,
        'upload_telegram_file',
        _fake_upload,
    )
    await add_plant.process_plant_photo(photo_message, state)
    assert state.data['image'] == 'file123'
    assert state.data['storage_key'] == 's3/key'
    assert await state.get_state() == AddPlant.warm_start.state


@pytest.mark.asyncio
async def test_process_warm_period_validation_and_success():
    state = FakeFSMContext()
    warm_start_message = FakeMessage()
    await add_plant.process_warm_start(
        warm_start_message, state, day=1, month=5
    )
    assert state.data['warm_start'] == {'day': 1, 'month': 5}
    assert await state.get_state() == AddPlant.warm_end.state

    await state.update_data({'warm_start': {'day': 10, 'month': 6}})
    warm_end_message = FakeMessage()
    await add_plant.process_warm_end(warm_end_message, state, day=5, month=6)
    assert add_const.INVALID_END_DATE_MSG in warm_end_message.answers[-1][0]

    await add_plant.process_warm_end(warm_end_message, state, day=20, month=6)
    assert await state.get_state() == AddPlant.warm_freq_type.state


class DummyCallback:
    def __init__(self, data: str, message: FakeMessage):
        self.data = data
        self.message = message
        self.from_user = message.from_user
        self.answers: list[str] = []

    async def answer(self, text: str = '', **kwargs):
        self.answers.append(text)


@pytest.mark.asyncio
async def test_process_fertilizing_flow(monkeypatch):
    state = FakeFSMContext()
    fert_start_message = FakeMessage(text='start')
    await add_plant.process_fertilizing_start(
        fert_start_message, state, day=1, month=7
    )
    assert state.data['fertilizing_start'] == {'day': 1, 'month': 7}
    assert await state.get_state() == AddPlant.fertilizing_end.state

    fert_end_message = FakeMessage(text='end')
    await add_plant.process_fertilizing_stop(
        fert_end_message, state, day=30, month=7
    )
    assert state.data['fertilizing_end'] == {'day': 30, 'month': 7}
    assert await state.get_state() == AddPlant.fertilizing_frequency_type.state

    callback_message = FakeMessage()
    callback = DummyCallback('days', callback_message)
    monkeypatch.setattr(
        add_plant, 'require_message', lambda _: callback_message
    )

    await add_plant.process_fertilizing_frequency_type(callback, state)

    assert state.data['fertilizing_frequency_type'] == 'days'
    assert await state.get_state() == AddPlant.fertilizing_every_n_days.state


@pytest.mark.asyncio
async def test_process_fertilizing_stop_invalid():
    state = FakeFSMContext()
    await state.update_data({'fertilizing_start': {'day': 10, 'month': 8}})
    message = FakeMessage(text='end')

    await add_plant.process_fertilizing_stop(message, state, day=5, month=8)

    assert add_const.INVALID_END_DATE_MSG in message.answers[-1][0]


@pytest.mark.asyncio
async def test_process_fertilizing_interval_validation(monkeypatch):
    user = make_user(user_id=99)
    state = FakeFSMContext()
    await state.update_data(
        {
            'name': 'Orchid',
            'warm_start': {'day': 1, 'month': 1},
            'warm_end': {'day': 2, 'month': 1},
            'warm_freq_type': 'weekly',
            'warm_freq_day': 0,
            'cold_freq_type': 'monthly',
            'cold_freq_day_of_month': 15,
            'fertilizing_start': {'day': 1, 'month': 1},
            'fertilizing_end': {'day': 2, 'month': 1},
            'fertilizing_frequency_type': 'days',
            'description': None,
            'image': None,
        }
    )
    zero_message = FakeMessage(user=user, text='0')
    await add_plant.process_fertilizing_interval(zero_message, state)
    assert NO_POSITIVE_INT_MSG in zero_message.answers[-1][0]

    good_message = FakeMessage(user=user, text='3')
    await add_plant.process_fertilizing_interval(good_message, state)

    assert await state.get_state() is None
    plants = await Plant.find(Plant.user_id == user.id).to_list()
    assert plants and plants[0].name == 'Orchid'


@pytest.mark.asyncio
async def test_process_plant_photo_requires_photo():
    state = FakeFSMContext()
    message = FakeMessage(photo=None)
    with pytest.raises(ValueError):
        await add_plant.process_plant_photo(message, state)


@pytest.mark.asyncio
async def test_warm_and_cold_frequency_wrappers(monkeypatch):
    state = FakeFSMContext()
    message = FakeMessage()
    callback = DummyCallback('weekly', message)

    called = {}

    async def fake_handle_frequency_choice(cb, st, prefix):
        called['freq'] = prefix

    async def fake_handle_weekly_days(cb, cb_data, st, prefix):
        called['weekly_days'] = prefix

    async def fake_handle_weekly_done(cb, st, prefix):
        called['weekly_done'] = prefix

    async def fake_handle_biweekly_day(cb, cb_data, st, prefix):
        called['biweekly_day'] = prefix

    async def fake_handle_day_of_month(msg, st, prefix):
        called['day_of_month'] = prefix

    monkeypatch.setattr(
        add_plant, 'handle_frequency_choice', fake_handle_frequency_choice
    )
    await add_plant.process_warm_freq_type(callback, state)
    await add_plant.process_cold_freq_type(callback, state)
    assert called['freq'] == 'cold'

    day_callback = SimpleNamespace(idx=1)
    monkeypatch.setattr(
        add_plant, 'handle_weekly_days', fake_handle_weekly_days
    )
    await add_plant.process_warm_weekly_days(callback, day_callback, state)
    await add_plant.process_cold_weekly_days(callback, day_callback, state)
    assert called['weekly_days'] == 'cold'

    monkeypatch.setattr(
        add_plant, 'handle_weekly_done', fake_handle_weekly_done
    )
    await add_plant.process_warm_weekly_done(callback, state)
    await add_plant.process_cold_weekly_done(callback, state)
    assert called['weekly_done'] == 'cold'

    monkeypatch.setattr(
        add_plant, 'handle_biweekly_day', fake_handle_biweekly_day
    )
    await add_plant.process_warm_biweekly_day(callback, day_callback, state)
    await add_plant.process_cold_biweekly_day(callback, day_callback, state)
    assert called['biweekly_day'] == 'cold'

    monkeypatch.setattr(
        add_plant, 'handle_day_of_month', fake_handle_day_of_month
    )
    await add_plant.process_warm_day_of_month(message, state)
    await add_plant.process_cold_day_of_month(message, state)
    assert called['day_of_month'] == 'cold'
