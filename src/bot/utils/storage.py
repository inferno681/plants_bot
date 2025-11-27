from contextlib import asynccontextmanager
from logging import getLogger
from uuid import uuid4

import aiohttp
from aioboto3 import Session  # type: ignore

from bot.log_message import FILE_DOWNLOAD_ERROR_LOG, STORAGE_UTIL_STARTED_LOG
from config import config

TG_URL = 'https://api.telegram.org/file/bot{token}/{file_path}'
STATUS_OK = 200


class S3StorageService:
    """Service for interacting with S3 storage using aioboto3."""

    def __init__(self):
        """S3StorageService initialization."""
        self.bucket = config.storage.bucket
        self.session = Session()
        self.endpoint_url = config.storage.endpoint_url
        self.aws_access_key = config.secrets.aws_access_key.get_secret_value()
        self.aws_secret_key = config.secrets.aws_secret_key.get_secret_value()
        self.log = getLogger(__name__)

        self.log.info(STORAGE_UTIL_STARTED_LOG)

    async def upload_file(self, storage_key: str, file_bytes: bytes):
        """Upload a file to S3 storage."""
        async with self._s3_client() as s3:
            await s3.put_object(
                Bucket=self.bucket, Key=storage_key, Body=file_bytes
            )

    async def delete_file(self, storage_key: str):
        """Delete a file from S3 storage."""
        async with self._s3_client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=storage_key)

    async def delete_files(self, storage_keys: list[str]):
        """Delete files from S3 storage."""
        async with self._s3_client() as s3:
            await s3.delete_objects(
                Bucket=self.bucket,
                Delete={
                    'Objects': [{'Key': key} for key in storage_keys],
                    'Quiet': True,
                },
            )

    async def upload_telegram_file(
        self,
        file_path: str,
        user_id: int,
    ) -> str | None:
        """
        Download file from Telegram and upload it to S3.

        Returns S3 storage key.
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                TG_URL.format(
                    token=config.secrets.bot_token.get_secret_value(),
                    file_path=file_path,
                )
            ) as resp:
                if resp.status != STATUS_OK:
                    self.log.info(FILE_DOWNLOAD_ERROR_LOG, user_id)
                    return None
                file_bytes = await resp.read()

        key = f'{user_id}/{uuid4()}.{file_path.split('.')[-1]}'

        await self.upload_file(key, file_bytes)

        return key

    @asynccontextmanager
    async def _s3_client(self):
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.aws_secret_key,
            aws_access_key_id=self.aws_access_key,
        ) as s3:
            yield s3


storage_service = S3StorageService()
