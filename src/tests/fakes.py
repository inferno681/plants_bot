from __future__ import annotations

from types import SimpleNamespace
from typing import Any


def make_user(
    user_id: int = 1,
    first_name: str = 'First',
    last_name: str | None = 'Last',
    username: str | None = 'user',
    full_name: str = 'First Last',
    language_code: str | None = 'en',
    is_premium: bool | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        full_name=full_name,
        language_code=language_code,
        is_premium=is_premium,
    )


class FakeFSMContext:
    def __init__(self):
        self._state: str | None = None
        self.data: dict[str, Any] = {}

    async def get_state(self) -> str | None:
        return self._state

    async def set_state(self, state):
        if hasattr(state, 'state'):
            self._state = state.state
        else:
            self._state = state

    async def update_data(self, new_data: dict[str, Any]):
        self.data.update(new_data)

    async def get_data(self) -> dict[str, Any]:
        return self.data

    async def clear(self):
        self._state = None
        self.data = {}


class FakeMessage:
    def __init__(
        self,
        user: SimpleNamespace | None = None,
        text: str | None = None,
        photo: list | None = None,
    ):
        self.from_user = user or make_user()
        self.text = text
        self.photo = photo
        self.answers: list[tuple[str, Any]] = []
        self.deleted = False
        self.edited_markup: list[Any] = []
        self.edited_text: list[str] = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))

    async def delete(self):
        self.deleted = True

    async def edit_reply_markup(self, reply_markup=None):
        self.edited_markup.append(reply_markup)

    async def edit_text(self, text: str, **kwargs):
        self.edited_text.append(text)


class FakeCallback:
    def __init__(
        self, message: FakeMessage, user: SimpleNamespace | None = None
    ):
        self.message = message
        self.from_user = user or message.from_user
        self.answers: list[str] = []

    async def answer(self, text: str = '', **kwargs):
        self.answers.append(text)
