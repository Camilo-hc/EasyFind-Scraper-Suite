"""
EasyFind - Motor de Scraping y Comparación de Precios.

Este archivo es un shim de compatibilidad que re-exporta todas
las clases y funciones desde el paquete reorganizado en src/easyfind/.

La GUI importa 'import EasyFind' y luego llama EasyFind.main(),
por lo que este shim mantiene esa interfaz pública intacta.
"""

import sys
import os

# Agregar src/ al path para encontrar el paquete easyfind
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from easyfind.config import Config, TASA_DOLAR
from easyfind.utils import Utils
from easyfind.store_strategies import StoreStrategies
from easyfind.content_parser import ContentParser
from easyfind.web_scraper import WebScraper
from easyfind.data_manager import DataManager
from easyfind.engine import main, procesar_tarea_segura