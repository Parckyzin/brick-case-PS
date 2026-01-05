# Settings example, I don't wanna use pydantic for this case, so it's not going to be a perfect settings file

from typing import Literal


class Settings:
    HEADLESS: bool = False
    CLIENT: Literal["requests", "playwright"] = "requests"
