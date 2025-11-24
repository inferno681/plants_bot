from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from bot.callback import Action, ChoicePlantCallback
from bot.constants import check_plant
from bot.handlers.check_plant import (
    CURRENT_PAGE_KEY,
    PAGES_KEY,
    cancel_handler,
    check_one_callback,
    cmd_check_one,
    next_handler,
    prev_handler,
)
from bot.models import Plant
from bot.states import PlantInfo
from config import config


class FakeFSMContext:
    def __init__(self) -> None:
        self.state = None
        self.data: dict[str, list] = {}

    async def set_state(self, state):
        self.state = state

    async def update_data(self, data: dict):
        self.data.update(data)

    async def get_data(self):
        return self.data

    async def clear(self):
        self.state = None
        self.data = {}


class FakeMessage:
    def __init__(self, user_id: int):
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[str] = []
        self.deleted = False
        self.edited_markup: list[Any] = []
        self.edited_text: list[str] = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append(text)

    async def delete(self):
        self.deleted = True

    async def edit_reply_markup(self, reply_markup=None):
        self.edited_markup.append(reply_markup)

    async def edit_text(self, text: str, **kwargs):
        self.edited_text.append(text)


class FakeCallback:
    def __init__(self, user_id: int, message: FakeMessage):
        self.from_user = SimpleNamespace(id=user_id)
        self.message = message
        self.answers: list[str] = []

    async def answer(self, text: str = '', **kwargs):
        self.answers.append(text)


async def create_plants(user_id: int, names: list[str]):
    for idx, name in enumerate(names):
        await Plant(
            user_id=user_id,
            name=name,
            last_watered_at=date(2024, 1, idx + 1),
        ).insert()


@pytest.mark.asyncio
async def test_cmd_check_one_without_plants(monkeypatch):
    message = FakeMessage(user_id=111)
    state = FakeFSMContext()

    await cmd_check_one(message, state)

    assert message.answers[-1] == check_plant.NO_PLANTS_MESSAGE
    assert state.state is None


@pytest.mark.asyncio
async def test_cmd_check_one_with_plants(monkeypatch):
    monkeypatch.setattr(config.service, 'page_size', 1, raising=False)
    user_id = 222
    await create_plants(user_id, ['Aloe', 'Ficus'])
    message = FakeMessage(user_id=user_id)
    state = FakeFSMContext()

    await cmd_check_one(message, state)

    assert state.state == PlantInfo.name
    assert PAGES_KEY in state.data
    assert message.answers


@pytest.mark.asyncio
async def test_prev_and_next_handlers(monkeypatch):
    monkeypatch.setattr(config.service, 'page_size', 1, raising=False)
    user_id = 333
    await create_plants(user_id, ['Monstera', 'Pilea'])
    ids = await Plant.get_all_ids(user_id)
    pages = [[ids[0]], [ids[1]]]
    state = FakeFSMContext()
    await state.update_data({PAGES_KEY: pages, CURRENT_PAGE_KEY: 1})
    message = FakeMessage(user_id)
    callback = FakeCallback(user_id, message)
    monkeypatch.setattr(
        'bot.handlers.check_plant.require_message',
        lambda _: message,
    )

    await prev_handler(callback, state)
    assert state.data[CURRENT_PAGE_KEY] == 0
    assert message.edited_markup

    await next_handler(callback, state)
    assert state.data[CURRENT_PAGE_KEY] == 1


@pytest.mark.asyncio
async def test_cancel_handler(monkeypatch):
    message = FakeMessage(user_id=444)
    callback = FakeCallback(444, message)
    state = FakeFSMContext()
    monkeypatch.setattr(
        'bot.handlers.check_plant.require_message',
        lambda _: message,
    )

    await cancel_handler(callback, state)

    assert message.deleted is True
    assert state.state is None


@pytest.mark.asyncio
async def test_check_one_callback_success(monkeypatch):
    user_id = 555
    await create_plants(user_id, ['Fern'])
    state = FakeFSMContext()
    message = FakeMessage(user_id)
    callback = FakeCallback(user_id, message)
    monkeypatch.setattr(
        'bot.handlers.check_plant.require_message',
        lambda _: message,
    )

    callback_data = ChoicePlantCallback(action=Action.check, name='Fern')
    await check_one_callback(callback, callback_data, state)

    assert message.edited_text


@pytest.mark.asyncio
async def test_check_one_callback_not_found(monkeypatch):
    user_id = 666
    await create_plants(user_id, ['Cactus'])
    state = FakeFSMContext()
    message = FakeMessage(user_id)
    callback = FakeCallback(user_id, message)
    monkeypatch.setattr(
        'bot.handlers.check_plant.require_message',
        lambda _: message,
    )

    callback_data = ChoicePlantCallback(action=Action.check, name='Unknown')
    await check_one_callback(callback, callback_data, state)

    expected = check_plant.PLANT_NOT_FOUND_MESSAGE.format(plant_name='Unknown')
    assert expected in message.answers[-1]
