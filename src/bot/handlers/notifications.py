from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery
from beanie import PydanticObjectId

from bot.keyboard import PlantActionCallback
from bot.models import Plant

router = Router(name='notification_router')


@router.callback_query(PlantActionCallback.filter())
async def handle_watering_callback(
    callback: CallbackQuery, callback_data: PlantActionCallback
):
    plant = await Plant.get(PydanticObjectId(callback_data.idx))
    if not plant:
        await callback.answer("❌ Растение не найдено", show_alert=True)
        return
    plant.next_watering_date()
    plant.last_watered_at = date.today()
    if callback_data.is_fertilized:
        plant.next_fertilizing_date()
        plant.last_fertilized_at = date.today()
    await plant.save()
    assert callback.message is not None
    await callback.message.edit_caption(
        caption=f'Растение {plant.name} полито', reply_markup=None
    )
    await callback.answer()
