from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class AddPlant(StatesGroup):
    name = State()
    description = State()
    image = State()
    warm_start = State()
    warm_end = State()
    warm_freq_type = State()
    warm_frequency = State()
    warm_freq_days = State()
    warm_freq_day = State()
    warm_freq_day_of_month = State()
    cold_freq_type = State()
    cold_frequency = State()
    cold_freq_days = State()
    cold_freq_day = State()
    cold_freq_day_of_month = State()
    cold_frequency = State()
    fertilizing_start = State()
    fertilizing_end = State()
    fertilizing_frequency_type = State()
    fertilizing_every_n_days = State()
    fertilizing_every_n_weeks = State()
    fertilizing_every_n_months = State()
    skipped = State()


class DeletePlant(StatesGroup):
    name = State()


class PlantInfo(StatesGroup):
    name = State()


async def set_next_state(state: FSMContext, next_state):
    current_state = await state.get_state()
    state_data = await state.get_data()
    history = state_data.get('history', [])
    if current_state:
        history.append(current_state)
    await state.update_data(history=history)
    await state.set_state(next_state)
