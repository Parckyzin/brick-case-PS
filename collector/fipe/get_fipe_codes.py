from logging import Logger
from cloudscraper import CloudScraper
from requests import Response
from pathlib import Path
from selectolax.parser import HTMLParser, Node

from collector.fipe.constants import Urls
from collector.logger import get_logger

logger: Logger = get_logger("FIPE_Codes")


def get_fipe_codes() -> list[str]:
    response: Response = CloudScraper().get(Urls.FIPE_CODES)
    response.raise_for_status()

    html: HTMLParser = HTMLParser(response.text)
    elements: list[Node] = html.css("*[title^='Tabela FIPE']")

    if not elements:
        return []

    return [
        text
        for element in elements
        if (text := (element.text() or "").strip())
        and text.replace("-", "").strip().isdigit()
        and "-" in text
    ]


def check_fipe_codes_file() -> None:
    if not Path("fipe_codes.txt").exists():
        logger.info("Fetching FIPE codes...")
        codes = get_fipe_codes()
        with open("fipe_codes.txt", "w", encoding="utf-8") as f:
            for code in codes:
                f.write(f"{code}\n")
        logger.info(f"Saved {len(codes)} FIPE codes to fipe_codes.txt")
