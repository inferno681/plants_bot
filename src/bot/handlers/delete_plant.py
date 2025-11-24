from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.callback import Action, ChoicePlantCallback
from bot.constants import (
    DELETE_PLANT,
    NO_PLANTS_MSG,
    PAGINATION_MESSAGE,
    PLANT_DELETED_MESSAGE,
)
from bot.constants.constants import DELETE_CANCELED_MSG
from bot.keyboard import get_keyboard_with_navigation, get_main_kb
from bot.models import Plant
from bot.states import DeletePlant
from bot.utils.telegram import require_message, require_user
from config import config

router = Router(name='delete_plant_router')

PAGES_KEY = 'pages'
CURRENT_PAGE_KEY = 'current_page'


@router.message(F.text == DELETE_PLANT)
async def cmd_delete_good(message: Message, state: FSMContext):
    user = require_user(message.from_user)
    telegram_id = user.id
    all_ids = await Plant.get_all_ids(telegram_id)

    if not all_ids:
        await message.answer(NO_PLANTS_MSG, reply_markup=get_main_kb())
        return

    page_size = config.service.page_size
    pages = [
        all_ids[i : i + page_size] for i in range(0, len(all_ids), page_size)
    ]
    current_page = 0

    plants = await Plant.get_documents_by_ids(telegram_id, pages[current_page])

    await state.set_state(DeletePlant.name)
    await state.update_data({PAGES_KEY: pages, CURRENT_PAGE_KEY: current_page})
    lines = [f'{plant.name} — {plant.last_watered_at}' for plant in plants]

    await message.answer(
        PAGINATION_MESSAGE.format(
            current_page=current_page + 1,
            pages=len(pages),
            lines='\n'.join(lines),
        ),
        reply_markup=get_keyboard_with_navigation(
            plants, current_page, len(pages), Action.delete
        ),
    )


@router.callback_query(
    DeletePlant.name, ChoicePlantCallback.filter(F.action == Action.cancel)
)
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    message = require_message(callback)
    await message.delete()
    await message.answer(DELETE_CANCELED_MSG, reply_markup=get_main_kb())
    await state.clear()
    await callback.answer()


@router.callback_query(
    DeletePlant.name, ChoicePlantCallback.filter(F.action == Action.prev)
)
async def prev_handler(callback: CallbackQuery, state: FSMContext):
    pagination_data = await state.get_data()
    pages = pagination_data.get(PAGES_KEY, [])
    current_page = pagination_data.get(CURRENT_PAGE_KEY, 0)
    current_page -= 1
    await state.update_data({CURRENT_PAGE_KEY: current_page})
    plants = await Plant.get_documents_by_ids(
        require_user(callback.from_user).id, pages[current_page]
    )
    message = require_message(callback)
    await message.edit_reply_markup(
        reply_markup=get_keyboard_with_navigation(
            plants, current_page, len(pages), Action.delete
        )
    )
    await callback.answer()


@router.callback_query(
    DeletePlant.name, ChoicePlantCallback.filter(F.action == Action.next)
)
async def next_handler(callback: CallbackQuery, state: FSMContext):
    pagination_data = await state.get_data()
    pages = pagination_data.get(PAGES_KEY, [])
    current_page = pagination_data.get(CURRENT_PAGE_KEY, 0)
    current_page += 1
    await state.update_data({CURRENT_PAGE_KEY: current_page})
    plants = await Plant.get_documents_by_ids(
        require_user(callback.from_user).id, pages[current_page]
    )
    message = require_message(callback)
    await message.edit_reply_markup(
        reply_markup=get_keyboard_with_navigation(
            plants, current_page, len(pages), Action.delete
        )
    )
    await callback.answer()


@router.callback_query(
    DeletePlant.name, ChoicePlantCallback.filter(F.action == Action.delete)
)
async def delete_handler(
    callback: CallbackQuery,
    callback_data: ChoicePlantCallback,
    state: FSMContext,
):
    plant_name = callback_data.name

    user = require_user(callback.from_user)
    await Plant.find_one(
        Plant.user_id == user.id, Plant.name == plant_name
    ).delete_one()

    message = require_message(callback)
    await message.delete()
    await message.answer(PLANT_DELETED_MESSAGE.format(plant_name=plant_name))

    await state.clear()
    await callback.answer()
