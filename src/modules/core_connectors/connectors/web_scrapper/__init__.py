"""Коннектор daemon-web-scrapper: тонкий клиент к демону + модели параметров запросов."""

from src.modules.core_connectors.connectors.web_scrapper.connector import WebScrapperConnector
from src.modules.core_connectors.connectors.web_scrapper.params import (
    WebScrapperScrapBatchParams,
)

__all__ = [
    "WebScrapperConnector",
    "WebScrapperScrapBatchParams",
]
