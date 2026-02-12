"""
Utilidades de procesamiento de texto para coincidencia de productos y parseo de precios.

Proporciona métodos estáticos para normalizar texto, limpiar precios en diferentes
formatos y monedas, y validar nombres de marcas.
"""

import re
from typing import Optional, Dict, Any

from .config import Config


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
        
        Args:
            valor: Precio como string, int, o float. Puede incluir símbolos
                   de moneda, separadores de miles, o texto adicional.
        
        Returns:
            int: Precio limpio como entero en CLP. Retorna 0 si no puede parsear.
        
        Example:
            >>> Utils.limpiar_precio_clp("$45.000")
            45000
            >>> Utils.limpiar_precio_clp("1.234.567 CLP")
            1234567
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
        
        Args:
            texto (str): Texto candidato a ser marca.
        
        Returns:
            Optional[str]: Marca validada y limpia, o None si no es válida.
        
        Example:
            >>> Utils.validar_marca("MARCA: 3M")
            '3M'
            >>> Utils.validar_marca("$45.000")
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
