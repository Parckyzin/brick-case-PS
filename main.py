import asyncio
import re

from pprint import pprint

from collector.logger import get_logger
from collector.fipe.get_fipe_codes import check_fipe_codes_file
from collector.fipe.car_data_extractor import CarDataExtractor


check_date_regex = r"^(0[1-9]|1[0-2])-(19|20)\d\d$"


def _check_date_format(date_str: str) -> bool:
    return re.match(check_date_regex, date_str) is not None


async def run_extraction(fipe_code: str, car_year: int, initial_date: str, final_date: str):
    async with CarDataExtractor() as extractor:
        return await extractor.extract_car_data(
            fipe_code=fipe_code,
            car_year=car_year,
            initial_date=initial_date,
            final_date=final_date
        )

if __name__ == "__main__":
    logger = get_logger("Main")
    logger.info("Checking FIPE codes file...")
    check_fipe_codes_file()
    logger.info("FIPE codes file check complete.")
    
    logger.warning("Make sure to enter valid CAR FIPE codes and dates.")
    logger.warning("This will not work with motorcycle or truck FIPE codes.")

    fipe_code = input("Enter a FIPE code (e.g., 001234-5): ").strip()
    car_year = int(input("Enter the car model year (e.g., 2020): ").strip())
    while True:
        initial_date_input = input("Enter the initial date in MM-YYYY format (e.g., 05-2023): ").strip()
        final_date_input = input("Enter the final in MM-YYYY format (e.g., 12-2023): ").strip()
        if not _check_date_format(initial_date_input) or not _check_date_format(final_date_input):
            logger.error("Invalid date format. Please use MM-YYYY format.")
        elif int(initial_date_input.split("-")[-1]) < 2001:
            logger.error("Initial date year must be 2001 or later.")
        else:
            break
    data = asyncio.run(run_extraction(fipe_code, car_year, initial_date_input, final_date_input))

    logger.info(f"Extracted data for {fipe_code}:")
    pprint(data)
