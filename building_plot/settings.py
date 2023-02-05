from pydantic import BaseSettings


class Settings(BaseSettings):
    mongo_connection_string: str = "mongodb://admin:pass@localhost:27017/"


settings = Settings()
