"""
Bot Recolector de Productos - Comdiel Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Comdiel (https://www.comdiel.cl), una tienda especializada en cableado estructurado,
fibra óptica, redes y telecomunicaciones en Chile.

Tecnología utilizada:
    - requests: Para realizar peticiones HTTP
    - BeautifulSoup: Para parsear y extraer datos del HTML
    - pandas: Para estructurar y exportar datos a Excel
    
Características principales:
    - Sistema robusto de reintentos (3 intentos por página)
    - Paginación automática mediante parámetros URL (?page=X)
    - Control de fallos consecutivos (máximo 5 antes de cambiar categoría)
    - Detección automática de fin de categoría
    - Eliminación de duplicados por URL
    - Exportación a formato Excel (.xlsx)

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Línea de negocio: Categoría del producto
    - Tienda: Nombre de la tienda (Comdiel)

Dependencias:
    pip install requests beautifulsoup4 pandas openpyxl

Uso:
    python Bot-recolector-Comdiel.py
    
Salida:
    Genera el archivo 'Base_Datos_Comdiel.xlsx' en la carpeta 'TIENDAS/'

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Comdiel"
DOMAIN = "https://www.comdiel.cl"

# Lista de Categorías
categorias = [
    ("Cableado Estructurado", "https://www.comdiel.cl/cableado-estructurado"),
    ("Fibra Óptica", "https://www.comdiel.cl/fibra-optica"),
    ("Telefonía", "https://www.comdiel.cl/telefonia"),
    ("Racks", "https://www.comdiel.cl/racks"),
    ("Networking", "https://www.comdiel.cl/networking"),
    ("Energía", "https://www.comdiel.cl/energia"),
    ("Seguridad", "https://www.comdiel.cl/seguridad"),
    ("Telemetría", "https://www.comdiel.cl/telemetria")
]

datos_totales = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

print(f"--- INICIANDO RECOLECCIÓN (REEMPLAZO TOTAL): {NOMBRE_TIENDA} ---")

for nombre_cat, url_cat in categorias:
    pagina = 1
    total_cat = 0
    print(f"\n>>> Procesando: {nombre_cat}")
    
    fallos_consecutivos = 0 
    
    while True:
        url_actual = f"{url_cat}?page={pagina}"
        response = None
        exito = False
        
        # --- SISTEMA DE REINTENTOS ---
        for intento in range(1, 4): 
            try:
                print(f"   Pág {pagina} (Intento {intento})...", end=" ")
                response = requests.get(url_actual, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    exito = True
                    fallos_consecutivos = 0
                    break
                else:
                    print(f"[Error {response.status_code}]", end=" ")
                    time.sleep(2)
            except Exception as e:
                print(f"[Fallo conexión]", end=" ")
                time.sleep(3)
        
        # --- ANÁLISIS DEL RESULTADO ---
        if not exito:
            print("-> Se saltó esta página por errores persistentes.")
            fallos_consecutivos += 1
            if fallos_consecutivos >= 5:
                print("!!! Demasiados errores seguidos. Pasando a siguiente categoría.")
                break
            pagina += 1
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        bloques = soup.find_all('div', class_='product-block')
        
        if not bloques:
            print("-> No hay más productos (Fin categoría).")
            break

        cantidad_pagina = len(bloques) 
        total_cat += cantidad_pagina   
        print(f"({cantidad_pagina} productos)")  
        
        for bloque in bloques:
            try:
                etiqueta_titulo = bloque.find('h4')
                if etiqueta_titulo:
                    nombre = etiqueta_titulo.text.strip()
                    link_parcial = etiqueta_titulo.find('a')['href']
                else:
                    link_obj = bloque.find('div', class_='caption').find('a')
                    nombre = link_obj.text.strip()
                    link_parcial = link_obj['href']
                
                if not link_parcial.startswith('http'):
                    link_final = f"{DOMAIN}{link_parcial}"
                else:
                    link_final = link_parcial
                
                datos_totales.append({
                    'Producto': nombre,
                    'Link': link_final,
                    'Línea de negocio': nombre_cat,
                    'Tienda': NOMBRE_TIENDA
                })
            except:
                continue

        pagina += 1
        time.sleep(random.uniform(0.5, 1.5))  # Optimizado: antes 0.5-3.5s

    print(f"--- Fin {nombre_cat}: {total_cat} productos recolectados ---")

# --- GUARDADO FINAL (REEMPLAZO) ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    # Ordenar y limpiar duplicados de la recolección actual
    columnas_ordenadas = ['Producto', 'Link', 'Línea de negocio', 'Tienda']
    df = df[columnas_ordenadas]
    df = df.drop_duplicates(subset=['Link'], keep='first')
    
    # 1. Definir carpeta TIENDAS
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # 2. Crear carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    # 3. Definir ruta del archivo
    nombre_archivo = "Base_Datos_Comdiel.xlsx" 
    ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
    
    try:
        df.to_excel(ruta_completa, index=False)
        print("\n" + "="*50)
        print(f"¡PROCESO COMPLETADO!")
        print(f"Se ha reemplazado/creado el archivo con los datos nuevos.")
        print(f"Total productos guardados: {len(df)}")
        print(f"Ubicación: {ruta_completa}")
        print("="*50)
    except ModuleNotFoundError:
        print("\nERROR: Falta la librería 'openpyxl'.")
    except Exception as e:
        print(f"\nError al guardar el Excel: {e}")
        
else:
    print("No se encontraron datos.")