import re
from datetime import date

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.constants import (
    DATE_BAD_DAY_RANGE,
    DATE_BAD_FORMAT,
    DATE_BAD_MONTH_RANGE,
    DATE_INVALID_DAY_IN_MONTH,
    NO_TEXT_ERROR_MSG,
    TEXT_REQUIRED_FILTER,
)
from bot.constants.add_plant import NO_PHOTO_MSG


class TextRequiredFilter(BaseFilter):

    async def __call__(self, message: Message, state: FSMContext):
        current_state = await state.get_state()

        if not message.text:
            await message.answer(
                TEXT_REQUIRED_FILTER.get(current_state, NO_TEXT_ERROR_MSG)
            )
            return False

        return True


class PhotoRequiredFilter(BaseFilter):

    async def __call__(self, message: Message):
        if not message.photo:
            await message.answer(NO_PHOTO_MSG)
            return False
        return True


class DateFilter(BaseFilter):

    def __init__(self):
        self.pattern = re.compile(r"^(\d{1,2})[-./ ](\d{1,2})$")

    async def __call__(self, message: Message):
        assert message.text is not None
        text = message.text.strip()
        match = self.pattern.match(text)

        if not match:
            await message.answer(DATE_BAD_FORMAT)
            return False

        day, month = map(int, match.groups())

        if not (1 <= day <= 31):
            await message.answer(DATE_BAD_DAY_RANGE)
            return False

        if not (1 <= month <= 12):
            await message.answer(DATE_BAD_MONTH_RANGE.format(month))
            return False

        try:
            date(2024, month, day)
        except ValueError:
            await message.answer(
                DATE_INVALID_DAY_IN_MONTH.format(month=month, day=day)
            )
            return False

        return {
            'day': day,
            'month': month,
        }
