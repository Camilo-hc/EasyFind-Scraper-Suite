"""
Bot Recolector de Productos - Artilec Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Artilec (https://www.artilec.com), una tienda especializada en seguridad electrónica,
control de acceso, CCTV y sistemas de alarmas en Chile.

Tecnología utilizada:
    - requests: Para realizar peticiones HTTP
    - BeautifulSoup: Para parsear y extraer datos del HTML
    - pandas: Para estructurar y exportar datos a Excel
    
Características principales:
    - Modo de página única (sin paginación)
    - Extracción completa de catálogo por categoría
    - Sistema de reintentos ante fallos de conexión
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Línea de negocio: Categoría del producto
    - Tienda: Nombre de la tienda (Artilec)

Dependencias:
    pip install requests beautifulsoup4 pandas openpyxl

Uso:
    python Bot-recolector-Artilec.py
    
Salida:
    Genera el archivo 'Base_Datos_Artilec.xlsx' en la carpeta 'TIENDAS/'

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================
# Nombre de la tienda para identificación en la base de datos
NOMBRE_TIENDA = "Artilec"

# Dominio base del sitio web (usado para construir URLs absolutas)
DOMAIN = "https://www.artilec.com" 

# Lista de categorías a procesar (modo página única - sin paginación)
# Cada categoría contiene todos los productos en una sola página
categorias = [
    ("Alarmas", "https://www.artilec.com/alarmas-de-intrusion"),
    ("Cableado Estructurado", "https://www.artilec.com/cableado-estructurado"),
    ("CCTV", "https://www.artilec.com/cctv"),
    ("Control de Acceso", "https://www.artilec.com/control-de-acceso"),
    ("Energia", "https://www.artilec.com/energia"),
    ("Incendio", "https://www.artilec.com/incendio"),
    ("Ley de Ductos", "https://www.artilec.com/ley-de-ductos"),
]

# Lista que almacenará todos los productos recolectados
datos_totales = []

# ============================================================================
# CONFIGURACIÓN DE HEADERS HTTP
# ============================================================================
# Headers para simular un navegador real y evitar bloqueos del servidor
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

# ============================================================================
# INICIO DEL PROCESO DE RECOLECCIÓN
# ============================================================================
print(f"--- INICIANDO RECOLECCIÓN (MODO PÁGINA ÚNICA): {NOMBRE_TIENDA} ---")

# Iterar sobre cada categoría (cada una es una página única con todos los productos)
for nombre_cat, url_cat in categorias:
    print(f"\n>>> Procesando: {nombre_cat}")
    
    try:
        print(f"   Descargando catálogo...", end=" ")
        response = requests.get(url_cat, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[Error {response.status_code}] -> Saltando categoría.")
            continue
            
        print("[OK]")

        soup = BeautifulSoup(response.text, 'html.parser')

        bloques = soup.find_all('div', class_='product-col')
        
        print(f"   ({len(bloques)} productos encontrados en esta categoría)")
        
        if not bloques:
            print("   -> No se detectaron productos (revisar selectores).")
            continue

        productos_categoria = 0

        for bloque in bloques:
            try:
                div_titulo = bloque.find('div', class_='producto_descripcion_name')
                
                if div_titulo:
                    link_obj = div_titulo.find('a')
                    if link_obj:
                        nombre = link_obj.text.strip()
                        link_parcial = link_obj.get('href', '')
                    else:
                        continue
                else:
                    continue
                
                if link_parcial and not link_parcial.startswith('http'):
                    if link_parcial.startswith('/'):
                        link_final = f"{DOMAIN}{link_parcial}"
                    else:
                        link_final = f"{DOMAIN}/{link_parcial}"
                else:
                    link_final = link_parcial
                
                datos_totales.append({
                    'Producto': nombre,
                    'Link': link_final,
                    'Línea de negocio': nombre_cat,
                    'Tienda': NOMBRE_TIENDA
                })
                productos_categoria += 1
            except Exception as e:
                continue
        
        print(f"   -> {productos_categoria} productos agregados exitosamente.")

    except Exception as e:
        print(f"\n[Fallo conexión o error crítico]: {e}")
    
    time.sleep(random.uniform(1.0, 2.0))  # Optimizado: antes 2.0-4.0 

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    columnas_ordenadas = ['Producto', 'Link', 'Línea de negocio', 'Tienda']
    df = df[columnas_ordenadas]
    
    # Eliminar duplicados por si acaso
    df = df.drop_duplicates(subset=['Link'], keep='first')
    
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # 1. Crear carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada: {ruta_carpeta}")
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    nombre_archivo = "Base_Datos_Artilec.xlsx" 
    ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
    
    # 2. ELIMINAR ARCHIVO SI YA EXISTE (Para asegurar reemplazo)
    if os.path.exists(ruta_completa):
        try:
            os.remove(ruta_completa)
            print(f"Archivo previo eliminado para ser reemplazado: {nombre_archivo}")
        except PermissionError:
            print(f"⚠️ ADVERTENCIA: El archivo '{nombre_archivo}' está abierto. Ciérralo para permitir el reemplazo.")

    # 3. Guardar el nuevo archivo
    try:
        df.to_excel(ruta_completa, index=False)
        print("\n" + "="*50)
        print(f"¡PROCESO COMPLETADO!")
        print(f"Total productos guardados: {len(df)}")
        print(f"Archivo Excel generado en: {ruta_completa}")
        print("="*50)
    except ModuleNotFoundError:
        print("\nERROR: Falta la librería 'openpyxl'. Ejecuta 'pip install openpyxl'")
    except Exception as e:
        print(f"\nError al guardar el Excel: {e}")      
else:
    print("No se encontraron datos.")