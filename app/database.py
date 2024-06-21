from motor.motor_asyncio import AsyncIOMotorClient

from .config import MONGODB_USER, MONGODB_PASSWORD, MONGODB_HOST, MONGODB_PORT, MONGODB_NAME, APP_NAME

mongodb_uri = f'mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/?authMechanism=DEFAULT'
database_name = APP_NAME + "_" + MONGODB_NAME


class MongoDB:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

mongodb = MongoDB(uri=mongodb_uri, db_name=database_name)