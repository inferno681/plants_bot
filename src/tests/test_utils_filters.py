from __future__ import annotations

import pytest

from bot.constants.add_plant import NO_PHOTO_MSG
from bot.constants.error import DATE_BAD_FORMAT
from bot.constants import (
    DATE_BAD_DAY_RANGE,
    DATE_BAD_MONTH_RANGE,
    DATE_INVALID_DAY_IN_MONTH,
)
from bot.utils.filters import DateFilter, PhotoRequiredFilter, TextRequiredFilter
from bot.states import AddPlant
from tests.fakes import FakeFSMContext, FakeMessage


@pytest.mark.asyncio
async def test_text_required_filter_handles_missing_text():
    filter_ = TextRequiredFilter()
    state = FakeFSMContext()
    await state.set_state(AddPlant.name)
    message = FakeMessage(text=None)

    result = await filter_(message, state)

    assert result is False
    assert message.answers


@pytest.mark.asyncio
async def test_photo_required_filter():
    filter_ = PhotoRequiredFilter()
    message = FakeMessage(photo=None)
    result = await filter_(message)
    assert result is False
    assert message.answers[-1][0] == NO_PHOTO_MSG
    message_with_photo = FakeMessage(photo=['id'])
    assert await filter_(message_with_photo) is True


@pytest.mark.asyncio
async def test_date_filter_validates_format():
    filter_ = DateFilter()
    message = FakeMessage(text='bad')

    result = await filter_(message)
    assert result is False
    assert message.answers[-1][0] == DATE_BAD_FORMAT

    message.text = '12-05'
    result = await filter_(message)
    assert result == {'day': 12, 'month': 5}

    message.text = '32-01'
    result = await filter_(message)
    assert result is False
    assert message.answers[-1][0] == DATE_BAD_DAY_RANGE

    message.text = '10-13'
    result = await filter_(message)
    assert DATE_BAD_MONTH_RANGE.format(month=13) == message.answers[-1][0]

    message.text = '31-02'
    result = await filter_(message)
    assert DATE_INVALID_DAY_IN_MONTH.format(month=2, day=31) == message.answers[-1][0]
