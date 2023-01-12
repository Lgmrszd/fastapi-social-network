from enum import Enum

from pydantic import BaseSettings


class Environment(str, Enum):
    prod = "prod"
    dev = "dev"


class Settings(BaseSettings):
    sqlalchemy_database_url: str = "sqlite:///./sql_app.db"
    sqlalchemy_echo: bool = False
    env: Environment = Environment.dev
    secret_key: str = f"{'_not_a_secret_':x^64}"


settings = Settings()
