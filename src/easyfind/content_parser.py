"""
Parseo genérico de HTML para extracción de marcas y precios.

Implementa estrategias genéricas de extracción que funcionan en la mayoría
de las tiendas, utilizando JSON-LD, meta tags y búsqueda de texto.
"""

import re
import json
from typing import Optional

from .config import Config, TASA_DOLAR
from .utils import Utils
from .store_strategies import StoreStrategies


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
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado.
            url (str): URL de la página para identificar la tienda.
        
        Returns:
            str: Nombre de la marca encontrada, o "Sin Marca" si no se encuentra.
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
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado.
            url (str): URL de la página para identificar la tienda.
        
        Returns:
            int: Precio en CLP como entero, 0 si no se encuentra o requiere login.
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
