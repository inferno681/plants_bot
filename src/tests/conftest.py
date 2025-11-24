import asyncio

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from bot.models import Plant, User


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def beanie_client():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client['plants_bot_tests'],
        document_models=[User, Plant],
    )
    yield client
    client.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(beanie_client):
    await Plant.delete_all()
    await User.delete_all()
    yield
