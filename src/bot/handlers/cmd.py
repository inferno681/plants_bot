from logging import getLogger

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from bot.constants import ALL_STATES, BACK, CANCEL, SKIP, STATE_MESSAGES
from bot.constants.error import SKIP_ACTION_ERROR_MSG, WRONG_FSM_CLASS_ERROR
from bot.constants.message import (
    BACK_TO_PREV_STEP_MSG,
    DESCRIPTION_SKIP_MSG,
    FERTILIZING_SKIP_MSG,
    FIRST_STEP_MSG,
    PHOTO_SKIP_MSG,
)
from bot.keyboard import get_cancel_kb, get_main_kb
from bot.log_message import BACK_ERROR_LOG
from bot.models import User
from bot.states import AddPlant
from bot.utils import save_plant, storage_service
from bot.utils.telegram import require_user

router = Router(name='cmd_router')
logger = getLogger(__name__)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Start command handler."""
    tg_user = require_user(message.from_user)
    user = await User.find_one(User.user_id == tg_user.id)
    if user is None:
        user = User(
            user_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            full_name=tg_user.full_name,
            language_code=tg_user.language_code,
            is_premium=getattr(tg_user, 'is_premium', None),
        )
        await user.insert()
    else:
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        user.username = tg_user.username
        user.full_name = tg_user.full_name
        user.language_code = tg_user.language_code
        user.is_premium = getattr(tg_user, 'is_premium', None)
        await user.save()
    await message.answer(
        f'Привет, {hbold(tg_user.full_name)}!',
        reply_markup=get_main_kb(),
    )


@router.message(F.text == CANCEL)
async def cancel_handler(message: Message, state: FSMContext):
    """Cancel handler."""
    state_data = await state.get_data()
    if 'storage_key' in state_data:
        await storage_service.delete_file(state_data.get('storage_key'))
    await state.clear()
    await message.answer(CANCEL, reply_markup=get_main_kb())


@router.message(F.text == SKIP)
async def skip_handler(message: Message, state: FSMContext):
    """Skip handler."""
    current_state = await state.get_state()
    if current_state == AddPlant.description:
        await state.update_data({'description': None})
        await message.answer(
            DESCRIPTION_SKIP_MSG,
            reply_markup=get_cancel_kb(back=True, skip=True),
        )
        await state.set_state(AddPlant.image)

    elif current_state == AddPlant.image:
        await state.update_data({'image': None})
        await message.answer(
            PHOTO_SKIP_MSG,
            reply_markup=get_cancel_kb(back=True),
        )
        await state.set_state(AddPlant.warm_start)

    elif current_state == AddPlant.fertilizing_start:
        state_data = await state.get_data()
        state_data['user_id'] = require_user(message.from_user).id
        await save_plant(plant_data=state_data, is_fert=False)
        await message.answer(
            FERTILIZING_SKIP_MSG,
            reply_markup=get_main_kb(),
        )
        await state.clear()


@router.message(F.text == BACK)
async def back_handler(message: Message, state: FSMContext):
    """Back handler."""
    state_data = await state.get_data()
    history = state_data.get('history', [])
    if not history:
        await message.answer(text=FIRST_STEP_MSG, reply_markup=get_cancel_kb())
        return

    previous_state = history.pop()
    await state.set_state(previous_state)
    await state.update_data({'history': history})
    state_data = await state.get_data()

    try:
        class_name, state_name = previous_state.split(':', 1)

        fsm_class = ALL_STATES.get(class_name)
        if not fsm_class:
            raise ValueError(
                WRONG_FSM_CLASS_ERROR.format(class_name=class_name)
            )

        new_state = getattr(fsm_class, state_name)
    except Exception as exc:
        await message.answer(SKIP_ACTION_ERROR_MSG)
        logger.info(BACK_ERROR_LOG, exc)

        return

    await state.set_state(new_state)
    await message.answer(
        STATE_MESSAGES.get(new_state, BACK_TO_PREV_STEP_MSG),
        reply_markup=get_cancel_kb(back=True if history else False),
    )
