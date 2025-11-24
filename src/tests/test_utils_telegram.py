from __future__ import annotations

from datetime import datetime

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from bot.utils import telegram


def build_message(text: str | None = 'hello') -> Message:
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=1, type='private'),
        from_user=User(id=1, is_bot=False, first_name='Test'),
        text=text,
    )


def test_require_user_returns_user():
    user = User(id=1, is_bot=False, first_name='Test')
    assert telegram.require_user(user) is user


def test_require_user_raises_on_none():
    with pytest.raises(ValueError):
        telegram.require_user(None)


def test_require_message_accepts_valid_callback():
    message = build_message()
    callback = CallbackQuery(id='1', chat_instance='1', from_user=message.from_user, message=message)
    assert telegram.require_message(callback) is message


def test_require_message_raises():
    callback = CallbackQuery(
        id='2',
        chat_instance='1',
        from_user=User(id=1, is_bot=False, first_name='X'),
    )
    with pytest.raises(ValueError):
        telegram.require_message(callback)


def test_require_callback_data_returns_value():
    callback = CallbackQuery(
        id='3',
        chat_instance='1',
        from_user=User(id=1, is_bot=False, first_name='X'),
        data='payload',
    )
    assert telegram.require_callback_data(callback) == 'payload'


def test_require_callback_data_raises():
    callback = CallbackQuery(
        id='4',
        chat_instance='1',
        from_user=User(id=1, is_bot=False, first_name='X'),
    )
    with pytest.raises(ValueError):
        telegram.require_callback_data(callback)


def test_require_text():
    message = build_message('42')
    assert telegram.require_text(message) == '42'
    message = build_message(None)
    with pytest.raises(ValueError):
        telegram.require_text(message)
