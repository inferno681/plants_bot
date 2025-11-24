from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import (
    DAYS_OF_WEEK,
    NO_DAYS_SELECTED_MSG,
    WATERING_FREQUENCY_CONFIG,
    add_plant,
)
from bot.keyboard import DayCallback, days_kb, frequency_type_kb, get_cancel_kb
from bot.models import FrequencyType
from bot.states import AddPlant
from bot.utils.telegram import (
    require_callback_data,
    require_message,
    require_text,
)


async def handle_frequency_choice(
    callback: CallbackQuery, state: FSMContext, prefix: str
):
    """Frequency choice (weekly / biweekly / monthly)."""
    data = require_callback_data(callback)
    freq_type = FrequencyType[data]
    await state.update_data({f'{prefix}_freq_type': freq_type.value})

    cfg = WATERING_FREQUENCY_CONFIG[freq_type.value]
    message = require_message(callback)
    kb_config: dict[str, Any] | None = cfg['kb']

    await message.edit_text(
        cfg['text'].format(
            period='тёплого' if prefix == 'warm' else 'холодного'
        ),
        reply_markup=days_kb(**kb_config) if kb_config else None,
    )
    state_suffix = cfg['state_suffix']
    await state.set_state(getattr(AddPlant, f'{prefix}_{state_suffix}'))
    await callback.answer()


async def handle_weekly_days(
    callback: CallbackQuery,
    callback_data: DayCallback,
    state: FSMContext,
    prefix: str,
):
    """Multi choice days of week."""
    day = callback_data.idx

    state_data = await state.get_data()
    key = f'{prefix}_freq_days'
    raw_selected = state_data.get(key, [])
    if isinstance(raw_selected, set):
        selected = list(raw_selected)
    elif isinstance(raw_selected, list):
        selected = list(raw_selected)
    else:
        selected = []

    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)

    await state.update_data({key: selected})
    message = require_message(callback)
    await message.edit_reply_markup(reply_markup=days_kb(selected))
    await callback.answer()


async def handle_weekly_done(
    callback: CallbackQuery, state: FSMContext, prefix: str
):
    """Confirmation of selecting multiple days."""
    state_data = await state.get_data()
    key = f'{prefix}_freq_days'
    raw_days = state_data.get(key, [])
    if isinstance(raw_days, (set, list)):
        days = list(raw_days)
    else:
        days = []
    if not days:
        await callback.answer(NO_DAYS_SELECTED_MSG, show_alert=True)
        return

    await state.update_data({key: set(days)})
    days_str = ', '.join(DAYS_OF_WEEK[day] for day in sorted(days))
    confirmation_text = add_plant.SELECTED_DAYS_MSG.format(days_str=days_str)
    message = require_message(callback)

    if prefix == 'warm':
        await message.edit_text(
            text=(
                f'{confirmation_text}\n\n{add_plant.ASK_COLD_PERIOD_FREQ_MSG}'
            ),
            reply_markup=frequency_type_kb(
                *FrequencyType.get_texts_and_callbacks(),
            ),
        )
        await state.set_state(AddPlant.cold_freq_type)
    else:
        await message.answer(
            (
                f'{confirmation_text}\n\n'
                f'{add_plant.ASK_FERTILIZING_PERIOD_START_MSG}'
            ),
            reply_markup=get_cancel_kb(back=True, skip=True),
        )
        await state.set_state(AddPlant.fertilizing_start)
    await callback.answer()


async def handle_biweekly_day(
    callback: CallbackQuery,
    callback_data: DayCallback,
    state: FSMContext,
    prefix: str,
):
    """Handle one day choose."""
    idx = callback_data.idx
    await state.update_data({f'{prefix}_freq_day': idx})
    day_str = DAYS_OF_WEEK[idx]
    message = require_message(callback)
    await message.edit_text(add_plant.SELECTED_DAY_MSG.format(day_str=day_str))
    if prefix == 'warm':
        await message.edit_text(
            text=add_plant.ASK_COLD_PERIOD_FREQ_MSG,
            reply_markup=frequency_type_kb(
                *FrequencyType.get_texts_and_callbacks(),
            ),
        )
        await state.set_state(AddPlant.cold_freq_type)
    else:
        await message.answer(
            add_plant.ASK_FERTILIZING_PERIOD_START_MSG,
            reply_markup=get_cancel_kb(back=True, skip=True),
        )
        await state.set_state(AddPlant.fertilizing_start)
    await callback.answer()


async def handle_day_of_month(
    message: Message, state: FSMContext, prefix: str
):
    """Handle day of month."""
    text = require_text(message)
    if not text.isdigit():
        await message.answer('❌ Введи число от 1 до 31.')
        return

    day = int(text)
    if not 1 <= day <= 31:
        await message.answer('❌ Число должно быть от 1 до 31.')
        return

    await state.update_data({f'{prefix}_freq_day_of_month': day})
    await message.answer(add_plant.SELECTED_DAY_MSG.format(day_str=day))
    if prefix == 'warm':
        await message.answer(
            text=add_plant.ASK_COLD_PERIOD_FREQ_MSG,
            reply_markup=frequency_type_kb(
                *FrequencyType.get_texts_and_callbacks(),
            ),
        )
        await state.set_state(AddPlant.cold_freq_type)
    else:
        await message.answer(
            add_plant.ASK_FERTILIZING_PERIOD_START_MSG,
            reply_markup=get_cancel_kb(back=True, skip=True),
        )
        await state.set_state(AddPlant.fertilizing_start)
