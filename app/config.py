"""Konfiguracja aplikacji wczytywana z pliku .env.

JWT_SECRET jest wymagany: bez niego serwer odmówi startu z jasnym błędem.
To celowe — cichy fallback na domyślny sekret byłby luką bezpieczeństwa
(każdy mógłby podrobić token).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str
    token_expire_days: int = 30  # po tylu dniach token wygasa (trzeba się zalogować)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
