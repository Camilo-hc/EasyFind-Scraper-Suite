"""
Estrategias de extracción específicas por tienda para marcas y precios.

Contiene métodos especializados para extraer información de tiendas que
requieren lógica personalizada debido a su estructura HTML única.
"""

import re
import json

from .utils import Utils
from .config import TASA_DOLAR


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
    def extract_videovision_price(soup):
        """Extrae precio USD sin IVA de VideoVision y convierte a CLP automáticamente"""
        try:
            bloque_neto = soup.select_one('.bloque-neto')
            if bloque_neto:
                precio_texto = bloque_neto.get_text(strip=True)
                precio_texto_limpio = precio_texto.split('+')[0].strip()
                precio_usd = Utils.limpiar_precio_usd_smart(precio_texto_limpio)
                if precio_usd > 0:
                    precio_clp = int(precio_usd * TASA_DOLAR)
                    return precio_clp
        except Exception:
            pass
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
            'compratecno': StoreStrategies.extract_compratecno_price,
            'videovision': StoreStrategies.extract_videovision_price
        }
        for clave, estrategia in ESTRATEGIAS_PRECIO.items():
            if clave in domain: return estrategia
        return None
