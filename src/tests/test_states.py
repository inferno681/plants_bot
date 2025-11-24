from __future__ import annotations

import pytest

from bot.states import AddPlant, set_next_state
from tests.fakes import FakeFSMContext


@pytest.mark.asyncio
async def test_set_next_state_tracks_history():
    state = FakeFSMContext()
    await state.set_state(AddPlant.name)
    await set_next_state(state, AddPlant.description)
    data = await state.get_data()
    assert data['history'] == [AddPlant.name.state]
    assert await state.get_state() == AddPlant.description.state
