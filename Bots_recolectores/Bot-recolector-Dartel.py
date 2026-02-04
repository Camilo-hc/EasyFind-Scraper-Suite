"""
Bot Recolector de Productos - Dartel Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Dartel (https://www.dartel.cl), una tienda especializada en materiales eléctricos,
automatización, iluminación y distribución eléctrica en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y renderizado de JavaScript
    - BeautifulSoup: Para parsear el HTML renderizado
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación con Selenium en modo headless (invisible)
    - Optimizaciones de velocidad (desactivación de imágenes, carga eager)
    - Sistema de reintentos con reinicio de navegador (3 intentos por página)
    - Scroll automático para cargar contenido dinámico
    - Selectores flexibles para diferentes estructuras HTML (VTEX)
    - Paginación automática mediante parámetros URL (?page=X)
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Navegador Selenium:
    Este bot requiere Google Chrome instalado en el sistema. El ChromeDriver
    se descarga automáticamente mediante webdriver_manager.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Línea de negocio: Categoría del producto
    - Tienda: Nombre de la tienda (Dartel)

Dependencias:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Dartel.py
    
Salida:
    Genera el archivo 'Base_Datos_Dartel.xlsx' en la carpeta 'TIENDAS/'
"""

import time
import pandas as pd
import random
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Dartel"
DOMAIN = "https://www.dartel.cl"

categorias = [
    ("Automatización", "https://www.dartel.cl/automatizacion-y-control"), 
    ("Calidad de Energia", "https://www.dartel.cl/calidad-de-energia"),   
    ("Canalizaciones", "https://www.dartel.cl/canalizaciones"),             
    ("Conductores", "https://www.dartel.cl/conductores"),
    ("Conectividad y Redes", "https://www.dartel.cl/conectividad-y-redes"),
    ("Distribución Eléctrica", "https://www.dartel.cl/distribucion-electrica"),
    ("Energías Renovables", "https://www.dartel.cl/energias-renovables-y-electromovilidad"),
    ("Ferretería Eléctrica", "https://www.dartel.cl/ferreteria-electrica"),
    ("Iluminación", "https://www.dartel.cl/iluminacion"),
    ("Instalaciones Residenciales", "https://www.dartel.cl/instalaciones-residenciales"),
    ("Instrumentos de Medidas", "https://www.dartel.cl/instrumentos-de-medidas"),
    ("Ley de Ductos", "https://www.dartel.cl/ley-de-ductos"),
    ("Materiales A Prueba de Explosión", "https://www.dartel.cl/materiales-a-prueba-de-explosion-apex"),
    ("Media Tensión", "https://www.dartel.cl/media-tension"),
    ("Motores Eléctricos", "https://www.dartel.cl/motores-electricos"),
    ("Otros", "https://www.dartel.cl/otros"),
    ("Respaldo Energético", "https://www.dartel.cl/respaldo-energetico"),
    ("Seguridad Electrónica", "https://www.dartel.cl/seguridad-electronica"),
    ("Sistema de Conexión a Tierra", "https://www.dartel.cl/sistema-de-conexion-a-tierra"),
    ("Soluciones Clínicas", "https://www.dartel.cl/soluciones-clinicas-hospitalarias"),
    ("Tableros y Armarios", "https://www.dartel.cl/tableros-y-armarios")
]

datos_totales = []

# --- FUNCIÓN AUXILIAR PARA INICIAR EL NAVEGADOR (OPTIMIZADA) ---
def iniciar_navegador():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    
    # --- OPTIMIZACIONES DE VELOCIDAD ---
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

print(f"--- INICIANDO RECOLECCIÓN OPTIMIZADA: {NOMBRE_TIENDA} ---")

# --- BUCLE PRINCIPAL POR CATEGORÍA ---
for nombre_cat, url_cat in categorias:
    print(f"\n>>> INICIANDO BLOQUE: {nombre_cat}")
    
    contador_categoria = 0
    driver = None 
    pagina = 1
    
    try:
        driver = iniciar_navegador()
        
        while True:
            url_actual = f"{url_cat}?page={pagina}"
            exito_pagina = False
            
            for intento in range(1, 4):
                try:
                    if driver is None:
                        print(f"   (Reiniciando navegador para Pág {pagina})...")
                        driver = iniciar_navegador()

                    if intento > 1:
                        print(f"   Reintentando Pág {pagina} ({intento}/3)...", end=" ")
                    else:
                        print(f"   Pág {pagina}...", end=" ")

                    driver.get(url_actual)
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                    time.sleep(1) 
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2.5) 
                    
                    html_renderizado = driver.page_source
                    soup = BeautifulSoup(html_renderizado, 'html.parser')

                    bloques = soup.find_all(lambda tag: tag.name in ['section', 'div', 'a'] and 
                                            tag.get('class') and 
                                            any('vtex-product-summary-2-x-container' in c for c in tag.get('class')))
                    
                    if not bloques:
                         bloques = soup.find_all(lambda tag: tag.name == 'div' and 
                                            tag.get('class') and 
                                            any('vtex-search-result-3-x-galleryItem' in c for c in tag.get('class')))

                    if not bloques:
                        print("-> 0 productos. Fin de la categoría.")
                        exito_pagina = True 
                        driver.quit() 
                        driver = None
                        break 
                    
                    print(f"({len(bloques)} encontrados)")
                    
                    productos_pagina_actual = 0
                    
                    for bloque in bloques:
                        try:
                            # LINK
                            link_obj = bloque.find('a', class_=lambda x: x and 'vtex-product-summary-2-x-clearLink' in x)
                            if not link_obj: link_obj = bloque.find('a', href=True)
                            
                            if link_obj and 'href' in link_obj.attrs:
                                link_parcial = link_obj['href']
                                link_final = f"{DOMAIN}{link_parcial}" if not link_parcial.startswith('http') else link_parcial
                            else:
                                continue

                            # NOMBRE
                            nombre_obj = bloque.find(class_=lambda x: x and 'vtex-product-summary-2-x-productBrand' in x)
                            if nombre_obj:
                                nombre = nombre_obj.text.strip()
                            else:
                                nombre_alt = bloque.find('h3')
                                nombre = nombre_alt.text.strip() if nombre_alt else "Nombre no detectado"

                            datos_totales.append({
                                'Producto': nombre,
                                'Link': link_final,
                                'Línea de negocio': nombre_cat,
                                'Tienda': NOMBRE_TIENDA
                            })
                            productos_pagina_actual += 1
                            contador_categoria += 1
                            
                        except Exception:
                            continue
                    
                    if productos_pagina_actual == 0:
                        raise Exception("Bloques vacíos (Error de carga)")

                    exito_pagina = True
                    break 

                except Exception as e:
                    print(f"[Fallo: {str(e)[:40]}...]", end=" ")
                    if driver:
                        try: driver.quit()
                        except: pass
                    driver = None
                    time.sleep(2)
            
            if not exito_pagina:
                print(f"\n!!! Pág {pagina} imposible de leer. Saltando.")
                pagina += 1
                continue
            
            if not bloques and exito_pagina:
                break
                
            pagina += 1

    except Exception as e:
        print(f"\nError general en categoría {nombre_cat}: {e}")
    
    finally:
        
        if driver:
            try: driver.quit()
            except: pass
            
    print(f">>> FINALIZADA {nombre_cat}. Total recolectado: {contador_categoria} productos.\n")

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    df = df[['Producto', 'Link', 'Línea de negocio', 'Tienda']]
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

    nombre_archivo = "Base_Datos_Dartel.xlsx" 
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
        print(f"Archivo guardado (reemplazado) en: {ruta_completa}")
        print("="*50)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("No se encontraron datos.")