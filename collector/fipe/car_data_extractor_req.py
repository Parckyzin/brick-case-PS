import datetime
from typing import Optional

import requests
import time

from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


from collector.logger import get_logger
from collector.fipe.constants import Urls

from collector.fipe.get_fipe_month_refs import get_month_code


class CarDataExtractorReq:
    def __init__(self):
        self.urls = Urls
        self._logger = get_logger("CarDataExtractorReq")
        self._months: dict[str, str] = {
            "01": "janeiro",
            "02": "fevereiro",
            "03": "março",
            "04": "abril",
            "05": "maio",
            "06": "junho",
            "07": "julho",
            "08": "agosto",
            "09": "setembro",
            "10": "outubro",
            "11": "novembro",
            "12": "dezembro",
        }
        self._session = requests.Session()
    
    def _request_fipe_data(self, fipe_code: str, tabela: str) -> requests.Response:
        url = self.urls.BR_API + self.urls.BR_API_FIPE_FILTER.format(
            fipe_code=fipe_code,
            tabela=tabela
        )
        response = self._session.get(url)
        return response

    def get_fipe_data(
            self,
            fipe_code: str,
            tabela: str,
            car_year: Optional[int],
            max_retries: int = 3,
            backoff_factor: float = 0.5
    ) -> dict:
    
        for attempt in range(max_retries):
            try:
                response = self._request_fipe_data(fipe_code, tabela)
            except requests.RequestException:
                if attempt == max_retries - 1:
                    return {}
                time.sleep(backoff_factor * (2 ** attempt))
                continue
    
            if response.status_code == 200:
                try:
                    return self._parse_data(response.json(), car_year) if car_year else response.json()
                except ValueError:
                    return {}
    
            if response.status_code == 400:
                self._logger.warning(f"{response.json()} for FIPE code {fipe_code} and tabela {tabela}")
                return {}
        
            if attempt < max_retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))
    
        return {}
    
    @staticmethod
    def _parse_data(data: list[dict], car_year: int) -> dict[str, str | int]:
        if not data:
            return {}
        parsed = {k: v.strip() if isinstance(v, str) else v for k, v in data[0].items()}
        parsed["ano_modelo"] = car_year
        return parsed

    def extract_car_data(
            self,
            fipe_code: str,
            car_year: Optional[int],
            initial_date: str,
            final_date: str,
            max_workers: int = 10
    ) -> dict:
        initial_datetime = datetime.datetime.strptime(initial_date, "%m-%Y")
        final_datetime = datetime.datetime.strptime(final_date, "%m-%Y")
        date_interval = [
            initial_datetime + relativedelta(months=i)
            for i in range((final_datetime.year - initial_datetime.year) * 12 + final_datetime.month - initial_datetime.month + 1)
        ]
    
        car_data: dict[str, dict[str, str | int]] = {}
        if not date_interval:
            return car_data
    
        def _worker(date: datetime.datetime):
            parsed_date = f"{self._months[date.strftime('%m')]}/{date.year}"
            tabela_ref = get_month_code(parsed_date)
            if not tabela_ref:
                self._logger.error(f"Could not find tabela reference for date {parsed_date}")
                return None
            data = self.get_fipe_data(fipe_code, str(tabela_ref), car_year)
            if data:
                formatted_date = date.strftime("%m/%Y")
                return formatted_date, data
            return None
    
        workers = min(max_workers, len(date_interval))
        self._logger.info(f"using {workers} workers for extraction")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_worker, d): d for d in date_interval if car_year is None or d.year >= car_year}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    formatted_date, data = result
                    car_data[formatted_date] = data
                    self._logger.info(f"Extracted data for {fipe_code} - {formatted_date}")
    
        return car_data
    
    def extract_multiple_cars_data(
            self,
            fipe_codes_and_ref_dates: list[tuple[str, Optional[int]]],
            initial_date: str,
            final_date: str,
            max_workers: int = 10
    ) -> dict[str, dict[str, dict[str, str | int]]]:
        all_data: dict[str, dict[str, dict[str, str | int]]] = {}
        for fipe_code, car_year in fipe_codes_and_ref_dates:
            car_data = self.extract_car_data(
                fipe_code=fipe_code,
                car_year=car_year,
                initial_date=initial_date,
                final_date=final_date,
                max_workers=max_workers
            )
            all_data[fipe_code] = car_data
        return all_data

