from __future__ import annotations

from types import SimpleNamespace

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.callback import Action
from bot.constants import ADD_PLANT, BACK, CANCEL, SKIP
from bot.keyboard import (
    days_kb,
    frequency_type_kb,
    get_cancel_kb,
    get_keyboard_with_navigation,
    get_main_kb,
    watering_kb,
)


def test_days_kb_multi_choice():
    kb = days_kb(selected=[0], single_choice=False)
    assert isinstance(kb, InlineKeyboardMarkup)
    serialized = kb.model_dump()
    texts = [button['text'] for row in serialized['inline_keyboard'] for button in row]
    assert '✅ Готово' in texts


def test_get_main_kb_contains_commands():
    kb = get_main_kb()
    assert isinstance(kb, ReplyKeyboardMarkup)
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert ADD_PLANT in flat


def test_get_cancel_kb_with_back_and_skip():
    kb = get_cancel_kb(back=True, skip=True)
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert BACK in flat
    assert CANCEL in flat
    assert SKIP in flat


def test_frequency_type_kb_builds_markup():
    kb = frequency_type_kb(['A', 'B'], ['a', 'b'])
    assert isinstance(kb, InlineKeyboardMarkup)
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert texts == ['A', 'B']


def test_watering_kb_has_optional_button():
    kb = watering_kb(
        is_fertilized=True, idx='507f1f77bcf86cd799439011'
    )
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert 'Растение полито' in texts
    assert any('удобрено' in text for text in texts)


def test_get_keyboard_with_navigation():
    plants = [SimpleNamespace(name='Plant1'), SimpleNamespace(name='Plant2')]
    kb = get_keyboard_with_navigation(plants, page=0, total_pages=2, action_for_item=Action.delete)
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert 'Plant1' in texts and 'Plant2' in texts
