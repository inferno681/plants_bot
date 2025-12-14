import asyncio
from logging import getLogger

from aiogram import Bot
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pymongo import MongoClient

from bot.constants import JOB_ID, WATERING_SCHEDULED_MESSAGE
from bot.keyboard import watering_kb
from bot.log_message import (
    JOB_ADDED_LOG,
    JOB_EXISTS_LOG,
    MESSAGE_SEND_ERROR_LOG,
    PLANT_LIST_NOT_RECEIVED_LOG,
    SCHEDULER_START_FAILED_LOG,
    SCHEDULER_START_LOG,
    START_PRICE_UPDATE_LOG,
    WATERING_NOTIFICATIONS_SEND_RESULT,
)
from bot.models import Plant
from config import config

log = getLogger(__name__)


bot: Bot | None = None


def set_bot(bot_instance: Bot):
    """Set bot globally."""
    global bot
    bot = bot_instance


jobstores = {
    'default': MongoDBJobStore(
        client=MongoClient(config.mongo_url),
        database=config.mongodb.db,
        collection='jobs',
    )
}
scheduler = AsyncIOScheduler(jobstores=jobstores)


async def watering_notifications():
    """Price update job."""
    log.info(START_PRICE_UPDATE_LOG)

    plants = await Plant.find_to_water_today()
    if not plants:
        log.error(PLANT_LIST_NOT_RECEIVED_LOG)
        return

    tasks = [send_watering_notification(plant) for plant in plants]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for result in results if result is True)
    log.info(WATERING_NOTIFICATIONS_SEND_RESULT, success_count, len(plants))


async def send_watering_notification(plant: Plant) -> bool:
    """Send watering notification."""
    if bot is None:
        log.error('Bot instance is not set.')
        return False

    plant_id = plant.id
    if plant_id is None:
        log.error('Plant id is missing for watering notification.')
        return False

    is_fert = plant.sync_watering_and_fertilizing()
    text = WATERING_SCHEDULED_MESSAGE.format(
        fert='и удобрить' if is_fert else '', name=plant.name
    )

    params = dict(
        chat_id=plant.user_id,
        parse_mode='HTML',
        reply_markup=watering_kb(idx=plant_id, is_fertilized=is_fert),
    )
    try:
        if plant.image:
            await bot.send_photo(**params, caption=text, photo=plant.image)
        else:
            await bot.send_message(**params, text=text)
    except Exception as exc:
        log.error(MESSAGE_SEND_ERROR_LOG, exc)
    return True


async def start_scheduler():
    """Start the scheduler and add the job if it doesn't exist."""
    try:
        if not scheduler.running:
            scheduler.start()
            log.info(SCHEDULER_START_LOG)
        if scheduler.get_job(JOB_ID):
            log.info(JOB_EXISTS_LOG, JOB_ID)
        else:
            scheduler.add_job(
                watering_notifications,
                trigger='cron',
                hour=16,
                minute=50,
                id=JOB_ID,
                replace_existing=False,
            )
            log.info(JOB_ADDED_LOG, JOB_ID)
    except Exception as exc:
        log.error(SCHEDULER_START_FAILED_LOG, exc)
