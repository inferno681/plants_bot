from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery
from beanie import PydanticObjectId

from bot.keyboard import PlantActionCallback
from bot.models import Plant
from bot.utils.telegram import require_message

router = Router(name='notification_router')


@router.callback_query(PlantActionCallback.filter())
async def handle_watering_callback(
    callback: CallbackQuery, callback_data: PlantActionCallback
):
    plant = await Plant.get(PydanticObjectId(callback_data.idx))
    if not plant:
        await callback.answer("❌ Растение не найдено", show_alert=True)
        return
    plant.last_watered_at = date.today()
    plant.next_watering_date()
    if callback_data.is_fertilized:
        plant.last_fertilized_at = date.today()
        plant.next_fertilizing_date()
    await plant.save()
    message = require_message(callback)
    await message.edit_caption(
        caption=f'Растение {plant.name} полито', reply_markup=None
    )
    await callback.answer()
