"""
Bot Recolector de Productos - EECOL Chile

Este script automatiza la recolección de información de productos desde el sitio web
de EECOL (https://eecol.cl), una tienda especializada en materiales eléctricos y 
automatización en Chile.

Tecnología utilizada:
    - requests: Para realizar peticiones HTTP
    - BeautifulSoup: Para parsear y extraer datos del HTML
    - pandas: Para estructurar y exportar datos a Excel
    
Características principales:
    - Sistema de reintentos automáticos ante fallos de conexión
    - Paginación automática mediante parámetros URL (?page=X)
    - Detección inteligente de fin de categoría (404, páginas vacías)
    - Eliminación de duplicados por URL
    - Exportación a formato Excel (.xlsx)

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Línea de negocio: Categoría del producto
    - Tienda: Nombre de la tienda (EECOL)

Dependencias:
    pip install requests beautifulsoup4 pandas openpyxl

Uso:
    python Bot-recolector-EECOL.py
    
Salida:
    Genera el archivo 'Base_Datos_EECOL.xlsx' en la carpeta 'TIENDAS/'

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
NOMBRE_TIENDA = "EECOL"

# Dominio base del sitio web (usado para construir URLs absolutas)
DOMAIN = "https://eecol.cl"

# Lista de categorías a procesar: (Nombre de categoría, URL de categoría)
# Cada tupla contiene el nombre descriptivo y la URL completa de la categoría
categorias = [
    ("Control y Maniobra", "https://eecol.cl/335-control-y-maniobra"),
    ("Protecciones", "https://eecol.cl/299-protecciones"),
    ("Accionamiento y Motores", "https://eecol.cl/509-accionamiento-y-motores"),
    ("Iluminación", "https://eecol.cl/304-iluminacion"),
    ("Conductores Eléctricos", "https://eecol.cl/355-conductores-electricos"),
    ("Canalización", "https://eecol.cl/308-canalizacion"),
    ("Materiales Eléctricos", "https://eecol.cl/292-materiales-electricos"),
    ("Comunicaciones", "https://eecol.cl/279-comunicaciones"),
    ("Respaldo de Energia", "https://eecol.cl/801-respaldo-de-energia"),
    ("Automatización e Instrumentación", "https://eecol.cl/6000-automatizacion-e-instrumentacion"),
    ("Sistema Puesta a Tierra", "https://eecol.cl/6304-sistema-puesta-a-tierra"),
    ("Media Tension", "https://eecol.cl/388-media-tension"),
    ("Calidad de Energia", "https://eecol.cl/808-calidad-de-energia"),
    ("Cajas y Tableros", "https://eecol.cl/6804-cajas-y-tableros")
]

# Lista que almacenará todos los productos recolectados de todas las categorías
datos_totales = []

# ============================================================================
# CONFIGURACIÓN DE HEADERS HTTP
# ============================================================================
# Headers personalizados para simular un navegador real y evitar bloqueos
# del servidor. Incluye User-Agent actualizado y configuración de idioma.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

# ============================================================================
# INICIO DEL PROCESO DE RECOLECCIÓN
# ============================================================================
print(f"--- INICIANDO RECOLECCIÓN (SALIDA EXCEL): {NOMBRE_TIENDA} ---")

# Iterar sobre cada categoría definida en la configuración
for nombre_cat, url_cat in categorias:
    pagina = 1  # Contador de páginas para la paginación
    print(f"\n>>> Procesando: {nombre_cat}")
    
    total_categoria = 0  # Contador de productos encontrados en esta categoría
    fallos_consecutivos = 0  # Contador de fallos para evitar loops infinitos
    
    # Loop de paginación: continúa hasta que no haya más páginas
    while True:
        # ====================================================================
        # CONSTRUCCIÓN DE URL CON PAGINACIÓN
        # ====================================================================
        # PrestaShop usa el parámetro ?page=X para la paginación
        url_actual = f"{url_cat}?page={pagina}"
        response = None
        exito = False
        
        # ====================================================================
        # SISTEMA DE REINTENTOS (3 intentos por página)
        # ====================================================================
        # Implementa resiliencia ante fallos temporales de red o servidor
        for intento in range(1, 4): 
            try:
                print(f"   Pág {pagina} (Intento {intento})...", end=" ")
                response = requests.get(url_actual, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    exito = True
                    fallos_consecutivos = 0
                    break
                elif response.status_code == 404:
                    print("[Fin de categoría detectado por 404]")
                    exito = False
                    break
                else:
                    print(f"[Error {response.status_code}]", end=" ")
                    time.sleep(2)
            except Exception as e:
                print(f"[Fallo conexión]", end=" ")
                time.sleep(3)
        
        if not exito and response and response.status_code == 404:
             break 

        # --- ANÁLISIS DEL RESULTADO ---
        if not exito:
            print("-> Se saltó esta página por errores persistentes.")
            fallos_consecutivos += 1
            if fallos_consecutivos >= 3:
                print("!!! Demasiados errores seguidos. Pasando a siguiente categoría.")
                break
            pagina += 1
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        
        bloques = soup.find_all('article', class_='product-miniature')
        
        if not bloques:
            print("-> No hay más productos (Fin categoría).")
            break
            
        print(f"({len(bloques)} productos en pág)")
        
        productos_nuevos_en_pagina = 0

        # Procesar cada bloque de producto encontrado en la página
        for bloque in bloques:
            try:
                # ============================================================
                # EXTRACCIÓN DE DATOS DEL PRODUCTO
                # ============================================================
                # Paso 1: Buscar el título del producto (contiene nombre y link)
                etiqueta_titulo = bloque.find('h2', class_='product-title')
                
                if etiqueta_titulo:
                    link_obj = etiqueta_titulo.find('a')
                    nombre = link_obj.text.strip()  # Nombre del producto
                    link_parcial = link_obj['href']  # URL del producto
                else:
                    # Si no se encuentra el título, saltar este producto
                    continue
                
                # ============================================================
                # CONSTRUCCIÓN DE URL COMPLETA
                # ============================================================
                # Convertir URLs relativas a absolutas si es necesario
                if not link_parcial.startswith('http'):
                    link_final = f"{DOMAIN}{link_parcial}"
                else:
                    link_final = link_parcial
                
                # ============================================================
                # ALMACENAMIENTO DE DATOS
                # ============================================================
                # Agregar el producto a la lista con estructura estandarizada
                datos_totales.append({
                    'Producto': nombre,
                    'Link': link_final,
                    'Línea de negocio': nombre_cat,
                    'Tienda': NOMBRE_TIENDA
                })
                productos_nuevos_en_pagina += 1
            except Exception as e:
                # Si hay error en un producto individual, continuar con el siguiente
                continue
        
        total_categoria += productos_nuevos_en_pagina

        if productos_nuevos_en_pagina == 0:
            print("-> Página cargada pero sin productos válidos (Posible fin).")
            break

        pagina += 1
        time.sleep(random.uniform(0.7, 1.5))  # Optimizado: antes 1.0-3.0s 

    print(f"--- Fin de {nombre_cat}. Total recolectado: {total_categoria} productos ---")

# ============================================================================
# GUARDADO FINAL EN EXCEL (.xlsx)
# ============================================================================
if datos_totales:
    # Paso 1: Convertir la lista de diccionarios a DataFrame de pandas
    df = pd.DataFrame(datos_totales)
    
    # Paso 2: Ordenar las columnas en el orden deseado para mejor legibilidad
    columnas_ordenadas = ['Producto', 'Link', 'Línea de negocio', 'Tienda']
    df = df[columnas_ordenadas]
    
    # Paso 3: Eliminar productos duplicados basándose en el Link
    # Mantiene la primera ocurrencia de cada producto único
    df = df.drop_duplicates(subset=['Link'], keep='first')
    
    # ========================================================================
    # CONFIGURACIÓN DE RUTA DE GUARDADO
    # ========================================================================
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # Paso 4: Crear carpeta TIENDAS si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada: {ruta_carpeta}")
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    nombre_archivo = "Base_Datos_EECOL.xlsx" 
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