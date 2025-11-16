from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import (
    DAYS_OF_WEEK,
    NO_DAYS_SELECTED_MSG,
    WATERING_FREQUENCY_CONFIG,
    add_plant,
)
from bot.keyboard import DayCallback, days_kb, frequency_type_kb, get_cancel_kb
from bot.model import FrequencyType
from bot.states import AddPlant


async def handle_frequency_choice(
    callback: CallbackQuery, state: FSMContext, prefix: str
):
    """Frequency choice (weekly / biweekly / monthly)."""
    freq_type = FrequencyType[callback.data]
    await state.update_data(**{f'{prefix}_freq_type': freq_type.value})

    cfg = WATERING_FREQUENCY_CONFIG[freq_type.value]

    await callback.message.edit_text(
        cfg['text'].format(
            period='тёплого' if prefix == 'warm' else 'холодного'
        ),
        reply_markup=days_kb(**cfg['kb']) if cfg['kb'] else None,
    )
    await state.set_state(getattr(AddPlant, f'{prefix}_{cfg['state_suffix']}'))
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
    selected = state_data.get(key, [])

    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)

    await state.update_data(**{key: selected})
    await callback.message.edit_reply_markup(reply_markup=days_kb(selected))
    await callback.answer()


async def handle_weekly_done(
    callback: CallbackQuery, state: FSMContext, prefix: str
):
    """Confirmation of selecting multiple days."""
    state_data = await state.get_data()
    key = f'{prefix}_freq_days'
    days = state_data.get(key, [])
    if not days:
        await callback.answer(NO_DAYS_SELECTED_MSG, show_alert=True)
        return

    await state.update_data(**{key: set(days)})
    days_str = ', '.join(DAYS_OF_WEEK[day] for day in sorted(days))
    confirmation_text = add_plant.SELECTED_DAYS_MSG.format(days_str=days_str)

    if prefix == 'warm':
        await callback.message.edit_text(
            text=(
                f'{confirmation_text}\n\n{add_plant.ASK_COLD_PERIOD_FREQ_MSG}'
            ),
            reply_markup=frequency_type_kb(
                *FrequencyType.get_texts_and_callbacks(),
            ),
        )
        await state.set_state(AddPlant.cold_freq_type)
    else:
        await callback.message.answer(
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
    await state.update_data(**{f'{prefix}_freq_day': idx})
    day_str = DAYS_OF_WEEK[idx]
    await callback.message.edit_text(
        add_plant.SELECTED_DAY_MSG.format(day_str=day_str)
    )
    if prefix == 'warm':
        await callback.message.edit_text(
            text=add_plant.ASK_COLD_PERIOD_FREQ_MSG,
            reply_markup=frequency_type_kb(
                *FrequencyType.get_texts_and_callbacks(),
            ),
        )
        await state.set_state(AddPlant.cold_freq_type)
    else:
        await callback.message.answer(
            add_plant.ASK_FERTILIZING_PERIOD_START_MSG,
            reply_markup=get_cancel_kb(back=True, skip=True),
        )
        await state.set_state(AddPlant.fertilizing_start)
    await callback.answer()


async def handle_day_of_month(
    message: Message, state: FSMContext, prefix: str
):
    """Handle day of month."""
    if not message.text.isdigit():
        await message.answer('❌ Введи число от 1 до 31.')
        return

    day = int(message.text)
    if not 1 <= day <= 31:
        await message.answer('❌ Число должно быть от 1 до 31.')
        return

    await state.update_data(**{f'{prefix}_freq_day_of_month': day})
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
