"""
Bot Recolector de Productos - Intcomex Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Intcomex (https://store.intcomex.com), un distribuidor mayorista de tecnología,
computación, redes, software y seguridad electrónica en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y renderizado de JavaScript
    - BeautifulSoup: Para parsear el HTML renderizado (opcional)
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación en modo headless (invisible)
    - Paginación mediante parámetros URL (?p=X)
    - Detección de páginas duplicadas mediante comparación de links
    - Sistema de límite de seguridad (máximo 50 páginas por categoría)
    - Extracción mediante XPath para mayor precisión
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Detección de Duplicados:
    Este bot compara los links de cada página con la anterior para detectar
    cuando el sitio web comienza a repetir productos (fin real de categoría).

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Intcomex)

Dependencias:
    pip install selenium pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Intcomex.py
    
Salida:
    Genera el archivo 'Base_Datos_Intcomex.xlsx' en la carpeta 'TIENDAS/'

"""

import time
import pandas as pd
import random
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Intcomex"
DOMAIN = "https://store.intcomex.com"

categorias = [
    # Computación
    ("Computo - Cables", "https://store.intcomex.com/es-XCL/Products/ByCategory/cac.cable"),
    ("Computo - Seguridad","https://store.intcomex.com/es-XCL/Products/ByCategory/cac.security?r=True"),
    ("Computo - Accesorios para Servidores", "https://store.intcomex.com/es-XCL/Products/ByCategory/cac.server?r=True"),
    ("Computo - Accesorios para Computadores de Mesa", "https://store.intcomex.com/es-XCL/Products/ByCategory/cac.desktop?r=True"),
    ("Computo - Servidores", "https://store.intcomex.com/es-XCL/Products/ByCategory/cpt.server?r=True"),
    ("Computo - Adaptadores y Controladores", "https://store.intcomex.com/es-XCL/Products/ByCategory/cco.adapter?r=True"),
    ("Computo - Sistemas de Enfriamiento", "https://store.intcomex.com/es-XCL/Products/ByCategory/cco.cool?r=True"),
    ("Computo - Accesorios de Protección", "https://store.intcomex.com/es-XCL/Products/ByCategory/ups.accessory?r=True"),
    ("Computo - Protectores", "https://store.intcomex.com/es-XCL/Products/ByCategory/ups.surge?r=True"),
    ("Computo - Respaldo de Energía", "https://store.intcomex.com/es-XCL/Products/ByCategory/ups.ups?r=True"),
    ("Computo - Reguladores en Línea", "https://store.intcomex.com/es-XCL/Products/ByCategory/ups.regulator?r=True"),
    ("Computo - Accesorios de Almacenamiento", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.acc?r=True"),
    ("Computo  - Disco Duro Externo", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.exthd?r=True"),
    ("Computo - Disco Duro Interno", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.inthd?r=True"),
    ("Computo - Almacenamiento de Redes", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.nw?r=True"),
    ("Computo - Disco de Estado Solido Interno", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.ssd?r=True"),
    ("Computo - Cintas de Almacenamiento", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.tape?r=True"),
    ("Computo - Disco de Estado Solido Externo", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.ssdext?r=True"),

    # Software
    ("Software - Aplicaciones para Negocios y Oficina", "https://store.intcomex.com/es-XCL/Products/ByCategory/sfw.business?r=True"),
    ("Software - Servidores Enterprise", "https://store.intcomex.com/es-XCL/Products/ByCategory/sfw.enterprise?r=True"),
    ("Sotware - Sistemas Operativos", "https://store.intcomex.com/es-XCL/Products/ByCategory/sfw.os?r=True"),
    ("Software - Microsoft", "https://store.intcomex.com/es-XCL/Products/ByDownloables?r=True&b=msf"),
    
    # Redes
    ("Redes - Telefonos IP", "https://store.intcomex.com/es-XCL/Products/ByCategory/com.ipphone?r=True"),
    ("Redes - Video Conferencia", "https://store.intcomex.com/es-XCL/Products/ByCategory/com.video?r=True"),
    ("Redes - Almacenamiento Redes", "https://store.intcomex.com/es-XCL/Products/ByCategory/sto.nw?r=True"),
    ("Redes - Servidores", "https://store.intcomex.com/es-XCL/Products/ByCategory/cpt.server?r=True"),
    ("Redes - Accesorios", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.acc?r=True"),
    ("Redes - Puntos de Acceso", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.accpoint?r=True"),
    ("Redes - Adaptadores y Controladores", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.nwadapter?r=True"),
    ("Redes - Antenas", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.antenna?r=True"),
    ("Redes - Puentes y Enrutadores", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.router?r=True"),
    ("Redes - Cables", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.nwcable?r=True"),
    ("Redes - Accesorios para Cableo", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.cableacc?r=True"),
    ("Redes - Conectores", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.nwconnect?r=True"),
    ("Redes - Modulos de Expansion", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.expansion?r=True"),
    ("Redes - Hubs & Switches", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.hubswitch?r=True"),
    ("Redes - KVM Switches, Consolas y Splitters", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.kvm?r=True"),
    ("Redes - Placas y Soported de Pared", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.wallplate?r=True"),
    ("Redes - Paneles, Gabinetes y Cajas de Redes", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.rackpanel?r=True"),
    ("Redes - Herramientas y Equipo de Herramientas", "https://store.intcomex.com/es-XCL/Products/ByCategory/net.nwtool?r=True"),

    # Electrónica
    ("Electrónica - Accesorios", "https://store.intcomex.com/es-XCL/Products/ByCategory/app.acc?r=True"),
    ("Electrónica - Climatiación", "https://store.intcomex.com/es-XCL/Products/ByCategory/app.heatcool?r=True"),
    ("Electrónica - Accesorios Audio y Video", "https://store.intcomex.com/es-XCL/Products/ByCategory/avs.accessory?r=True"),
    ("Electrónica - Sistemas de Audio", "https://store.intcomex.com/es-XCL/Products/ByCategory/avs.system?r=True"),
    ("Electrónica - Cables", "https://store.intcomex.com/es-XCL/Products/ByCategory/avs.cable?r=True"),
    ("Electrónica - Accesorios para camaras", "https://store.intcomex.com/es-XCL/Products/ByCategory/dca.acc?r=True"),
    ("Electrónica - Camaras Web", "https://store.intcomex.com/es-XCL/Products/ByCategory/dca.webcam?r=True"),

    # Accesorios
    ("Accesorios - Cables y Adaptadores", "https://store.intcomex.com/es-XCL/Products/ByCategory/acc.cable?r=True"),
    
    #Seguridad
    ("Seguridad - Accesorios de Vigilancia", "https://store.intcomex.com/es-XCL/Products/ByCategory/vis.acc?r=True"),
    ("Seguridad - Camaras Analogas", "https://store.intcomex.com/es-XCL/Products/ByCategory/vis.camera?r=True"),
    ("Seguridad - Kits", "https://store.intcomex.com/es-XCL/Products/ByCategory/vis.kit?r=True"),
    ("Seguridad - Camaras de Red", "https://store.intcomex.com/es-XCL/Products/ByCategory/vis.netcam?r=True"),
    ("Seguridad - NVRs", "https://store.intcomex.com/es-XCL/Products/ByCategory/vis.nvr?r=True"),
    ("Seguridad - Accesorios Intrusion", "https://store.intcomex.com/es-XCL/Products/ByCategory/int.acc?r=True"),
    ("Seguridad - Kits Intrusion", "https://store.intcomex.com/es-XCL/Products/ByCategory/int.kit?r=True"),
    ("Seguridad - Paneles y Teclados", "https://store.intcomex.com/es-XCL/Products/ByCategory/int.panel?r=True"),
    ("Seguridad - Sensores", "https://store.intcomex.com/es-XCL/Products/ByCategory/int.sensor?r=True"),
    ("Seguridad - Tarjetas", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.card?r=True"),
    ("Seguridad - Sistema de Puerta", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.door?r=True"),
    ("Seguridad - Kits Control de Acceso", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.kit?r=True"),
    ("Seguridad - Paneles", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.panel?r=True"),
    ("Seguridad - Lectores y Teclados", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.reader?r=True"),
    ("Seguridad - Accesorios de Acceso", "https://store.intcomex.com/es-XCL/Products/ByCategory/act.acc?r=True"),
    ("Seguridad - Accesorios incendio", "https://store.intcomex.com/es-XCL/Products/ByCategory/fir.acc?r=True"),
    ("Seguridad - Dispositivos de Deteccion", "https://store.intcomex.com/es-XCL/Products/ByCategory/fir.detect?r=True"),
    ("Seguridad - Paneles Incendio", "https://store.intcomex.com/es-XCL/Products/ByCategory/fir.panel?r=True")
]

datos_totales = []

# --- CONFIGURACIÓN DEL NAVEGADOR (MODO OCULTO/HEADLESS) ---
print(">>> Configurando navegador en modo oculto...")
chrome_options = Options()
chrome_options.add_argument("--headless") 
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

for nombre_cat, url_base in categorias:
    pagina = 1
    print(f"\nProcesando: {nombre_cat}")
    
    url_limpia = url_base.split('?')[0]
    links_pagina_anterior = [] # Memoria para detectar si la web repite la página

    while True:
        url_actual = f"{url_limpia}?p={pagina}"
        
        # Límite de seguridad
        if pagina > 50: 
            print("   -> Límite de seguridad alcanzado.")
            break

        try:
            print(f"   Leyendo Pág {pagina}...", end=" ")
            driver.get(url_actual)
            
            try:
                # Espera rápida de carga
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/Product/Detail/')]"))
                )
            except:
                print("[No se encontraron productos]")
                break

            elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/Product/Detail/')]")
            
            # Listas temporales para esta página
            datos_esta_pagina = []
            links_esta_pagina = []
            
            for elem in elementos:
                try:
                    nombre_prod = elem.text.strip()
                    link_parcial = elem.get_attribute('href')
                    
                    if not nombre_prod: continue
                    if "Ingresar" in nombre_prod: continue
                    
                    if not link_parcial.startswith("http"):
                        link_final = f"{DOMAIN}{link_parcial}"
                    else:
                        link_final = link_parcial

                    # --- AQUÍ ESTÁN LAS 4 COLUMNAS SOLICITADAS ---
                    datos_esta_pagina.append({
                        'Producto': nombre_prod,
                        'Link': link_final,
                        'Categoría': nombre_cat,
                        'Tienda': NOMBRE_TIENDA
                    })
                    links_esta_pagina.append(link_final)
                    
                except Exception:
                    continue

            # --- LÓGICA DE DETECCIÓN DE FIN ---
            if not datos_esta_pagina:
                print("-> 0 productos capturados. Fin.")
                break
            
            # Si los links son idénticos a los de la vuelta anterior, la web nos devolvió
            if links_esta_pagina == links_pagina_anterior:
                print(f"   -> [STOP] La página {pagina} es idéntica a la anterior. Fin real.")
                break
            
            # Si son nuevos, guardamos
            datos_totales.extend(datos_esta_pagina)
            links_pagina_anterior = links_esta_pagina
            
            print(f"({len(datos_esta_pagina)} productos)")
            
            pagina += 1
            time.sleep(random.uniform(0.6, 1.2))  # Optimizado: antes 1.0-2.0s

        except Exception as e:
            print(f"Error en Pág {pagina}: {e}")
            break

driver.quit()

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    # Ordenar columnas (opcional, por limpieza)
    if 'Producto' in df.columns:
        cols = ['Producto', 'Link', 'Categoría', 'Tienda']
        df = df[[c for c in cols if c in df.columns]]
    
    # Eliminar duplicados exactos de link
    df = df.drop_duplicates(subset=['Link'])
    
    # --- CAMBIO DE RUTA A CARPETA TIENDAS ---
    nombre_carpeta = "TIENDAS"
    ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)
    
    # 1. Crear carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        try:
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada: {ruta_carpeta}")
        except OSError as e:
            print(f"Error creando carpeta: {e}")

    nombre_archivo = f"Base_Datos_{NOMBRE_TIENDA}.xlsx"
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
        print("\n" + "="*60)
        print(f"¡PROCESO COMPLETADO!")
        print(f"Total productos guardados: {len(df)}")
        print(f"Archivo Excel generado en: {ruta_completa}")
        print("="*60)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("\nNo se obtuvieron datos.")