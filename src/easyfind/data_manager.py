"""
Carga de bases de datos y lógica de coincidencia difusa para búsqueda de productos.

Maneja la carga de archivos Excel/CSV de tiendas y proporciona múltiples niveles
de precisión para la búsqueda de productos.
"""

import os
import re
from typing import Tuple, Optional

import pandas as pd

from .config import Config, RAPIDFUZZ_DISPONIBLE
from .utils import Utils

if RAPIDFUZZ_DISPONIBLE:
    from rapidfuzz import fuzz, process


class DataManager:
    """Carga de bases de datos y lógica de coincidencia difusa para búsqueda de productos."""
    
    @staticmethod
    def cargar_bases_datos(ruta_carpeta: str) -> pd.DataFrame:
        """Carga y unifica todas las bases de datos de tiendas desde una carpeta.
        
        Lee archivos Excel (.xlsx) y CSV (.csv) de la carpeta especificada,
        extrae las columnas de nombre y URL, y las unifica en un solo DataFrame
        con el texto normalizado para búsqueda difusa.
        
        Args:
            ruta_carpeta (str): Ruta a la carpeta que contiene los archivos
                de bases de datos (ej: 'TIENDAS/').
        
        Returns:
            pd.DataFrame: DataFrame unificado con columnas ['Nombre', 'URL', 'Tienda', 'Nombre_Norm'].
                Retorna DataFrame vacío si no hay archivos válidos.
        """
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
        """Búsqueda de precisión media (match probable)."""
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
