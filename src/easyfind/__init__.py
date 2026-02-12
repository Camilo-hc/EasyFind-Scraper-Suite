"""
EasyFind - Suite de Comparación de Precios Automatizada.

Sistema automatizado de comparación de precios para productos eléctricos
de proveedores chilenos. Combina scraping web asíncrono con coincidencia
difusa de doble precisión.

Autor: Camilo Hernández
"""

__version__ = "1.0.0"

from .config import Config
from .utils import Utils
from .store_strategies import StoreStrategies
from .content_parser import ContentParser
from .web_scraper import WebScraper
from .data_manager import DataManager
from .engine import main, procesar_tarea_segura
