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
from config import config

router = Router(name='delete_plant_router')


@router.message(F.text == DELETE_PLANT)
async def cmd_delete_good(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
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
    await state.update_data(pages=pages, current_page=current_page)
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
    await callback.message.delete()
    await callback.message.answer(
        DELETE_CANCELED_MSG, reply_markup=get_main_kb()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    DeletePlant.name, ChoicePlantCallback.filter(F.action == Action.prev)
)
async def prev_handler(callback: CallbackQuery, state: FSMContext):
    pagination_data = await state.get_data()
    pages = pagination_data.get('pages', [])
    current_page = pagination_data.get('current_page', 0)
    current_page -= 1
    await state.update_data(current_page=current_page)
    plants = await Plant.get_documents_by_ids(
        callback.from_user.id, pages[current_page]
    )
    await callback.message.edit_reply_markup(
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
    pages = pagination_data.get('pages', [])
    current_page = pagination_data.get('current_page', 0)
    current_page += 1
    await state.update_data(current_page=current_page)
    plants = await Plant.get_documents_by_ids(
        callback.from_user.id, pages[current_page]
    )
    await callback.message.edit_reply_markup(
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

    await Plant.find_one(
        Plant.user_id == callback.from_user.id, Plant.name == plant_name
    ).delete_one()

    await callback.message.delete()
    await callback.message.answer(
        PLANT_DELETED_MESSAGE.format(plant_name=plant_name)
    )

    await state.clear()
    await callback.answer()
