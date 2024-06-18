import os
from click import get_app_dir

APP_NAME = "memotica"


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()

        return cls._instance

    def _initialize(self):
        environment = os.getenv("ENVIRONMENT", "production")
        if environment == "development":
            self.sqlite_url = "sqlite:///memotica.db"
            return

        self.app_dir = get_app_dir(app_name=APP_NAME)
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)

        self.sqlite_url = "sqlite:///" + os.path.join(self.app_dir, "memotica.db")
