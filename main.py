import asyncio
import datetime
import re
import time

from pprint import pprint

from collector.logger import get_logger
from collector.fipe.get_fipe_codes import check_fipe_codes_file
from collector.fipe.car_data_extractor import CarDataExtractor
from collector.fipe.car_data_extractor_req import CarDataExtractorReq
from collector.settings import Settings


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
    
    if Settings.CLIENT == "playwright":
        
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
    
    else:
        start = time.time()
        # Example FIPE codes and years for extraction
        cars_to_extract = [
            ("008096-9", 2001),
            ("008097-7", 2001),
            ("008138-8", 2013),
            ("008144-2", 2011),
            ("008155-8", 2016),
            ("005209-4", 2006)
        ]
        initial_date = "01-2001"
        final_date = "12-2025"
        extractor = CarDataExtractorReq()
        all_data = extractor.extract_multiple_cars_data(
            fipe_codes_and_ref_dates=cars_to_extract,
            initial_date=initial_date,
            final_date=final_date,
            max_workers=301
        )
        all_data_len = sum(len(v) for v in all_data.values())
        end = time.time()
        with open("extracted_cars_data.json", "w", encoding="utf-8") as f:
            import json
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info("Extracted data saved to extracted_car_data.json")
        logger.info(f"Total extraction time: {end - start:.2f} seconds")
        logger.info(f"Extracted data for {len(all_data)} cars with a total of {all_data_len} entries.")
