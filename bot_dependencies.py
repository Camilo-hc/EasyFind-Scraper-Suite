"""
Este archivo existe SOLO para forzar a PyInstaller a incluir las librerías
que usan los bots externos (que no son importadas directamente por App.py).
NO SE EJECUTA, SOLO SE IMPORTA.
"""

import sys

# Si estamos en tiempo de ejecución normal, no hacemos nada.
# Esto es solo para el análisis de PyInstaller.
if getattr(sys, 'frozen', False):
    pass

try:
    # 1. Librerías Estándar y Comunes
    import pandas as pd
    import openpyxl
    import requests
    import bs4  # BeautifulSoup
    
    # 2. Selenium y Drivers
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    
    # 3. Otras utilidades
    import time
    import random
    import os
    import json
    import re
    
except ImportError:
    pass
