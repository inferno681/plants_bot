from types import SimpleNamespace

import pytest

import bot.utils.handlers as utils_handlers
from bot.constants import DAYS_OF_WEEK, NO_DAYS_SELECTED_MSG
from bot.states import AddPlant
from bot.utils.handlers import (
    _extract_selected_days,
    _render_selected_days_text,
    handle_biweekly_day,
    handle_day_of_month,
    handle_frequency_choice,
    handle_weekly_days,
    handle_weekly_done,
)
from tests.fakes import FakeFSMContext, FakeMessage


def test_extract_selected_days_handles_list_and_set():
    data = {'warm_freq_days': [1, 2]}
    assert _extract_selected_days(data, 'warm_freq_days') == [1, 2]

    data = {'warm_freq_days': {1, 2}}
    assert sorted(_extract_selected_days(data, 'warm_freq_days')) == [1, 2]


def test_extract_selected_days_returns_empty_for_other_types():
    data = {'warm_freq_days': 'invalid'}
    assert _extract_selected_days(data, 'warm_freq_days') == []


def test_render_selected_days_text_uses_day_names():
    days = [0, 1]
    rendered = _render_selected_days_text(days)
    assert DAYS_OF_WEEK[0] in rendered
    assert DAYS_OF_WEEK[1] in rendered


class DummyCallback:
    def __init__(self, data: str, message: FakeMessage | None = None):
        self.data = data
        self.message = message or FakeMessage()
        self.answers: list[dict] = []

    async def answer(self, text: str = '', show_alert: bool = False):
        self.answers.append({'text': text, 'alert': show_alert})


@pytest.mark.asyncio
async def test_handle_frequency_choice(monkeypatch):
    state = FakeFSMContext()
    message = FakeMessage()
    callback = DummyCallback('weekly', message)
    monkeypatch.setattr(utils_handlers, 'require_message', lambda _: message)

    await handle_frequency_choice(callback, state, prefix='warm')

    assert state.data['warm_freq_type'] == 'weekly'
    assert await state.get_state() == AddPlant.warm_freq_days.state


@pytest.mark.asyncio
async def test_handle_weekly_days(monkeypatch):
    state = FakeFSMContext()
    await state.update_data({'warm_freq_days': [1]})
    message = FakeMessage()
    callback = DummyCallback('data', message)
    monkeypatch.setattr(utils_handlers, 'require_message', lambda _: message)

    await handle_weekly_days(
        callback, SimpleNamespace(idx=2), state, prefix='warm'
    )

    assert sorted(state.data['warm_freq_days']) == [1, 2]


@pytest.mark.asyncio
async def test_handle_weekly_done_with_and_without_days(monkeypatch):
    state = FakeFSMContext()
    callback = DummyCallback('data', FakeMessage())

    await handle_weekly_done(callback, state, prefix='warm')
    assert callback.answers[-1]['alert'] is True
    assert callback.answers[-1]['text'] == NO_DAYS_SELECTED_MSG

    await state.update_data({'warm_freq_days': {0, 1}})
    message = FakeMessage()
    monkeypatch.setattr(utils_handlers, 'require_message', lambda _: message)

    await handle_weekly_done(callback, state, prefix='warm')
    assert message.edited_text


@pytest.mark.asyncio
async def test_handle_biweekly_day(monkeypatch):
    state = FakeFSMContext()
    message = FakeMessage()
    callback = DummyCallback('data', message)
    monkeypatch.setattr(utils_handlers, 'require_message', lambda _: message)

    await handle_biweekly_day(
        callback, SimpleNamespace(idx=3), state, prefix='warm'
    )

    assert state.data['warm_freq_day'] == 3


@pytest.mark.asyncio
async def test_handle_day_of_month_validates(monkeypatch):
    state = FakeFSMContext()
    message = FakeMessage(text='abc')

    await handle_day_of_month(message, state, prefix='warm')
    assert 'Введи число' in message.answers[-1][0]

    message.text = '15'
    await handle_day_of_month(message, state, prefix='warm')
    assert state.data['warm_freq_day_of_month'] == 15
