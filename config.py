from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env файлынан оқиды
    model_config = SettingsConfigDict(env_file=".env")

    # Дерекқор мекенжайы — міндетті өріс, болмаса сервер іске қосылмайды
    database_url: str

    # SQL логын қосу/өшіру (debug үшін) — әдепкі өшірулі
    sql_echo: bool = False


# Барлық жерде осы объектіні импорттаймыз
settings = Settings()
