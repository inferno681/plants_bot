from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from bot.handlers.check_plants import cmd_check_all
from bot.models import Plant


class FakeMessage:
    def __init__(self, user_id: int):
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[tuple[str, object]] = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.asyncio
async def test_cmd_check_all_no_plants():
    message = FakeMessage(user_id=123)

    await cmd_check_all(message)

    assert message.answers
    text, _ = message.answers[0]
    assert 'Растения не отслеживаются' in text


@pytest.mark.asyncio
async def test_cmd_check_all_lists_plants():
    message = FakeMessage(user_id=456)
    await Plant(
        user_id=456,
        name='Monstera',
        last_watered_at=date(2024, 1, 1),
        last_fertilized_at=date(2024, 2, 1),
    ).insert()
    await Plant(
        user_id=456,
        name='Ficus',
        last_watered_at=date(2024, 3, 1),
        last_fertilized_at=date(2024, 4, 1),
    ).insert()

    await cmd_check_all(message)

    assert len(message.answers) == 1
    text, _ = message.answers[0]
    assert '1. Monstera' in text
    assert '2. Ficus' in text
