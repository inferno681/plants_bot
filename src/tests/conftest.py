from __future__ import annotations

import asyncio
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

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
async def clean_db(beanie_client):  # noqa: PT004
    for model in (Plant, User):
        await model.delete_all()
    yield
