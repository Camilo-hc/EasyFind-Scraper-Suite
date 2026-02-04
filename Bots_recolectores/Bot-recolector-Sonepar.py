"""
Bot Recolector de Productos - Sonepar Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Sonepar (https://shop.sonepar.cl), un distribuidor líder de materiales eléctricos,
automatización, iluminación y soluciones energéticas en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y renderizado de JavaScript
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación en modo headless (invisible)
    - Sistema robusto de reintentos (3 intentos por página)
    - Paginación mediante parámetros en URL con formato de plantilla
    - Detección de páginas duplicadas mediante comparación de links
    - Límite de seguridad (máximo 200 páginas por categoría)
    - Esperas aleatorias entre páginas (1.5-3 segundos)
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - URLs con Plantilla:
    Las URLs de categorías incluyen {} como marcador de posición para el
    número de página, permitiendo una paginación dinámica eficiente.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Sonepar)

Dependencias:
    pip install selenium pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Sonepar.py
    
Salida:
    Genera el archivo 'Base_Datos_Sonepar.xlsx' en la carpeta 'TIENDAS/'

"""

import time
import pandas as pd
import random
import os
import sys

# --- IMPORTACIONES ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Sonepar"
DOMAIN = "https://shop.sonepar.cl"
MAX_INTENTOS = 3  # Número de veces que intentará si falla la carga

# Lista de categorías
categorias = [
    ("Automatización", "https://shop.sonepar.cl/products?text=&categories=6&brands=&pdmsModifiers=&pdmsParticulars=&type=&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators=&page={}"),
    ("Cableado Estructurado y Accesorios", "https://shop.sonepar.cl/products?text=&categories=14&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Cables y Alambres", "https://shop.sonepar.cl/products?text=&categories=1&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Calidad de Energía y Respaldo", "https://shop.sonepar.cl/products?text=&categories=8&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Canalizaciones y Accesorios", "https://shop.sonepar.cl/products?text=&categories=2&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Control Industrial y Señalización", "https://shop.sonepar.cl/products?text=&categories=5&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Electromovilidad y Electrificación", "https://shop.sonepar.cl/products?text=&categories=269&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Enchufes Industriales", "https://shop.sonepar.cl/products?text=&categories=7&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Ferreteria Eléctrica", "https://shop.sonepar.cl/products?text=&categories=7&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Instrumentos y Herramientas", "https://shop.sonepar.cl/products?text=&categories=11&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Lamparas y Accesorios", "https://shop.sonepar.cl/products?text=&categories=12&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Luminarias", "https://shop.sonepar.cl/products?text=&categories=13&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Placas Interruptores Enchufes Cajas", "https://shop.sonepar.cl/products?text=&categories=3&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Protecciones Eléctricas", "https://shop.sonepar.cl/products?text=&categories=4&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators="),
    ("Tableros, Gabinetes y Accesorios", "https://shop.sonepar.cl/products?text=&categories=9&brands=&pdmsModifiers=&pdmsParticulars=&type=&page={}&order=relevance&isFilterUpdate=1&minPrice=&maxPrice=&greenIndicators=")
]

datos_totales = []

# --- CONFIGURACIÓN DEL NAVEGADOR ---
print(">>> Configurando navegador en modo oculto...")
chrome_options = Options()
chrome_options.add_argument("--headless=new") 
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--log-level=3") 
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# Optimizaciones de rendimiento
chrome_options.add_argument("--disable-images")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print(">>> Navegador iniciado correctamente.")
except Exception as e:
    sys.exit(f"Error crítico al iniciar Chrome: {e}")

print(f"--- INICIANDO RECOLECCIÓN: {NOMBRE_TIENDA} ---")

for nombre_cat, url_plantilla in categorias:
    pagina = 1
    print(f"\nProcesando: {nombre_cat}")
    
    links_pagina_anterior = [] 

    while True:
        url_actual = url_plantilla.format(pagina)
        
        # Límite de seguridad
        if pagina > 200: 
            print("   -> Límite de seguridad alcanzado.")
            break

        datos_esta_pagina = []
        links_esta_pagina = []
        lectura_exitosa = False # Bandera para saber si logramos leer la página

        # --- SISTEMA DE REINTENTOS ---
        for intento in range(1, MAX_INTENTOS + 1):
            try:
                print(f"   Leyendo Pág {pagina} (Intento {intento}/{MAX_INTENTOS})...", end=" ")
                driver.get(url_actual)
                
                # Espera de carga
                try:
                    WebDriverWait(driver, 6).until(  # Optimizado: antes 10s
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/products/')]"))
                    )
                except TimeoutException:
                    raise Exception("Tiempo de espera agotado buscando productos")

                elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/products/')]")
                
                if not elementos:
                    raise Exception("Lista de elementos vacía")

                # PROCESAMIENTO
                for elem in elementos:
                    try:
                        nombre_prod = elem.text.strip()
                        link_parcial = elem.get_attribute('href')
                        
                        if not nombre_prod or len(nombre_prod) < 3: continue
                        
                        if not link_parcial.startswith("http"):
                            link_final = f"{DOMAIN}{link_parcial}"
                        else:
                            link_final = link_parcial

                        if link_final in links_esta_pagina: continue

                        datos_esta_pagina.append({
                            'Producto': nombre_prod,
                            'Link': link_final,
                            'Categoría': nombre_cat,
                            'Tienda': NOMBRE_TIENDA
                        })
                        links_esta_pagina.append(link_final)
                    except:
                        continue
                
                # Si llegamos aquí sin errores, marcamos éxito y salimos del bucle de intentos
                lectura_exitosa = True
                print(f"OK ({len(datos_esta_pagina)} prods)")
                break 

            except Exception as e:
                print(f"[X] Falló: {e}")
                if intento < MAX_INTENTOS:
                    tiempo_espera = random.uniform(1.5, 3.0)  # Optimizado: antes 2-5s
                    print(f"   ... Reintentando en {tiempo_espera:.1f} segs ...")
                    time.sleep(tiempo_espera)
                else:
                    print("   -> Se acabaron los intentos para esta página.")

        # --- VALIDACIONES POST-LECTURA ---
        
        if not lectura_exitosa:
            print("-> No se pudo leer la página tras varios intentos. Pasando a siguiente categoría.")
            break

        if not datos_esta_pagina:
            print("-> 0 productos capturados. Fin.")
            break
        
        if links_esta_pagina == links_pagina_anterior:
            print(f"   -> [STOP] La página {pagina} es idéntica a la anterior. Fin real.")
            break
        
        datos_totales.extend(datos_esta_pagina)
        links_pagina_anterior = links_esta_pagina
        
        pagina += 1
        time.sleep(random.uniform(0.8, 1.5))  # Optimizado: antes 1.5-3.0s

driver.quit()

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    # 1. Asegurar orden exacto de columnas
    if 'Categoría' in df.columns:
        cols = ['Producto', 'Link', 'Categoría', 'Tienda']
        df = df[[c for c in cols if c in df.columns]]
    
    # 2. Eliminar duplicados
    df = df.drop_duplicates(subset=['Link'])
    
    # --- CAMBIO DE RUTA A CARPETA TIENDAS ---
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # Crear carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada: {ruta_carpeta}")
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    nombre_archivo = f"Base_Datos_{NOMBRE_TIENDA}.xlsx"
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
        print("\n" + "="*60)
        print(f"¡PROCESO COMPLETADO!")
        print(f"Total productos guardados: {len(df)}")
        print(f"Archivo Excel generado en: {ruta_completa}")
        print("="*60)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("\nNo se obtuvieron datos.")