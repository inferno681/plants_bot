from logging import getLogger
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.constants import NOT_REGISTERED_MSG
from bot.log_message import (
    NO_USER_LOG,
    NOT_PRIVATE_CHAT_LOG,
    UNAUTHORIZED_ACCESS_LOG,
)
from bot.model import User


class UserOnlyMiddleware(BaseMiddleware):
    """Allow only registered users in private chats (except /start)."""

    def __init__(self):
        self.log = getLogger(__name__)

    async def __call__(
        self, handler, event: TelegramObject, data: dict
    ) -> Any:

        user = data.get('event_from_user')
        chat = data.get('event_chat')

        if chat and chat.type != ChatType.PRIVATE:
            self.log.info(NOT_PRIVATE_CHAT_LOG, chat.type)
            return

        if isinstance(event, Message) and (event.text or '').startswith(
            '/start'
        ):
            return await handler(event, data)

        if user is None:
            self.log.info(NO_USER_LOG)
            return

        if await self._is_registered(user.id):
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer(NOT_REGISTERED_MSG)
        elif isinstance(event, CallbackQuery):
            await event.answer(NOT_REGISTERED_MSG, show_alert=True)

        self.log.info(UNAUTHORIZED_ACCESS_LOG, user.id)
        return

    async def _is_registered(self, user_id: int) -> bool:
        try:
            return (await User.find_one(User.user_id == user_id)) is not None
        except Exception:
            return False
