from enum import StrEnum

class Urls(StrEnum):
    FIPE_CODES = "https://www.tabelafipebrasil.com/fipe/carros"
    BR_API = "https://brasilapi.com.br/api"
    BR_API_FIPE_PATH = "/fipe/preco/v1/{fipe_code}?tabela_referencia={tabela}"
    FIPE_WEBPAGE = "https://veiculos.fipe.org.br"

