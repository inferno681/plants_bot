from aiogram import Router

from bot.handlers.add_plant import router as add_plant_router
from bot.handlers.check_plant import router as check_one
from bot.handlers.check_plants import router as check_plants
from bot.handlers.cmd import router as cmd_router
from bot.handlers.delete_plant import router as delete_plant
from bot.handlers.notifications import router as notification_router

main_router = Router(name='main_router')
main_router.include_router(cmd_router)
main_router.include_router(add_plant_router)
main_router.include_router(notification_router)
main_router.include_router(check_plants)
main_router.include_router(delete_plant)
main_router.include_router(check_one)
