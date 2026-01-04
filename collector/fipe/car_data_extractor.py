import datetime
from logging import Logger
from dateutil.relativedelta import relativedelta

from playwright.async_api import async_playwright, Page, Browser, TimeoutError

from collector.fipe.constants import Urls
from collector.logger import get_logger

from collector.settings import Settings

date_dict: dict[str, str] = {
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


def _parse_date(formatted_date: str) -> str:
    month, year = formatted_date.split("/")
    month_name = date_dict.get(month)
    if month_name is None:
        raise ValueError(f"Invalid month: {month}")
    return f"{month_name}/{year}"


class CarDataExtractor:
    def __init__(self) -> None:
        self.logger: Logger = get_logger("CarDataExtractor")

    async def _click_middle_screen(self) -> None:
        await self.page.mouse.click(960, 540)
        
    async def _wait_for_selector(self, selector: str, timeout: int = 3000) -> bool:
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except TimeoutError:
            return False
        except Exception as e:
            self.logger.error(f"Error while waiting for selector {selector}: {e}")
            return False
    
    async def _format_extracted_data(self) -> dict[str, str | float]:
        div = await self.page.query_selector("#resultadocarroCodigoFipe")
        if div is None:
            self.logger.error("Could not find result data container.")
            return {}
        table = await div.query_selector("table")
        if table is None:
            self.logger.error("Could not find result data table.")
            return {}
        rows = await table.query_selector_all("tr")
        data: dict[str, str | int] = {}
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) != 2:
                continue
            key = (await cols[0].inner_text()).strip().rstrip(":")
            value = (await cols[1].inner_text()).strip()
            match key:
                case "Mês de referência":
                    data["reference_month"] = value
                case "Código Fipe":
                    data["fipe_code"] = value
                case "Marca":
                    data["brand"] = value
                case "Modelo":
                    data["model"] = value
                case "Ano Modelo":
                    data["model_year"] = value
                case "Autenticação":
                    data["authentication"] = value
                case "Preço Médio":
                    data["average_price"] = float(value.replace("R$ ", "").replace(".", "").replace(",", "."))
                case _:
                    continue
        return data
                
    async def _select_car_code_and_year(self, fipe_code: str, car_year: int) -> bool:
        await self.page.fill('#selectCodigocarroCodigoFipe', fipe_code)
        await self._click_middle_screen()
        if await self._wait_for_selector(".modal.alert"):
            self.logger.warning(f"FIPE code {fipe_code} not found.")
            await self.page.click('.btnClose')
            return False
        select = await self.page.query_selector("#selectCodigoAnocarroCodigoFipe_chosen a")
        if select is None:
            self.logger.error("Could not find year selection dropdown.")
        await select.click()
        opt = await self.page.query_selector(f'#selectCodigoAnocarroCodigoFipe_chosen li:text-matches("^{car_year}")')
        if opt is None:
            self.logger.error(f"Could not find year option for year {car_year}.")
        await opt.click()
        return True

    async def _select_reference_date(self, formated_date: str) -> bool:
        select = await self.page.query_selector('#selectTabelaReferenciacarroCodigoFipe_chosen a')
        if select is None:
            self.logger.error("Could not find reference date dropdown.")
            return False
        await select.click()
        if not await self._wait_for_selector("#selectTabelaReferenciacarroCodigoFipe_chosen .active-result"):
            self.logger.error("Reference date options did not load.")
            return False
        option = await self.page.query_selector(f"#selectTabelaReferenciacarroCodigoFipe_chosen .active-result:text-matches('^{formated_date} ')")  # noqa: E501
        if option is None:
            self.logger.warning(f"Reference date {formated_date} not found.")
            return False
        await option.click()
        return True

    async def extract_car_data(
            self,
            fipe_code: str,
            car_year: int,
            initial_date: str,
            final_date: str,
    ) -> dict[str, dict[str, str | float]]:
        
        initial_datetime = datetime.datetime.strptime(initial_date, "%m-%Y")
        final_datetime = datetime.datetime.strptime(final_date, "%m-%Y")
        date_interval = [
            initial_datetime + relativedelta(months=i)
            for i in range((final_datetime.year - initial_datetime.year) * 12 + final_datetime.month - initial_datetime.month + 1)
        ]
        
        car_data: dict[str, dict[str, str | int]] = {}
        await self.page.goto(Urls.FIPE_WEBPAGE)
        await self.page.click('a[data-category="indices_indicadores_subitens"]')
        
        for date in date_interval:
            formatted_date = date.strftime("%m/%Y")
            await self.page.click('a[data-aba="Abacarro-codigo"]')
            if not await self._select_car_code_and_year(fipe_code, car_year):
                continue
            if not await self._select_reference_date(_parse_date(formatted_date)):
                continue
            await self.page.click('#buttonPesquisarcarroPorCodigoFipe')
            car_data[formatted_date] = await self._format_extracted_data()
            self.logger.info(f"Extracted data for {fipe_code} - {formatted_date}")

        return car_data

    async def __aenter__(self) -> "CarDataExtractor":
        self.playwright = await async_playwright().start()
        self.browser: Browser = await self.playwright.chromium.launch(headless=Settings.HEADLESS)
        self.page: Page = await self.browser.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.page.close()
        await self.browser.close()
        await self.playwright.stop()
