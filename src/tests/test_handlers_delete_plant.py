from __future__ import annotations

import importlib
from datetime import date

import pytest

from bot.callback import Action, ChoicePlantCallback
from bot.constants import NO_PLANTS_MSG, PLANT_DELETED_MESSAGE
from bot.handlers.delete_plant import (
    CURRENT_PAGE_KEY,
    PAGES_KEY,
    cancel_handler,
    cmd_delete_good,
    delete_handler,
    next_handler,
    prev_handler,
)
from bot.models import Plant
from bot.states import DeletePlant
from config import config
from tests.fakes import FakeCallback, FakeFSMContext, FakeMessage, make_user

delete_module = importlib.import_module('bot.handlers.delete_plant')


async def create_plants(user_id: int, names: list[str]):
    for idx, name in enumerate(names):
        await Plant(
            user_id=user_id,
            name=name,
            last_watered_at=date(2024, 1, idx + 1),
        ).insert()


@pytest.mark.asyncio
async def test_cmd_delete_good_no_plants():
    message = FakeMessage(make_user(user_id=10))
    state = FakeFSMContext()

    await cmd_delete_good(message, state)

    assert message.answers[-1][0] == NO_PLANTS_MSG
    assert await state.get_state() is None


@pytest.mark.asyncio
async def test_cmd_delete_good_with_plants(monkeypatch):
    monkeypatch.setattr(config.service, 'page_size', 1, raising=False)
    user = make_user(user_id=11)
    await create_plants(user.id, ['Orchid', 'Ivy'])
    message = FakeMessage(user)
    state = FakeFSMContext()

    await cmd_delete_good(message, state)

    assert await state.get_state() == DeletePlant.name.state
    assert PAGES_KEY in state.data
    assert '1' in message.answers[-1][0]


@pytest.mark.asyncio
async def test_prev_and_next_handlers(monkeypatch):
    monkeypatch.setattr(config.service, 'page_size', 1, raising=False)
    user = make_user(user_id=12)
    await create_plants(user.id, ['Rose', 'Tulip'])
    ids = await Plant.get_all_ids(user.id)
    pages = [[ids[0]], [ids[1]]]
    state = FakeFSMContext()
    await state.update_data({PAGES_KEY: pages, CURRENT_PAGE_KEY: 1})
    message = FakeMessage(user)
    callback = FakeCallback(message)
    monkeypatch.setattr(delete_module, 'require_message', lambda _: message)

    await prev_handler(callback, state)
    assert state.data[CURRENT_PAGE_KEY] == 0
    assert message.edited_markup

    await next_handler(callback, state)
    assert state.data[CURRENT_PAGE_KEY] == 1


@pytest.mark.asyncio
async def test_cancel_handler(monkeypatch):
    user = make_user(user_id=13)
    message = FakeMessage(user)
    callback = FakeCallback(message)
    state = FakeFSMContext()
    monkeypatch.setattr(delete_module, 'require_message', lambda _: message)

    await cancel_handler(callback, state)

    assert message.deleted is True


@pytest.mark.asyncio
async def test_delete_handler(monkeypatch):
    user = make_user(user_id=14)
    await create_plants(user.id, ['Lavender'])
    message = FakeMessage(user)
    callback = FakeCallback(message)
    state = FakeFSMContext()
    monkeypatch.setattr(delete_module, 'require_message', lambda _: message)

    callback_data = ChoicePlantCallback(action=Action.delete, name='Lavender')
    await delete_handler(callback, callback_data, state)

    assert (
        PLANT_DELETED_MESSAGE.format(plant_name='Lavender')
        in message.answers[-1][0]
    )
    assert await Plant.find_one(Plant.name == 'Lavender') is None
