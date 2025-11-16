from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId

from bot.callback import (
    Action,
    ChoicePlantCallback,
    DayCallback,
    PlantActionCallback,
)
from bot.constants import (
    ADD_PLANT,
    BACK,
    CANCEL,
    CHECK_PLANT,
    CHECK_PLANTS,
    DAYS_OF_WEEK,
    DELETE_PLANT,
    MAIN_KB_PLACEHOLDER,
    NEXT_PAGE_BUTTON,
    PREV_PAGE_BUTTON,
    SKIP,
)
from bot.model import Plant


def days_kb(selected: list[int] | None = None, single_choice=False):
    selected = selected or []
    builder = InlineKeyboardBuilder()

    for idx, day in enumerate(DAYS_OF_WEEK):
        text = f"✅ {day}" if idx in selected else day
        builder.button(
            text=text,
            callback_data=DayCallback(idx=idx, action='select'),
        )

    if not single_choice:
        builder.button(
            text='✅ Готово',
            callback_data=DayCallback(idx=-1, action='done').pack(),
        )

    builder.adjust(3)
    return builder.as_markup()


def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADD_PLANT),
                KeyboardButton(text=CHECK_PLANTS),
            ],
            [
                KeyboardButton(text=DELETE_PLANT),
                KeyboardButton(text=CHECK_PLANT),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=MAIN_KB_PLACEHOLDER,
    )


def get_cancel_kb(back: bool = False, skip: bool = False):
    keyboard = []
    if back:
        keyboard.append([KeyboardButton(text=BACK)])
    keyboard.append([KeyboardButton(text=CANCEL)])
    if skip:
        keyboard[0].append(KeyboardButton(text=SKIP))
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def frequency_type_kb(
    texts: list[str], callbacks: list[str], row_width: int = 1
):
    builder = InlineKeyboardBuilder()
    for text, callback in zip(texts, callbacks):
        builder.button(text=text, callback_data=callback)
    builder.adjust(row_width)
    return builder.as_markup()


def watering_kb(is_fertilized: bool, idx: PydanticObjectId):
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Растение полито',
        callback_data=PlantActionCallback(idx=str(idx), is_fertilized=False),
    )
    if is_fertilized:
        builder.button(
            text='Растение полито и удобрено',
            callback_data=PlantActionCallback(
                idx=str(idx), is_fertilized=True
            ),
        )
    return builder.as_markup()


def get_keyboard_with_navigation(
    plants: list[Plant], page: int, total_pages: int, action_for_item: Action
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for plant in plants:
        kb.button(
            text=plant.name,
            callback_data=ChoicePlantCallback(
                action=action_for_item, name=plant.name
            ).pack(),
        )

    kb.adjust(2)

    nav = InlineKeyboardBuilder()

    if page > 0:
        nav.button(
            text=PREV_PAGE_BUTTON,
            callback_data=ChoicePlantCallback(
                action=Action.prev, name=None
            ).pack(),
        )

    if page < total_pages - 1:
        nav.button(
            text=NEXT_PAGE_BUTTON,
            callback_data=ChoicePlantCallback(
                action=Action.next, name=None
            ).pack(),
        )

    if nav.buttons:
        nav.adjust(2)
        kb.row(*nav.buttons)

    kb.button(
        text=CANCEL,
        callback_data=ChoicePlantCallback(
            action=Action.cancel, name=None
        ).pack(),
    )

    return kb.as_markup()
