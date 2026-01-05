from enum import StrEnum


class Urls(StrEnum):
    FIPE_CODES = "https://www.tabelafipebrasil.com/fipe/carros"
    BR_API = "https://brasilapi.com.br/api"
    BR_API_FIPE_FILTER = "/fipe/preco/v1/{fipe_code}?tabela_referencia={tabela}"
    BR_API_FIPE_GENERAL = "/fipe/preco/v1/{fipe_code}"
    FIPE_WEBPAGE = "https://veiculos.fipe.org.br"
    FIPE_TABLE_REFERENCES = "https://parallelum.com.br/fipe/api/v2/references"


