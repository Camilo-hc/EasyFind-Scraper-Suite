"""
Bot Recolector de Productos - Automatec Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Automatec (https://www.automatec.cl), una tienda especializada en seguridad electrónica,
CCTV, automatización, control de acceso y sistemas de alarmas en Chile.

Tecnología utilizada:
    - requests: Para realizar peticiones HTTP
    - BeautifulSoup: Para parsear y extraer datos del HTML
    - pandas: Para estructurar y exportar datos a Excel
    
Características principales:
    - Sistema robusto de reintentos (3 intentos por página)
    - Paginación automática mediante parámetros URL (?page=X)
    - Detección múltiple de fin de categoría (404, mensajes de texto)
    - Selectores CSS flexibles para diferentes versiones del sitio
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Automatec)

Dependencias:
    pip install requests beautifulsoup4 pandas openpyxl

Uso:
    python Bot-recolector-Automatec.py
    
Salida:
    Genera el archivo 'Base_Datos_Automatec.xlsx' en la carpeta 'TIENDAS/'

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Automatec"
DOMAIN = "https://www.automatec.cl"

# Lista de Categorías
categorias = [
    ("Ajax", "https://www.automatec.cl/tienda/327-ajax"),
    ("CCTV", "https://www.automatec.cl/tienda/18-cctv"),
    ("Automatización", "https://www.automatec.cl/tienda/24-automatizacion"),
    ("Alarmas", "https://www.automatec.cl/tienda/47-alarmas"),
    ("Control de Acceso", "https://www.automatec.cl/tienda/30-control-de-acceso"),
    ("Cerco Eléctrico", "https://www.automatec.cl/tienda/27-cerco-electrico"),
    ("Citofonía y Videoportero", "https://www.automatec.cl/tienda/80-citofonia-y-videoportero"),
    ("Incendio", "https://www.automatec.cl/tienda/309-incendio"),
    ("Almacenamiento", "https://www.automatec.cl/tienda/36-almacenamiento"),
    ("Cableado Estructurado", "https://www.automatec.cl/tienda/49-cableado-estructurado"),
    ("Conectividad", "https://www.automatec.cl/tienda/168-conectividad"),
    ("Digital Signage", "https://www.automatec.cl/tienda/145-digital-signage"),
    ("Ferretería", "https://www.automatec.cl/tienda/72-ferreteria")
]

datos_totales = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.automatec.cl/tienda/",
}

print(f"--- INICIANDO RECOLECCIÓN ROBUSTA: {NOMBRE_TIENDA} ---")

for nombre_cat, url_cat in categorias:
    pagina = 1
    total_categoria = 0
    print(f"\n>>> Procesando: {nombre_cat}")
    
    while True:
        url_actual = url_cat if pagina == 1 else f"{url_cat}?page={pagina}"
        
        exito = False
        for intento in range(1, 4): 
            try:
                print(f"   Leyendo Pág {pagina}...", end=" ")
                response = requests.get(url_actual, headers=headers, timeout=20)
                if response.status_code == 200:
                    exito = True
                    break
                elif response.status_code == 404:
                    print("[Fin de categoría - 404]")
                    exito = False
                    break
                time.sleep(2)
            except Exception:
                time.sleep(2)
        
        if not exito:
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        bloques = soup.select('.product-miniature') or soup.select('.ajax_block_product')

        if not bloques:
            if "No hay productos" in soup.text or "no existen productos" in soup.text.lower():
                print("[Fin: No hay más productos]")
            else:
                print("-> Lista vacía (Posible cambio de diseño).")
            break
            
        print(f"({len(bloques)} detectados)", end=" ")
        
        productos_pagina_actual = 0
        for bloque in bloques:
            try:
                etiqueta_titulo = bloque.select_one('.product-title a, .product-name a, h3.h3.product-title a')
                if etiqueta_titulo:
                    nombre = etiqueta_titulo.text.strip()
                    link_parcial = etiqueta_titulo['href']
                else:
                    link_obj = bloque.find('a')
                    if link_obj and 'href' in link_obj.attrs:
                        nombre = link_obj.get('title', 'Producto sin nombre').strip()
                        if not nombre:
                            img = bloque.find('img')
                            nombre = img.get('alt', 'Producto sin nombre') if img else "Producto sin nombre"
                        link_parcial = link_obj['href']
                    else:
                        continue
                
                link_final = link_parcial if link_parcial.startswith('http') else f"{DOMAIN}{link_parcial}"
                
                datos_totales.append({
                    'Producto': nombre,
                    'Link': link_final,
                    'Categoría': nombre_cat,
                    'Tienda': NOMBRE_TIENDA
                })
                productos_pagina_actual += 1
                total_categoria += 1

            except Exception:
                continue
        
        print(f"-> OK ({productos_pagina_actual} procesados)")
        
        if productos_pagina_actual == 0:
            break

        pagina += 1
        time.sleep(random.uniform(0.6, 1.2))  # Optimizado: antes 1.0-2.0s
    
    print(f"--- TOTAL {nombre_cat.upper()}: {total_categoria} productos encontrados ---")

# --- GUARDADO FINAL ---
if datos_totales:
    # 1. Preparar DataFrame
    df = pd.DataFrame(datos_totales)
    # Reordenar columnas para mantener consistencia visual si se desea (opcional)
    if 'Categoría' in df.columns:
        cols = ['Producto', 'Link', 'Categoría', 'Tienda']
        # Asegurarse que existan todas
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
    
    df = df.drop_duplicates(subset=['Link'])
    
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # 2. Crear carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada: {ruta_carpeta}")
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    nombre_archivo = "Base_Datos_Automatec.xlsx"
    ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
    
    # 3. ELIMINAR ARCHIVO SI YA EXISTE (Para asegurar reemplazo)
    if os.path.exists(ruta_completa):
        try:
            os.remove(ruta_completa)
            print(f"Archivo previo eliminado para ser reemplazado: {nombre_archivo}")
        except PermissionError:
            print(f"⚠️ ADVERTENCIA: El archivo '{nombre_archivo}' está abierto. Ciérralo para permitir el reemplazo.")
    
    # 4. Guardar el nuevo archivo
    try:
        df.to_excel(ruta_completa, index=False)
        print("\n" + "="*50)
        print(f"¡PROCESO COMPLETADO!")
        print(f"Total productos guardados: {len(df)}")
        print(f"Archivo Excel generado en: {ruta_completa}")
        print("="*50)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("No se encontraron datos.")