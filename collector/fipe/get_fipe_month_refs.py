import requests
import os
import json
from functools import lru_cache

from collector.fipe.constants import Urls
from collector.logger import get_logger


logger = get_logger("FipeMonthRefs")


def get_fipe_month_refs() -> dict[str, str]:
    try:
        response = requests.get(Urls.FIPE_TABLE_REFERENCES)
        response.raise_for_status()
        data = response.json()
        month_refs = {
            item["month"]: item["code"] for item in data
        }
        logger.info(f"Fetched {len(month_refs)} FIPE month references.")
        return month_refs
    except requests.RequestException as e:
        logger.error(f"Error fetching FIPE month references: {e}")
        return {}


def check_and_update_fipe_month_refs(file_path: str = "fipe_month_refs.json") -> None:
    logger.info("Fetching FIPE month references...")
    month_refs = get_fipe_month_refs()
    if month_refs:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(month_refs, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved FIPE month references to {file_path}")


@lru_cache(maxsize=128)
def _months_codes() -> dict[str, str]:
    try:
        with open("fipe_month_refs.json", "r", encoding="utf-8") as f:
            month_refs = json.load(f)
        return month_refs
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error reading FIPE month references: {e}")
        return {}


@lru_cache(maxsize=128)
def get_month_code(month: str, file_path: str = "fipe_month_refs.json") -> str | None:
    if not os.path.exists(file_path):
        check_and_update_fipe_month_refs(file_path)
    return _months_codes().get(month)
