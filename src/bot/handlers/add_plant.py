from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import (
    ADD_PLANT,
    FERTILIZING_INTERVAL_CONFIG,
    NO_POSITIVE_INT_MSG,
    add_plant,
)
from bot.keyboard import (
    DayCallback,
    frequency_type_kb,
    get_cancel_kb,
    get_main_kb,
)
from bot.model import FertilizingType, FrequencyType, Plant
from bot.states import AddPlant, set_next_state
from bot.utils import (
    DateFilter,
    PhotoRequiredFilter,
    TextRequiredFilter,
    handle_biweekly_day,
    handle_day_of_month,
    handle_frequency_choice,
    handle_weekly_days,
    handle_weekly_done,
    save_plant,
)

router = Router(name='add_plant_router')


@router.message(F.text == ADD_PLANT)
async def add_plat_handler(message: Message, state: FSMContext) -> None:
    """Command to start adding a plant."""
    await message.answer(
        add_plant.ASK_NAME_MSG,
        reply_markup=get_cancel_kb(),
    )
    await set_next_state(state, AddPlant.name)


@router.message(AddPlant.name, TextRequiredFilter())
async def process_plant_name(message: Message, state: FSMContext) -> None:
    """Process the plant name sent by the user."""
    if await Plant.find_one(
        Plant.user_id == message.from_user.id, Plant.name == message.text
    ):
        await message.answer(
            add_plant.NOT_UNIQUE_NAME_MSG,
            reply_markup=get_cancel_kb(back=True),
        )
        return
    await state.update_data(name=message.text)

    await message.answer(
        add_plant.ASK_DESCRIPTION_MSG,
        reply_markup=get_cancel_kb(back=True, skip=True),
    )
    await set_next_state(state, AddPlant.description)


@router.message(AddPlant.description, TextRequiredFilter())
async def process_plant_description(
    message: Message, state: FSMContext
) -> None:
    """Process the description of the plant."""
    await state.update_data(description=message.text)
    await message.answer(
        add_plant.ASK_PHOTO_MSG,
        reply_markup=get_cancel_kb(back=True, skip=True),
    )
    await set_next_state(state, AddPlant.image)


@router.message(AddPlant.image, PhotoRequiredFilter())
async def process_plant_photo(message: Message, state: FSMContext):
    """Process plant photo and save by file_id."""
    file_id = message.photo[-1].file_id
    await state.update_data(image=file_id)
    await message.answer(
        add_plant.ASK_WARM_PERIOD_START_MSG,
        reply_markup=get_cancel_kb(back=True),
    )
    await set_next_state(state, AddPlant.warm_start)


@router.message(AddPlant.warm_start, TextRequiredFilter(), DateFilter())
async def process_warm_start(
    message: Message, state: FSMContext, day: int, month: int
):
    """Process the start date of the warm period."""
    await state.update_data(warm_start={'day': day, 'month': month})
    await message.answer(
        add_plant.ASK_WARM_PERIOD_END_MSG,
        reply_markup=get_cancel_kb(back=True),
    )
    await set_next_state(state, AddPlant.warm_end)


@router.message(AddPlant.warm_end, TextRequiredFilter(), DateFilter())
async def process_warm_end(
    message: Message, state: FSMContext, day: int, month: int
):
    """Process the end date of the warm period."""
    state_data = await state.get_data()
    warm_start = state_data.get('warm_start')

    if warm_start and (
        (month < warm_start['month'])
        or (month == warm_start['month'] and day < warm_start['day'])
    ):
        await message.answer(add_plant.INVALID_END_DATE_MSG)
        return

    await state.update_data(warm_end={'day': day, 'month': month})

    await message.answer(
        add_plant.ASK_WATERING_FREQUENCY_WARM_MSG,
        reply_markup=frequency_type_kb(
            *FrequencyType.get_texts_and_callbacks(),
        ),
    )
    await set_next_state(state, AddPlant.warm_freq_type)


@router.callback_query(
    AddPlant.warm_freq_type, F.data.in_(FrequencyType.get_names())
)
async def process_warm_freq_type(callback: CallbackQuery, state: FSMContext):
    await handle_frequency_choice(callback, state, prefix='warm')


@router.callback_query(
    AddPlant.warm_freq_days, DayCallback.filter(F.action == "select")
)
async def process_warm_weekly_days(
    callback: CallbackQuery, callback_data: DayCallback, state: FSMContext
):
    await handle_weekly_days(callback, callback_data, state, prefix='warm')


@router.callback_query(
    AddPlant.warm_freq_days, DayCallback.filter(F.action == "done")
)
async def process_warm_weekly_done(callback: CallbackQuery, state: FSMContext):
    await handle_weekly_done(callback, state, prefix='warm')


@router.callback_query(
    AddPlant.warm_freq_day, DayCallback.filter(F.action == "select")
)
async def process_warm_biweekly_day(
    callback: CallbackQuery, callback_data: DayCallback, state: FSMContext
):
    await handle_biweekly_day(callback, callback_data, state, prefix='warm')


@router.message(AddPlant.warm_freq_day_of_month)
async def process_warm_day_of_month(message: Message, state: FSMContext):
    await handle_day_of_month(message, state, prefix='warm')


@router.callback_query(
    AddPlant.cold_freq_type, F.data.in_(FrequencyType.get_names())
)
async def process_cold_freq_type(callback: CallbackQuery, state: FSMContext):
    await handle_frequency_choice(callback, state, prefix='cold')


@router.callback_query(
    AddPlant.cold_freq_days, DayCallback.filter(F.action == 'select')
)
async def process_cold_weekly_days(
    callback: CallbackQuery, callback_data: DayCallback, state: FSMContext
):
    await handle_weekly_days(callback, callback_data, state, prefix='cold')


@router.callback_query(
    AddPlant.cold_freq_days, DayCallback.filter(F.action == 'done')
)
async def process_cold_weekly_done(callback: CallbackQuery, state: FSMContext):
    await handle_weekly_done(callback, state, prefix='cold')


@router.callback_query(
    AddPlant.cold_freq_day, DayCallback.filter(F.action == "select")
)
async def process_cold_biweekly_day(
    callback: CallbackQuery, callback_data: DayCallback, state: FSMContext
):
    await handle_biweekly_day(callback, callback_data, state, prefix='cold')


@router.message(AddPlant.cold_freq_day_of_month)
async def process_cold_day_of_month(message: Message, state: FSMContext):
    await handle_day_of_month(message, state, prefix='cold')


@router.message(AddPlant.fertilizing_start, TextRequiredFilter(), DateFilter())
async def process_fertilizing_start(
    message: Message, state: FSMContext, day: int, month: int
):
    """Process the start date of fertilizing."""
    await state.update_data(fertilizing_start={'day': day, 'month': month})
    await message.answer(
        add_plant.ASK_FERTILIZING_PERIOD_END_MSG,
        reply_markup=get_cancel_kb(back=True),
    )
    await set_next_state(state, AddPlant.fertilizing_end)


@router.message(AddPlant.fertilizing_end, TextRequiredFilter(), DateFilter())
async def process_fertilizing_stop(
    message: Message, state: FSMContext, day: int, month: int
):
    """Process the end date of fertilizing."""
    state_data = await state.get_data()
    fertilizing_start = state_data.get('fertilizing_start')

    if fertilizing_start and (
        (month < fertilizing_start['month'])
        or (
            month == fertilizing_start['month']
            and day < fertilizing_start['day']
        )
    ):
        await message.answer(add_plant.INVALID_END_DATE_MSG)
        return

    await state.update_data(fertilizing_end={'day': day, 'month': month})

    await message.answer(
        add_plant.ASK_FERTILIZING_FREQUENCY_MSG,
        reply_markup=frequency_type_kb(
            *FertilizingType.get_texts_and_callbacks()
        ),
    )
    await set_next_state(state, AddPlant.fertilizing_frequency_type)


@router.callback_query(
    AddPlant.fertilizing_frequency_type,
    F.data.in_(FertilizingType.get_names()),
)
async def process_fertilizing_frequency_type(
    callback: CallbackQuery, state: FSMContext
):
    """Process the fertilizing frequency type."""
    fertilizing_type = FertilizingType[callback.data]

    await state.update_data(fertilizing_frequency_type=fertilizing_type.value)

    cfg = FERTILIZING_INTERVAL_CONFIG[callback.data]
    message = add_plant.ASK_FERTILIZING_INTERVAL_MESSAGE.format(
        interval=cfg['interval_text']
    )

    await callback.message.answer(
        message, reply_markup=get_cancel_kb(back=True)
    )
    await set_next_state(state, cfg['state'])
    await callback.answer()


@router.message(
    F.text.isdigit(),
    StateFilter(
        AddPlant.fertilizing_every_n_days,
        AddPlant.fertilizing_every_n_weeks,
        AddPlant.fertilizing_every_n_months,
    ),
)
async def process_fertilizing_interval(message: Message, state: FSMContext):
    """Обрабатывает ввод числа для удобрения."""
    value = int(message.text)
    if value <= 0:
        await message.answer(NO_POSITIVE_INT_MSG)
        return

    state_data = await state.get_data()
    state_data['user_id'] = message.from_user.id
    state_data['fertilizing_frequency'] = value
    await save_plant(plant_data=state_data, is_fert=True)
    await message.answer('Растение добавлено.', reply_markup=get_main_kb())

    await state.clear()
