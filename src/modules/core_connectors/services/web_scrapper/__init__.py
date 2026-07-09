"""Коннектор daemon-web-scrapper: тонкий клиент к демону + модели параметров запросов."""

from src.modules.core_connectors.services.web_scrapper.gateway import WebScrapperGateway
from src.modules.core_connectors.services.web_scrapper.params import (
    WebScrapperScrapBatchParams,
)

__all__ = [
    "WebScrapperGateway",
    "WebScrapperScrapBatchParams",
]
