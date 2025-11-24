from __future__ import annotations

import pytest

from bot.constants import CANCEL, STATE_MESSAGES
from bot.constants.error import SKIP_ACTION_ERROR_MSG
from bot.constants.message import (
    DESCRIPTION_SKIP_MSG,
    FIRST_STEP_MSG,
    PHOTO_SKIP_MSG,
)
from bot.handlers.cmd import (
    back_handler,
    cancel_handler,
    command_start_handler,
    skip_handler,
)
from bot.models import User
from bot.states import AddPlant
from tests.fakes import FakeFSMContext, FakeMessage, make_user


@pytest.mark.asyncio
async def test_command_start_handler_creates_user():
    user = make_user(user_id=201, full_name='Tester')
    message = FakeMessage(user)

    await command_start_handler(message)

    stored = await User.find_one(User.user_id == user.id)
    assert stored is not None
    assert 'Привет' in message.answers[-1][0]


@pytest.mark.asyncio
async def test_cancel_handler_clears_state():
    message = FakeMessage()
    state = FakeFSMContext()
    await state.set_state(AddPlant.name)

    await cancel_handler(message, state)

    assert await state.get_state() is None
    assert message.answers[-1][0] == CANCEL


@pytest.mark.asyncio
async def test_skip_handler_description():
    message = FakeMessage()
    state = FakeFSMContext()
    await state.set_state(AddPlant.description)

    await skip_handler(message, state)

    assert await state.get_state() == AddPlant.image.state
    assert state.data['description'] is None
    assert DESCRIPTION_SKIP_MSG in message.answers[-1][0]


@pytest.mark.asyncio
async def test_skip_handler_image():
    message = FakeMessage()
    state = FakeFSMContext()
    await state.set_state(AddPlant.image)

    await skip_handler(message, state)

    assert await state.get_state() == AddPlant.warm_start.state
    assert PHOTO_SKIP_MSG in message.answers[-1][0]


@pytest.mark.asyncio
async def test_skip_handler_fertilizing_start(monkeypatch):
    called = {}

    async def fake_save_plant(plant_data, is_fert):
        called['data'] = plant_data
        called['is_fert'] = is_fert

    monkeypatch.setattr('bot.handlers.cmd.save_plant', fake_save_plant)

    user = make_user(user_id=202)
    message = FakeMessage(user)
    state = FakeFSMContext()
    await state.set_state(AddPlant.fertilizing_start)
    await state.update_data({'dummy': 'value'})

    await skip_handler(message, state)

    assert called['is_fert'] is False
    assert called['data']['user_id'] == user.id
    assert await state.get_state() is None


@pytest.mark.asyncio
async def test_back_handler_without_history():
    message = FakeMessage()
    state = FakeFSMContext()

    await back_handler(message, state)

    assert message.answers[-1][0] == FIRST_STEP_MSG


@pytest.mark.asyncio
async def test_back_handler_with_history():
    message = FakeMessage()
    state = FakeFSMContext()
    await state.update_data({'history': ['AddPlant:description']})

    await back_handler(message, state)

    assert await state.get_state() == AddPlant.description.state
    expected = STATE_MESSAGES[AddPlant.description]
    assert expected in message.answers[-1][0]


@pytest.mark.asyncio
async def test_back_handler_invalid_history():
    message = FakeMessage()
    state = FakeFSMContext()
    await state.update_data({'history': ['Unknown:state']})

    await back_handler(message, state)

    assert SKIP_ACTION_ERROR_MSG in message.answers[-1][0]
