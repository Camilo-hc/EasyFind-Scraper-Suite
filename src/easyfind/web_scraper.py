"""
Web scraper basado en Playwright asíncrono con gestión concurrente de pestañas.

Maneja la automatización del navegador Chromium para scraping de páginas dinámicas.
"""

import asyncio
import random
from typing import Tuple

import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from .config import Config
from .content_parser import ContentParser


class WebScraper:
    """Web scraper basado en Playwright asíncrono con gestión concurrente de pestañas.
    
    Maneja la automatización del navegador Chromium para scraping de páginas dinámicas.
    Implementa optimizaciones de rendimiento como bloqueo de recursos y reintentos automáticos.
    
    Attributes:
        playwright: Instancia de Playwright para control del navegador.
        browser: Instancia del navegador Chromium.
    
    Note:
        - Usa Chromium en modo headless para mejor rendimiento
        - Bloquea imágenes/CSS/fuentes para acelerar carga 3x
        - Implementa rotación de User-Agents
        - Maneja timeouts y errores automáticamente
        - Compatible con aplicaciones empaquetadas (PyInstaller)
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
    
    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-gpu', '--no-sandbox']
            )

    async def stop(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        print("Motor detenido.")

    async def procesar_url(self, url: str) -> Tuple[int, str, str]:
        """Hace scraping de URL para extraer precio y marca.
        
        Args:
            url (str): URL del producto a scrapear.
        
        Returns:
            Tuple[int, str, str]: (precio_clp, marca, mensaje_error)
        """
        if not url or pd.isna(url) or len(str(url)) < 5: 
            return 0, "Sin Marca", "URL Inválida"
        
        # Ajuste específico para Automatec
        if 'automatec.cl' in url and "id_currency=" not in url: 
            url += "&id_currency=1" if "?" in url else "?id_currency=1"

        page = None
        INTENTOS_MAXIMOS = 2
        
        try:
            if not self.browser: await self.start()
            context = await self.browser.new_context(
                user_agent=random.choice(Config.USER_AGENTS),
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,svg,css,woff,woff2,gif,ico}", lambda route: route.abort())

            for intento in range(1, INTENTOS_MAXIMOS + 1):
                try:
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    await page.goto(url, timeout=25000, wait_until='domcontentloaded')
                    
                    if 'sonepar' in url.lower(): await page.wait_for_timeout(1000) 
                    if 'dartel' in url.lower(): await page.wait_for_timeout(800)

                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')

                    precio = ContentParser.extraer_precio(soup, url)
                    marca = ContentParser.extraer_marca(soup, url)

                    await page.close()
                    await context.close()
                    return precio, marca, ""
                except Exception as e:
                    if intento < INTENTOS_MAXIMOS:
                        await asyncio.sleep(1.5) 
                        continue 
                    else:
                        if page: await page.close()
                        if context: await context.close()
                        return 0, "Sin Marca", f"Err: {str(e)[:20]}"
        except Exception as e:
            return 0, "Sin Marca", f"Driver: {str(e)}"
        return 0, "Sin Marca", "Unknown"
