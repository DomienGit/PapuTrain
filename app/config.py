"""Konfiguracja aplikacji wczytywana z pliku .env.

JWT_SECRET jest wymagany: bez niego serwer odmówi startu z jasnym błędem.
To celowe — cichy fallback na domyślny sekret byłby luką bezpieczeństwa
(każdy mógłby podrobić token).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str
    token_expire_days: int = 30  # po tylu dniach token wygasa (trzeba się zalogować)
    gemini_api_key: str = ""  # pusty = generowanie planów wyłączone (jasny błąd w API)
    # Kolejność modeli przy wyczerpaniu darmowego limitu (429): API próbuje po kolei.
    gemini_models: str = "gemini-3.6-flash,gemini-3-flash-preview,gemini-3.5-flash-lite,gemini-3.1-flash-lite"

    @property
    def gemini_models_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_models.split(",") if m.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
