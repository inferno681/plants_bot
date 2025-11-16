from enum import StrEnum, auto

from aiogram.filters.callback_data import CallbackData


class DayCallback(CallbackData, prefix='day'):
    idx: int
    action: str


class PlantActionCallback(CallbackData, prefix='plant'):
    idx: str
    is_fertilized: bool


class Action(StrEnum):
    next = auto()
    prev = auto()
    cancel = auto()
    delete = auto()
    check = auto()


class ChoicePlantCallback(CallbackData, prefix='choice'):
    action: Action
    name: str | None
