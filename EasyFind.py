"""EasyFind - Motor de Scraping Asíncrono de Precios.

Sistema automatizado de comparación de precios para productos eléctricos de proveedores chilenos.
Utiliza Playwright para scraping web asíncrono con coincidencia difusa de doble precisión.

Autor: Camilo Hernández
"""

"""
ARCHIVO TÉCNICO
NO MODIFICAR
Cualquier cambio aquí puede romper la herramienta
"""

import pandas as pd
import asyncio
import os
import time
import sys
import random
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import urllib3
from typing import List, Tuple, Optional, Dict, Any
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from collections import defaultdict

# ========== NUEVO: IMPORTAR RAPIDFUZZ ==========
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_DISPONIBLE = True
except ImportError:
    print(" RapidFuzz no instalado. Usando método legacy.")
    print("   Instala con: pip install rapidfuzz")
    RAPIDFUZZ_DISPONIBLE = False
# ================================================

# Configuración de ruta de navegadores para ejecutable empaquetado
if getattr(sys, 'frozen', False):
    # Cuando está empaquetado con PyInstaller
    # _MEIPASS es la carpeta temporal donde PyInstaller extrae los archivos
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "browsers")
else:
    # En desarrollo, usar la carpeta browsers del proyecto
    base_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(base_path, "browsers")):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "browsers")

class Config:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    load_dotenv()

    # --- AJUSTES DE VELOCIDAD Y CONCURRENCIA ---
    CONCURRENCIA_GLOBAL = 8   # Total de pestañas simultáneas
    CONCURRENCIA_POR_TIENDA = 2 # Máximo de pestañas por dominio 
    TAMANO_LOTE_GUARDADO = 100 # Guardar Excel cada 50 productos procesados
    
    CARPETA_TIENDAS = "TIENDAS"
    
    # ========== NUEVO: UMBRALES DE SIMILITUD ==========
    UMBRAL_ALTA_PRECISION = 85      # Similitud mínima para match confiable
    UMBRAL_MEDIA_PRECISION = 75     # Similitud para match probable
    UMBRAL_BAJA_PRECISION = 65      # Similitud mínima aceptable
    # ==================================================
    
    # Textos de Salida
    TEXTO_LOGIN = "Ver Web / Login"
    TEXTO_ERROR = "ERROR / NO DETECTADO"
    TEXTO_SIN_LINK = "Link no encontrado"

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    TIENDAS_CON_IVA = ['COMPRATECNO', 'COMDIEL', 'DARTEL', 'EECOL', 'GOBANTES', 'VITEL']
    TIENDAS_SOLO_MARCA = ['SONEPAR', 'TRANSWORLD', 'INTCOMEX']
    
    PALABRAS_IGNORAR = [
        'ODF', 'JUMPER', 'MUFA', 'MANGUITO', 'BANDEJA', 'SPLITTER', 'NAP', 'ROSETA',
        'PIGTAIL', 'PATCHCORD', 'PATCH', 'CORD', 'CONNECTOR', 'ADAPTER', 'DISTRIBUIDOR',
        'TERMINAL', 'CAJA', 'GABINETE', 'RACK', 'ORGANIZADOR', 'FACEPLATE', 'KEYSTONE',
        'FIBRA', 'CABLE', 'CONECTOR', 'BOBINA', 'KIT', 'HERRAMIENTA', 'TESTER', 
        'MODULO', 'MÓDULO', 'UNIDAD', 'TRANSCEIVER', 'SFP', 'MEDIA', 'CONVERTER',
        'TAMAÑO', 'TAMANO', 'DIMENSIONES', 'PESO', 'MEDIDA', 'LONGITUD', 'ANCHO', 'ALTO',
        'PRECIO', 'VALOR', 'DESCRIPCION', 'DETALLE', 'SKU', 'CODIGO', 'INTERNET', 
        'NORMAL', 'OFERTA', 'OFERTAS', 'OUTLET', 'CATEGORIA', 'PRODUCTO', 
        'RELACIONADOS', 'INGRESAR', 'REGISTRARSE', 'CUENTA', 'CARRITO', 'MENU', 
        'BUSCAR', 'CONTACTO', 'INICIO', 'HOME', 'LOGIN', 'FICHA', 'TECNICA', 
        'DESCARGAR', 'PDF', 'STOCK', 'DISPONIBLE', 'AGOTADO', 'ENVIO', 'RETIRO',
        'ESPECIFICACIONES', 'CARACTERISTICAS', 'OPINIONES', 'COMENTARIOS', 
        'REFERENCIA', 'NUMERO', 'SERIE', 'MODELO', 'PART', 'NUMBER', 'CANTIDAD'
    ]

    @staticmethod
    def obtener_dolar_oficial() -> int:
        """Obtiene la tasa de cambio oficial USD/CLP desde la API de mindicador.cl.
        
        Realiza hasta 3 intentos de conexión a la API pública de mindicador.cl
        para obtener el valor actualizado del dólar. Si todos los intentos fallan,
        retorna un valor por defecto de 870 CLP.
        
        Returns:
            int: Tasa de cambio USD/CLP. Valor por defecto 870 si falla la API.
        
        Note:
            - Timeout de 10 segundos por intento
            - Espera de 2 segundos entre intentos fallidos
            - Imprime mensajes de progreso en consola
            - No lanza excepciones, siempre retorna un valor
        
        Example:
            >>> tasa = Config.obtener_dolar_oficial()
            🌎 Obteniendo valor del Dólar
               ✅ Dólar: $950 CLP
            >>> print(tasa)
            950
        """
        print("🌎 Obteniendo valor del Dólar")
        url = "https://mindicador.cl/api"
        for intento in range(1, 4):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    valor = int(data['dolar']['valor'])
                    print(f"Dólar: ${valor} CLP")
                    return valor
            except Exception as e:
                print(f"Intento {intento} fallido: {e}")
                time.sleep(2)
        
        print("Fallaron todos los intentos. Usando valor por defecto $870")
        return 870

TASA_DOLAR = 870

class Utils:
    """Utilidades de procesamiento de texto para coincidencia de productos y parseo de precios.
    
    Esta clase proporciona métodos estáticos para normalizar texto, limpiar precios
    en diferentes formatos y monedas, y validar nombres de marcas. Todos los métodos
    están diseñados para ser robustos y manejar entradas mal formateadas.
    """
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Normaliza texto de productos para coincidencia difusa.
        
        Convierte el texto a mayúsculas, elimina separadores, y estandariza
        patrones comunes en productos eléctricos (fibra óptica, categorías de cable).
        
        Args:
            texto (str): Texto del producto a normalizar.
        
        Returns:
            str: Texto normalizado en mayúsculas sin separadores.
        
        Note:
            - Convierte "24 HILOS" -> "24F", "48FO" -> "48F"
            - Estandariza "CAT 6A" -> "CAT6A", "CAT.6" -> "CAT6"
            - Reemplaza comas, guiones y slashes por espacios
            - Retorna string vacío si la entrada es None o vacía
        
        Example:
            >>> Utils.normalizar_texto("Cable UTP CAT-6A, 24 hilos")
            'CABLE UTP CAT6A 24F'
            >>> Utils.normalizar_texto("Fibra óptica 48FO")
            'FIBRA OPTICA 48F'
        """
        if not texto: return ""
        t = str(texto).upper().strip()
        t = re.sub(r'(\d+)\s*(FO|HILOS|HILO|H|FIBRA)\b', r'\1F', t)
        t = re.sub(r'CAT[\.\s-]*(\d+[A-Z]?)', r'CAT\1', t)
        t = t.replace(',', ' ').replace('-', ' ').replace('/', ' ')
        return t

    @staticmethod
    def limpiar_precio_clp(valor) -> int:
        """Parsea y limpia un precio en pesos chilenos desde diferentes formatos.
        
        Maneja múltiples formatos de entrada incluyendo separadores de miles
        (puntos/comas), símbolos de moneda ($, CLP), y espacios. Detecta
        automáticamente el formato y convierte a entero.
        
        Args:
            valor: Precio como string, int, o float. Puede incluir símbolos
                   de moneda, separadores de miles, o texto adicional.
        
        Returns:
            int: Precio limpio como entero en CLP. Retorna 0 si no puede parsear.
        
        Note:
            - Maneja formato chileno: "$45.000" -> 45000
            - Maneja formato europeo: "45.000,50" -> 45000
            - Maneja formato americano: "45,000.50" -> 45000
            - Elimina texto adicional después de "+" (ej: "$100 + IVA")
            - Retorna 0 en caso de error en lugar de lanzar excepción
        
        Example:
            >>> Utils.limpiar_precio_clp("$45.000")
            45000
            >>> Utils.limpiar_precio_clp("1.234.567 CLP")
            1234567
            >>> Utils.limpiar_precio_clp("$99,99")
            99
        """
        if not valor: return 0
        val_str = str(valor).strip().upper().replace('$', '').replace('CLP', '').strip()
        val_str = val_str.split('+')[0].strip()
        
        match = re.search(r'([\d\.,]+)', val_str)
        if not match: return 0
        val_str = match.group(1)

        try:
            if ',' in val_str and '.' in val_str:
                if val_str.rfind(',') > val_str.rfind('.'): 
                    val_str = val_str.replace('.', '').replace(',', '.')
                else: 
                    val_str = val_str.replace(',', '') 
            elif ',' in val_str:
                partes = val_str.split(',')
                if len(partes[-1]) == 2: val_str = val_str.replace(',', '.')
                else: val_str = val_str.replace(',', '') 
            elif '.' in val_str:
                partes = val_str.split('.')
                ultimo_bloque = partes[-1]
                if len(ultimo_bloque) != 3:
                    return int(float(val_str))
                else:
                    val_str = val_str.replace('.', '')

            return int(float(val_str))
        except: 
            return 0

    @staticmethod
    def limpiar_precio_usd_smart(valor) -> float:
        """Parsea y limpia un precio en dólares estadounidenses.
        
        Args:
            valor: Precio como string, int, o float. Puede incluir "USD", "US$", "$".
        
        Returns:
            float: Precio limpio como float en USD. Retorna 0.0 si no puede parsear.
        
        Note:
            - Elimina símbolos: "USD", "US", "$"
            - Maneja comas como separador decimal (formato europeo)
            - Retorna 0.0 en caso de error
        
        Example:
            >>> Utils.limpiar_precio_usd_smart("USD 45.99")
            45.99
            >>> Utils.limpiar_precio_usd_smart("$1,234.56")
            1234.56
        """
        if not valor: return 0.0
        v = str(valor).upper().replace('USD', '').replace('US', '').replace('$', '').strip()
        v = re.sub(r'[^\d,\.]', '', v)
        if not v: return 0.0
        try:
            if ',' in v and '.' in v:
                if v.rfind(',') > v.rfind('.'): v = v.replace('.', '').replace(',', '.')
                else: v = v.replace(',', '')
            elif ',' in v: v = v.replace(',', '.')
            return float(v)
        except: return 0.0

    @staticmethod
    def validar_marca(texto: str) -> Optional[str]:
        """Valida y limpia nombre de marca, filtrando patrones inválidos.
        
        Aplica múltiples reglas de validación para asegurar que el texto
        extraído corresponda realmente a una marca y no a otros elementos
        de la página (precios, descripciones, etc.).
        
        Args:
            texto (str): Texto candidato a ser marca.
        
        Returns:
            Optional[str]: Marca validada y limpia, o None si no es válida.
        
        Note:
            - Elimina prefijos: "MARCA:", "FABRICANTE:"
            - Rechaza si es solo números
            - Rechaza si tiene longitud < 2 o > 30 caracteres
            - Rechaza si contiene: $, @, WWW.
            - Rechaza si coincide con palabras prohibidas (Config.PALABRAS_IGNORAR)
            - Permite marcas conocidas: 3M, D-LINK, TP-LINK, UBIQUITI, etc.
            - Rechaza si parece código alfanumérico largo (ej: SKU)
        
        Example:
            >>> Utils.validar_marca("MARCA: 3M")
            '3M'
            >>> Utils.validar_marca("$45.000")
            None
            >>> Utils.validar_marca("CABLE UTP")
            None
        """
        if not texto: return None
        t = str(texto).strip().upper() 
        t = t.replace('MARCA:', '').replace('MARCA', '').strip()
        t = t.replace('FABRICANTE:', '').replace('FABRICANTE', '').strip()
        t = t.lstrip('-:., ').rstrip('.:, ')

        if t.replace('.', '').replace(',', '').strip().isdigit(): return None
        if len(t) < 2 or len(t) > 30: return None
        if '$' in t or '@' in t or 'WWW.' in t: return None
        
        MARCAS_OK = ['3M', 'D-LINK', 'TP-LINK', 'UBIQUITI', 'MIKROTIK', 'CISCO', 'APC', 'HIKVISION', 'DAHUA']
        if not any(m in t for m in MARCAS_OK):
             if re.search(r'[A-Z]', t) and re.search(r'[0-9]', t) and len(t) > 5: return None

        for prohibida in Config.PALABRAS_IGNORAR:
            if prohibida == t or f" {prohibida} " in f" {t} ": return None
            
        return t
    
    # ========== NUEVO: EXTRACCIÓN DE CARACTERÍSTICAS ==========
    @staticmethod
    def extraer_caracteristicas(texto: str) -> Dict[str, Any]:
        """Extrae características clave del texto para matching inteligente."""
        texto_norm = Utils.normalizar_texto(texto)
        
        # Extraer números técnicos (modelos, versiones, etc)
        numeros = re.findall(r'\b\d+[A-Z]?\b', texto_norm)
        
        # Extraer códigos alfanuméricos (ej: "CAT6A", "48F")
        codigos = re.findall(r'\b[A-Z]+\d+[A-Z]?\b', texto_norm)
        
        # Palabras significativas (filtrar palabras cortas y comunes)
        palabras = [p for p in texto_norm.split() 
                   if len(p) > 2 and p not in Config.PALABRAS_IGNORAR]
        
        return {
            'texto_completo': texto_norm,
            'numeros': numeros,
            'codigos': codigos,
            'palabras': palabras,
            'tokens_criticos': numeros + codigos  # Los más importantes para matching
        }
    # ==========================================================

class StoreStrategies:
    """Estrategias de extracción específicas por tienda para marcas y precios.
    
    Esta clase contiene métodos especializados para extraer información de tiendas
    que requieren lógica personalizada debido a su estructura HTML única. Cada método
    está optimizado para una tienda específica.
    
    Note:
        - Todos los métodos son estáticos y reciben un objeto BeautifulSoup
        - Retornan None si no pueden extraer la información
        - Se usan como fallback antes de las estrategias genéricas
    """
    
    @staticmethod
    def extract_lk(soup):
        try:
            container = soup.select_one('.pag_detalle')
            if container and container.has_attr('data-fab'):
                fab_id = container['data-fab']
                fab_link = soup.select_one(f'.barraFabricantes a[data-id="{fab_id}"]')
                if fab_link and fab_link.get('title'): return fab_link['title']
        except: pass
        try:
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title and og_title.get('content'):
                txt = og_title['content'].replace('LK - ', '')
                if '. ' in txt: return txt.split('. ')[1].split(' ')[0]
        except: pass
        return None

    @staticmethod
    def extract_transworld(soup):
        marca_link = soup.select_one('a[href*="/marcas/"]')
        if marca_link: return marca_link.get_text(strip=True)
        return None

    @staticmethod
    def extract_intcomex(soup):
        marca_node = soup.select_one('.marca')
        return marca_node.get_text(strip=True) if marca_node else None

    @staticmethod
    def extract_compratecno_marca(soup):
        man_node = soup.select_one('.product-manufacturer meta[itemprop="name"]') or \
                   soup.select_one('.product-manufacturer span[itemprop="name"]')
        if man_node: 
            return man_node.get('content') if man_node.get('content') else man_node.get_text(strip=True)
        return None

    @staticmethod
    def extract_dartel_price(soup):
        try:
            template = soup.find('template', attrs={'data-varname': '__STATE__'})
            if template:
                script = template.find('script')
                if script and script.string:
                    data = json.loads(script.string)
                    for key, val in data.items():
                        if isinstance(val, dict) and 'commertialOffer' in key:
                            price = val.get('Price')
                            if price and isinstance(price, (int, float)) and price > 0:
                                return int(price)
        except Exception: pass
        
        precios_vtex = soup.select('[class*="sellingPriceValue"]')
        for el in precios_vtex:
            val = Utils.limpiar_precio_clp(el.get_text())
            if val > 0: return val
        meta = soup.select_one('meta[property="product:price:amount"]')
        if meta and meta.get('content'): return int(float(meta['content']))
        return 0

    @staticmethod
    def extract_gobantes_price(soup):
        for sel in ['.skuBestPrice', '.best-price', '.sales-price', '.precio-oferta', '.product-price']:
            el = soup.select_one(sel)
            if el: return Utils.limpiar_precio_clp(el.get_text())
        scripts = soup.find_all('script')
        for s in scripts:
            if s.string and 'Price' in s.string:
                match = re.search(r'"Price":(\d+)', s.string)
                if match: return int(match.group(1))
        return 0

    @staticmethod
    def extract_vitel_price(soup):
        for sel in ['.price', '.regular-price', '.price-box .price']:
            el = soup.select_one(sel)
            if el: return Utils.limpiar_precio_clp(el.get_text())
        return 0
    
    @staticmethod
    def extract_compratecno_price(soup):
        for sel in ['.current-price span[itemprop="price"]', '.product-price', '#our_price_display']:
            el = soup.select_one(sel)
            if el and el.has_attr('content'): return int(float(el['content']))
            if el: return Utils.limpiar_precio_clp(el.get_text())
        return 0

    @staticmethod
    def get_brand_strategy(domain: str):
        ESTRATEGIAS_MARCA = {
            'lk.cl': StoreStrategies.extract_lk,
            'linkstore': StoreStrategies.extract_lk,
            'transworld': StoreStrategies.extract_transworld,
            'intcomex': StoreStrategies.extract_intcomex,
            'compratecno': StoreStrategies.extract_compratecno_marca
        }
        for clave, estrategia in ESTRATEGIAS_MARCA.items():
            if clave in domain: return estrategia
        return None

    @staticmethod
    def get_price_strategy(domain: str):
        ESTRATEGIAS_PRECIO = {
            'dartel': StoreStrategies.extract_dartel_price,
            'gobantes': StoreStrategies.extract_gobantes_price,
            'vitel': StoreStrategies.extract_vitel_price,
            'compratecno': StoreStrategies.extract_compratecno_price
        }
        for clave, estrategia in ESTRATEGIAS_PRECIO.items():
            if clave in domain: return estrategia
        return None

class ContentParser:
    """Parseo genérico de HTML para extracción de marcas y precios.
    
    Esta clase implementa estrategias genéricas de extracción que funcionan
    en la mayoría de las tiendas. Utiliza múltiples técnicas: JSON-LD,
    meta tags, y búsqueda de texto para maximizar la tasa de éxito.
    
    Note:
        - Intenta primero estrategias específicas por tienda (StoreStrategies)
        - Luego aplica estrategias genéricas (JSON-LD, meta tags)
        - Finalmente busca en el texto de la página
        - Todos los métodos manejan errores silenciosamente
    """
    
    @staticmethod
    def _extraer_marca_json_ld(soup) -> Optional[str]:
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
            try:
                if not s.string: continue
                data = json.loads(s.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get('@type') == 'Product' and 'brand' in item:
                        brand = item['brand']
                        return brand.get('name') if isinstance(brand, dict) else str(brand)
            except: continue
        return None

    @staticmethod
    def _extraer_marca_generic(soup) -> Optional[str]:
        meta_tags = ['meta[itemprop="brand"]', 'meta[property="product:brand"]', 
                     'meta[name="brand"]', 'meta[itemprop="manufacturer"]']
        for tag in meta_tags:
            el = soup.select_one(tag)
            if el and el.get('content'):
                m = Utils.validar_marca(el['content'])
                if m: return m
        nodos_marca = soup.find_all(string=re.compile(r'Marca|Fabricante|Brand', re.I))
        for nodo in nodos_marca:
            if len(nodo) > 30: continue
            padre = nodo.parent
            if padre.name in ['script', 'style', 'head', 'title', 'a']: continue
            siguiente = padre.find_next_sibling(['td', 'dd', 'span', 'div', 'p', 'strong'])
            if siguiente:
                m = Utils.validar_marca(siguiente.get_text(separator=' ', strip=True))
                if m: return m
        return None

    @classmethod
    def extraer_marca(cls, soup, url: str) -> str:
        """Extrae marca desde HTML usando estrategias específicas por tienda o genéricas.
        
        Aplica una cascada de estrategias de extracción, comenzando con las más
        específicas y terminando con las genéricas. Siempre retorna un valor.
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado.
            url (str): URL de la página para identificar la tienda.
        
        Returns:
            str: Nombre de la marca encontrada, o "Sin Marca" si no se encuentra.
        
        Note:
            - Prioridad 1: Estrategia específica de la tienda (StoreStrategies)
            - Prioridad 2: JSON-LD para tiendas conocidas (Artilec, Eecol, Sonepar)
            - Prioridad 3: Estrategia genérica (meta tags, texto)
            - Valida todas las marcas con Utils.validar_marca()
        
        Example:
            >>> soup = BeautifulSoup(html, 'html.parser')
            >>> marca = ContentParser.extraer_marca(soup, "https://lk.cl/producto/123")
            >>> print(marca)
            '3M'
        """
        domain = url.lower()
        strategy = StoreStrategies.get_brand_strategy(domain)
        if strategy:
            m = strategy(soup)
            if m: return Utils.validar_marca(m) or "Sin Marca"
        if any(x in domain for x in ['artilec', 'eecol', 'sonepar']):
            m = cls._extraer_marca_json_ld(soup)
            if m: return Utils.validar_marca(m) or "Sin Marca"
        m = cls._extraer_marca_generic(soup)
        return m if m else "Sin Marca"

    @classmethod
    def extraer_precio(cls, soup, url: str) -> int:
        """Extrae precio desde HTML usando estrategias específicas por tienda o genéricas.
        
        Aplica estrategias de extracción en cascada, manejando diferentes formatos
        de precio (CLP, USD) y estructuras HTML. Retorna 0 para tiendas que requieren login.
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado.
            url (str): URL de la página para identificar la tienda.
        
        Returns:
            int: Precio en CLP como entero, 0 si no se encuentra o requiere login.
        
        Note:
            - Retorna 0 para tiendas en TIENDAS_SOLO_MARCA (requieren login)
            - Prioridad 1: Estrategia específica de la tienda
            - Prioridad 2: Meta tags (product:price:amount, itemprop="price")
            - Prioridad 3: Selectores CSS comunes (.price, .current-price, etc.)
            - Convierte USD a CLP automáticamente usando TASA_DOLAR
            - Filtra precios menores a 1000 CLP (probablemente errores)
        
        Example:
            >>> soup = BeautifulSoup(html, 'html.parser')
            >>> precio = ContentParser.extraer_precio(soup, "https://lk.cl/producto/123")
            >>> print(precio)
            45000
        """
        url_lower = url.lower()
        if any(t.lower() in url_lower for t in Config.TIENDAS_SOLO_MARCA): return 0
        
        estrategia = StoreStrategies.get_price_strategy(url_lower)
        if estrategia:
            p = estrategia(soup)
            if p > 0: return p

        if 'automatec' in url_lower:
            el = soup.select_one('.current-price-value[content]') or soup.select_one('meta[itemprop="price"]')
            if el and el.get('content'):
                val_usd = Utils.limpiar_precio_usd_smart(el['content'])
                if val_usd > 0: return int(val_usd * TASA_DOLAR)

        for tag in ['meta[property="product:price:amount"]', 'meta[itemprop="price"]']:
            el = soup.select_one(tag)
            if el and el.get('content'):
                try:
                    raw_val = el['content'].strip()
                    if re.match(r'^\d+(\.\d+)?$', raw_val): 
                        return int(float(raw_val))
                except: pass
                p = Utils.limpiar_precio_clp(el['content'])
                if p > 0: return p

        selectores = ['.price', '.current-price', '.product-price', '.sales-price', 
                      '.precio-internet', '.precio-oferta', 'span.amount']
        for sel in selectores:
            els = soup.select(sel)
            for el in els:
                texto = el.get_text(separator='|', strip=True).split('|')[0]
                if len(texto) > 20: continue 
                p = Utils.limpiar_precio_clp(texto)
                if p > 1000: return p 
        return 0

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
        
        Navega a la URL, extrae el HTML, y parsea precio y marca usando
        ContentParser. Implementa reintentos automáticos y manejo de errores.
        
        Args:
            url (str): URL del producto a scrapear.
        
        Returns:
            Tuple[int, str, str]: (precio_clp, marca, mensaje_error)
                - precio_clp: Precio en CLP, 0 si no se encuentra
                - marca: Nombre de la marca, "Sin Marca" si no se encuentra
                - mensaje_error: String vacío si OK, descripción del error si falla
        
        Note:
            - Valida URL antes de procesar
            - Ajusta URL para Automatec (fuerza moneda CLP)
            - Bloquea recursos innecesarios (imágenes, CSS, fuentes)
            - Espera adicional para tiendas lentas (Sonepar, Dartel)
            - Máximo 2 intentos con espera de 1.5s entre intentos
            - Timeout de 25 segundos por intento
        
        Example:
            >>> scraper = WebScraper()
            >>> await scraper.start()
            >>> precio, marca, err = await scraper.procesar_url("https://lk.cl/producto/123")
            >>> print(f"{marca}: ${precio}")
            3M: $45000
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

class DataManager:
    """Carga de bases de datos y lógica de coincidencia difusa para búsqueda de productos."""
    
    @staticmethod
    def cargar_bases_datos(ruta_carpeta: str) -> pd.DataFrame:
        dfs = []
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)
            return pd.DataFrame()

        archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(('.xlsx', '.csv')) and not f.startswith('~$')]
        print(f"Cargando {len(archivos)} bases de datos...")
        
        for archivo in archivos:
            nombre_tienda = archivo.replace("Base_Datos_", "").replace(".xlsx", "").replace(".csv", "").replace("Base_Datos", "").upper().strip()
            
            nombre_tienda = nombre_tienda.replace("_", " ")
            
            ruta = os.path.join(ruta_carpeta, archivo)
            try:
                if archivo.endswith('.csv'): df = pd.read_csv(ruta, on_bad_lines='skip')
                else: df = pd.read_excel(ruta)
                df.columns = [c.strip().lower() for c in df.columns]
                col_nombre = next((c for c in df.columns if c in ['nombre', 'producto', 'nombre del producto', 'itemname']), None)
                col_link = next((c for c in df.columns if c in ['link', 'url', 'enlace']), None)

                if col_nombre and col_link:
                    temp = df[[col_nombre, col_link]].copy()
                    temp.columns = ['Nombre', 'URL']
                    temp['Tienda'] = nombre_tienda
                    temp['Nombre_Norm'] = temp['Nombre'].astype(str).apply(Utils.normalizar_texto)
                    temp = temp.dropna(subset=['URL'])
                    dfs.append(temp)
            except Exception as e:
                print(f"Error {archivo}: {e}")
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    # ========== NUEVA FUNCIÓN: MATCHING CON RAPIDFUZZ ==========
    @staticmethod
    def _match_con_rapidfuzz(busqueda: str, df_tienda: pd.DataFrame, umbral: int) -> Tuple[Optional[str], Optional[str], int]:
        """
        Búsqueda mejorada usando RapidFuzz para similitud difusa.
        
        Args:
            busqueda: Texto del producto a buscar
            df_tienda: DataFrame con productos de la tienda
            umbral: Score mínimo de similitud (0-100)
            
        Returns:
            Tuple[URL, Nombre, Score]: Mejor match encontrado
        """
        if df_tienda.empty or pd.isna(busqueda):
            return None, None, 0
        
        busqueda_norm = Utils.normalizar_texto(busqueda)
        caracteristicas_busqueda = Utils.extraer_caracteristicas(busqueda)
        
        # Paso 1: Filtro por tokens críticos (números y códigos técnicos)
        df_candidatos = df_tienda.copy()
        tokens_criticos = caracteristicas_busqueda['tokens_criticos']
        
        if tokens_criticos:
            # Productos deben tener AL MENOS el 70% de los tokens críticos
            def tiene_tokens_criticos(texto):
                matches = sum(1 for token in tokens_criticos if token in texto)
                return matches >= len(tokens_criticos) * 0.7
            
            df_candidatos = df_candidatos[
                df_candidatos['Nombre_Norm'].apply(tiene_tokens_criticos)
            ]
        
        # Si no hay candidatos con tokens críticos, usar toda la base
        if df_candidatos.empty:
            df_candidatos = df_tienda.copy()
        
        # Paso 2: Calcular similitud con RapidFuzz
        nombres_norm = df_candidatos['Nombre_Norm'].tolist()
        
        # Token Set Ratio: ignora orden de palabras y duplicados
        resultado = process.extractOne(
            busqueda_norm,
            nombres_norm,
            scorer=fuzz.token_set_ratio,
            score_cutoff=umbral
        )
        
        if resultado:
            texto_match, score, idx = resultado
            fila_ganadora = df_candidatos.iloc[idx]
            return fila_ganadora['URL'], fila_ganadora['Nombre'], score
        
        return None, None, 0
    # ===========================================================

    @staticmethod
    def _core_match_legacy(busqueda: str, df_tienda: pd.DataFrame, factor_sensibilidad: float) -> Tuple[Optional[str], Optional[str]]:
        """Lógica central de coincidencia difusa LEGACY. factor_sensibilidad: 0.9 (estricto) o 0.6 (relajado)."""
        if df_tienda.empty or pd.isna(busqueda): return None, None
        
        palabras, tecnicos = [], []
        busqueda_norm = Utils.normalizar_texto(busqueda)
        for t in busqueda_norm.split():
            if any(char.isdigit() for char in t): tecnicos.append(t)
            elif len(t) > 2: palabras.append(t)
        
        if not palabras and not tecnicos: return None, None
        
        mask_tecnica = pd.Series([True] * len(df_tienda), index=df_tienda.index)
        for token_tec in tecnicos:
            if len(token_tec) >= 2: 
                 mask_tecnica = mask_tecnica & df_tienda['Nombre_Norm'].str.contains(re.escape(token_tec), regex=True)
        
        df_candidatos = df_tienda[mask_tecnica].copy()
        
        if df_candidatos.empty: 
            if factor_sensibilidad > 0.8: return None, None
            df_candidatos = df_tienda.copy()

        df_candidatos['score'] = 0
        for palabra in palabras:
            df_candidatos['score'] += df_candidatos['Nombre_Norm'].str.contains(re.escape(palabra), regex=True).astype(int)
        
        umbral = max(1, len(palabras) * factor_sensibilidad)
        
        ganadores = df_candidatos[df_candidatos['score'] >= umbral].sort_values('score', ascending=False)
        
        if not ganadores.empty:
            mejor = ganadores.iloc[0]
            return mejor['URL'], mejor['Nombre']
        return None, None

    # ========== FUNCIONES PÚBLICAS MEJORADAS ==========
    @classmethod
    def buscar_match_alta_precision(cls, busqueda, df_tienda):
        """Búsqueda de alta precisión (match muy confiable)."""
        if RAPIDFUZZ_DISPONIBLE:
            url, nombre, score = cls._match_con_rapidfuzz(
                busqueda, df_tienda, Config.UMBRAL_ALTA_PRECISION
            )
            return url, nombre
        else:
            return cls._core_match_legacy(busqueda, df_tienda, factor_sensibilidad=0.9)

    @classmethod
    def buscar_match_media_precision(cls, busqueda, df_tienda):
        """NUEVO: Búsqueda de precisión media (match probable)."""
        if RAPIDFUZZ_DISPONIBLE:
            url, nombre, score = cls._match_con_rapidfuzz(
                busqueda, df_tienda, Config.UMBRAL_MEDIA_PRECISION
            )
            return url, nombre
        else:
            return cls._core_match_legacy(busqueda, df_tienda, factor_sensibilidad=0.75)

    @classmethod
    def buscar_match_baja_precision(cls, busqueda, df_tienda):
        """Búsqueda de baja precisión (último intento)."""
        if RAPIDFUZZ_DISPONIBLE:
            url, nombre, score = cls._match_con_rapidfuzz(
                busqueda, df_tienda, Config.UMBRAL_BAJA_PRECISION
            )
            return url, nombre
        else:
            return cls._core_match_legacy(busqueda, df_tienda, factor_sensibilidad=0.6)
    # ==================================================

async def procesar_tarea_segura(sem_global, sem_dominio, scraper, tienda, url, row_idx, metodo_origen):
    """Wrapper para scraping concurrente con limitación de tasa basada en semáforos."""
    async with sem_global:
        async with sem_dominio:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            precio, marca, err = await scraper.procesar_url(url)
            return row_idx, tienda, url, marca, precio, err, metodo_origen

async def main(callback_log=None, callback_progress=None, stop_event=None):
    """Orquestador principal: carga bases de datos, realiza coincidencia de doble precisión y hace scraping de URLs concurrentemente."""
    
    def log(mensaje):
        print(mensaje)
        if callback_log:
            msg_limpio = str(mensaje).replace("\n", "")
            callback_log(msg_limpio)

    if getattr(sys, 'frozen', False):
        carpeta_root = os.path.dirname(sys.executable)
    else:
        carpeta_root = os.path.dirname(os.path.abspath(__file__))
    
    global TASA_DOLAR
    TASA_DOLAR = Config.obtener_dolar_oficial()
    
    if RAPIDFUZZ_DISPONIBLE:
        log(f"--- Iniciando EasyFind MEJORADO (con RapidFuzz) ---")
    else:
        log(f"--- Iniciando EasyFind (modo legacy) ---")
    
    scraper = WebScraper()
    await scraper.start()
    
    try:
        log("Cargando bases de datos de TIENDAS")
        df_db = DataManager.cargar_bases_datos(os.path.join(carpeta_root, Config.CARPETA_TIENDAS))
        if df_db.empty: 
            log("Error: Sin bases de datos en la carpeta TIENDAS.")
            return

        # Cargar archivo de Productos
        try:
            ruta_xlsx = os.path.join(carpeta_root, "PRODUCTOS.xlsx")
            ruta_csv = os.path.join(carpeta_root, "PRODUCTOS.csv")
            
            if os.path.exists(ruta_xlsx):
                df_pedido = pd.read_excel(ruta_xlsx)
            elif os.path.exists(ruta_csv):
                df_pedido = pd.read_csv(ruta_csv)
            else:
                log("No se encontró PRODUCTOS.xlsx ni PRODUCTOS.csv")
                return
        except Exception as e:
            log(f"Error leyendo archivo de productos: {e}")
            return
            
        col_desc = next((c for c in df_pedido.columns if c.lower() in ['itemname', 'descripcion', 'producto']), None)
        if not col_desc: 
            log("Falta columna ItemName/Descripcion en el Excel.")
            return

        tiendas = sorted(df_db['Tienda'].unique())
        # Preparar columnas de salida (SIN METODO)
        for t in tiendas:
            for campo in ['Link', 'Marca', 'Precio']:
                if f"{t} {campo}" not in df_pedido.columns:
                    df_pedido[f"{t} {campo}"] = ""

        # --- FASE 1: GENERACIÓN DE TAREAS DUALES ---
        log(f"⚙️ Analizando {len(df_pedido)} productos")
        
        tareas_pendientes = []
        
        # Inicializar Semáforos
        sem_global = asyncio.Semaphore(Config.CONCURRENCIA_GLOBAL)
        sems_dominio = defaultdict(lambda: asyncio.Semaphore(Config.CONCURRENCIA_POR_TIENDA))
        
        cache_tiendas = {t: df_db[df_db['Tienda'] == t] for t in tiendas}

        count_alta = 0
        count_media = 0
        count_baja = 0
        count_fail = 0

        for idx, row in df_pedido.iterrows():
            producto = str(row[col_desc])
            
            for tienda in tiendas:
                df_subset = cache_tiendas[tienda]
                
                # 1. INTENTO ALTA PRECISIÓN
                url_final, _ = DataManager.buscar_match_alta_precision(producto, df_subset)
                metodo = "Alta Precisión"

                # 2. INTENTO MEDIA PRECISIÓN (NUEVO)
                if not url_final:
                    url_final, _ = DataManager.buscar_match_media_precision(producto, df_subset)
                    metodo = "Media Precisión"
                
                # 3. INTENTO BAJA PRECISIÓN
                if not url_final:
                    url_final, _ = DataManager.buscar_match_baja_precision(producto, df_subset)
                    metodo = "Baja Precisión"
                
                # 4. RESULTADO
                if url_final:
                    dominio_base = url_final.split('/')[2] if '//' in url_final else 'generic'
                    t = procesar_tarea_segura(
                        sem_global, 
                        sems_dominio[dominio_base], 
                        scraper, 
                        tienda, 
                        url_final, 
                        idx,
                        metodo
                    )
                    tareas_pendientes.append(t)
                    
                    if metodo == "Alta Precisión": count_alta += 1
                    elif metodo == "Media Precisión": count_media += 1
                    else: count_baja += 1
                else:
                    # Escribir directamente "Link no encontrado"
                    df_pedido.at[idx, f"{tienda} Link"] = Config.TEXTO_SIN_LINK
                    df_pedido.at[idx, f"{tienda} Precio"] = Config.TEXTO_SIN_LINK
                    df_pedido.at[idx, f"{tienda} Marca"] = "-"
                    count_fail += 1

        log(f"Resumen de Búsqueda en DB:")
        log(f"Alta Precisión: {count_alta}")
        log(f"Media Precisión: {count_media}")
        log(f"Baja Precisión: {count_baja}")
        log(f"No encontrados: {count_fail}")
        log(f"Iniciando scraping de {len(tareas_pendientes)} URLs...")
        
        # --- FASE 2: EJECUCIÓN ASÍNCRONA ---
        total_tareas = len(tareas_pendientes)
        completados = 0
        ultimo_guardado = 0
        
        if total_tareas > 0:
            for corrutina in asyncio.as_completed(tareas_pendientes):
                
                # VERIFICACIÓN DE DETENCIÓN 
                if stop_event and stop_event.is_set():
                    log("Proceso detenido por el usuario.")
                    break 
                
                row_idx, tienda, url_final, marca, precio, err, metodo_usado = await corrutina
                
                # Reglas de IVA y Login
                precio_final = 0
                es_tienda_login = tienda in Config.TIENDAS_SOLO_MARCA

                if precio > 0:
                    if tienda in Config.TIENDAS_CON_IVA:
                        precio_final = int(precio / 1.19)
                    else:
                        precio_final = precio
                
                valor_para_excel = ""
                tag_log = ""

                if precio_final > 0:
                    valor_para_excel = precio_final
                    tag_log = f"$ {precio_final:,.0f}"
                elif es_tienda_login:
                    valor_para_excel = Config.TEXTO_LOGIN
                    tag_log = "Login Req"
                else:
                    valor_para_excel = Config.TEXTO_ERROR
                    tag_log = "No detectado"
                
                if err: tag_log += f" ({err})"

                # Escribir en DF 
                df_pedido.at[row_idx, f"{tienda} Link"] = url_final
                df_pedido.at[row_idx, f"{tienda} Marca"] = marca
                df_pedido.at[row_idx, f"{tienda} Precio"] = valor_para_excel

                completados += 1
                
                # ACTUALIZACIÓN DE BARRA DE PROGRESO
                if callback_progress:
                    callback_progress(completados, total_tareas)

                if completados % 5 == 0 or completados == total_tareas:
                    log(f"[{completados}/{total_tareas}] {tienda} ({metodo_usado}) -> {tag_log}")

                # Guardado Parcial
                if completados - ultimo_guardado >= Config.TAMANO_LOTE_GUARDADO:
                    try:
                        df_pedido.to_excel(os.path.join(carpeta_root, "Resultado_Parcial.xlsx"), index=False)
                        ultimo_guardado = completados
                    except: pass

        # Guardado Final
        output = os.path.join(carpeta_root, "Resultado.xlsx")
        df_pedido.to_excel(output, index=False)
        
        if stop_event and stop_event.is_set():
            log(f"Proceso detenido. Se guardó lo avanzado en: Resultado.xlsx")
        else:
            log(f"Busqueda terminada. Archivo guardado: Resultado.xlsx")

    except KeyboardInterrupt:
        log("Interrumpido por usuario.")
        try:
            df_pedido.to_excel(os.path.join(carpeta_root, "Resultado_Interrumpido.xlsx"), index=False)
        except: pass
    except Exception as e:
        log(f"Error General: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())