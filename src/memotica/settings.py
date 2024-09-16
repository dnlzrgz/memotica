from typing import Type, Tuple
from pathlib import Path
from click import get_app_dir
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

app_dir = Path(get_app_dir(app_name="memotica"))
config_file_path = app_dir / "config.toml"


class AppSettings(BaseModel):
    db_url: str = f"sqlite:///{app_dir / 'memotica.db'}"


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)

    model_config = SettingsConfigDict(toml_file=f"{app_dir / 'config.toml'}")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        app_dir.mkdir(parents=True, exist_ok=True)
        return (TomlConfigSettingsSource(settings_cls),)
