from aiogram import F, Router
from aiogram.types import Message

from bot.constants import CHECK_PLANTS
from bot.constants.check_plant import PLANT_INFO_LINE
from bot.keyboard import get_main_kb
from bot.models import Plant
from bot.utils.telegram import require_user

router = Router(name='check_plants_router')


@router.message(F.text == CHECK_PLANTS)
async def cmd_check_all(message: Message) -> None:
    """Check all plants handler."""
    user = require_user(message.from_user)
    plants = await Plant.find_many(Plant.user_id == user.id).to_list()
    if not plants:
        await message.answer(
            'Растения не отслеживаются', reply_markup=get_main_kb()
        )
        return

    lines = '\n'.join(
        PLANT_INFO_LINE.format(
            pos=index,
            name=plant.name,
            watering=plant.last_watered_at,
            fertilizing=plant.last_fertilized_at,
        )
        for index, plant in enumerate(plants, start=1)
    )
    await message.answer(lines, reply_markup=get_main_kb())
