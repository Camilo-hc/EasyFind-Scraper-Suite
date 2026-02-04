"""
Bot Recolector de Productos - Transworld Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Transworld (https://www.transworld.cl), una empresa especializada en conectividad,
fibra óptica, cableado estructurado, networking y seguridad electrónica en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y renderizado de JavaScript
    - BeautifulSoup: Para parsear el HTML renderizado
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación en modo headless (invisible)
    - Sistema anti-detección (desactivación de características de automatización)
    - Scroll automático para activar lazy loading
    - Paginación mediante botón "Siguiente" (WooCommerce)
    - Selectores específicos para WooCommerce
    - Esperas aleatorias entre páginas (2-4 segundos)
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Plataforma WooCommerce:
    Este sitio usa WooCommerce, por lo que los selectores CSS están
    optimizados para esta plataforma de e-commerce.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Transworld)

Dependencias:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Transworld.py
    
Salida:
    Genera el archivo 'Base_Datos_Transworld.xlsx' en la carpeta 'TIENDAS/'

"""

import time
import pandas as pd
import random
import os
from bs4 import BeautifulSoup

# --- IMPORTACIONES DE SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Transworld"

# Categorías de TRANSWORLD
categorias = [
    ("Fibra Óptica", "https://www.transworld.cl/categoria-producto/conectividad-con-fibra-optica/"),
    ("Inalámbrica", "https://www.transworld.cl/categoria-producto/conectividad-inalambrica/"),
    ("Cableado Estructurado", "https://www.transworld.cl/categoria-producto/cableado-estructurado/"),
    ("Canalización", "https://www.transworld.cl/categoria-producto/canalizacion/"),
    ("Gabinetes", "https://www.transworld.cl/categoria-producto/gabinetes-de-comunicacion/"),
    ("Networking", "https://www.transworld.cl/categoria-producto/networking/"),
    ("CCTV", "https://www.transworld.cl/categoria-producto/cctv/"),
    ("Seguridad Máquinas", "https://www.transworld.cl/categoria-producto/seguridad-de-maquinas/"),
    ("Energía", "https://www.transworld.cl/energia/")
]

def iniciar_navegador():
    chrome_options = Options()
    
    # --- MODO SEGUNDO PLANO (HEADLESS) ---
    chrome_options.add_argument("--headless=new") 
    
    # --- ANTI-DETECCIÓN ---
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Iniciar driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

print(f"--- INICIANDO RECOLECCIÓN EN {NOMBRE_TIENDA} (SEGUNDO PLANO) ---")
print("El navegador se está ejecutando en memoria (no verás la ventana).")
print("Por favor espera...")

datos_totales = []
driver = iniciar_navegador()

try:
    for nombre_cat, url_cat in categorias:
        print(f"\n" + "="*60)
        print(f">>> CATEGORÍA: {nombre_cat}")
        print("="*60)
        
        driver.get(url_cat)
        pagina_actual = 1
        
        while True:
            print(f"   -> Procesando Página {pagina_actual}...", end=" ")
            
            try:
                # 1. Esperar carga inicial de productos
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.product"))
                    )
                except:
                    print(" [Tiempo de espera agotado o sin productos]")
                    pass 

                # 2. Scroll para asegurar carga de imágenes/scripts (Lazy Load)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                # 3. Analizar HTML con BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Selector específico de Transworld
                bloques = soup.select("li.product")
                
                if not bloques:
                    print(" [0 productos encontrados - Fin de categoría]")
                    break
                
                # 4. Extraer Datos (Solo Producto, Link, Categoria, Tienda)
                conteo_pag = 0
                for item in bloques:
                    try:
                        # -- TITULO --
                        titulo_tag = item.select_one('.woocommerce-loop-product__title')
                        if not titulo_tag: continue 
                        nombre = titulo_tag.get_text(strip=True)

                        # -- LINK --
                        link_tag = item.select_one('a.woocommerce-loop-product__link')
                        link = link_tag['href'] if link_tag else "Sin Link"

                        # Guardamos SOLO lo solicitado
                        datos_totales.append({
                            'Producto': nombre,
                            'Link': link,
                            'Categoría': nombre_cat,
                            'Tienda': NOMBRE_TIENDA
                        })
                        conteo_pag += 1
                    except Exception as e:
                        continue
                
                print(f"({conteo_pag} productos extraídos)")

                if conteo_pag == 0:
                    break

                # 5. Paginación: Buscar botón "Siguiente"
                try:
                    boton_siguiente = driver.find_element(By.CSS_SELECTOR, "a.next.page-numbers")
                    
                    if boton_siguiente.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView();", boton_siguiente)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", boton_siguiente)
                        
                        pagina_actual += 1
                        time.sleep(random.uniform(0.8, 1.5))  # Optimizado: antes 2.0-4.0s
                    else:
                        print("      [Fin] Botón siguiente no activo.")
                        break
                except:
                    print("      [Fin] Última página alcanzada.")
                    break
                
            except Exception as e:
                print(f"\n      [Error en lectura de página] {e}")
                break

except Exception as e:
    print(f"\n[ERROR CRÍTICO DEL BOT] {e}")

finally:
    driver.quit()
    print("\n" + "-"*30)
    print("Navegador cerrado.")

# --- GUARDADO FINAL ---
if datos_totales:
    print("Procesando datos para guardar...")
    df = pd.DataFrame(datos_totales)
    
    # Ordenar columnas
    columnas_ordenadas = ['Producto', 'Link', 'Categoría', 'Tienda']
    # Filtro defensivo
    cols = [c for c in columnas_ordenadas if c in df.columns]
    df = df[cols]
    
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

    nombre_archivo = "Base_Datos_Transworld.xlsx"
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
        print(f"✅ ¡PROCESO COMPLETADO!")
        print(f"Total productos guardados: {len(df)}")
        print(f"Archivo guardado en: {ruta_completa}")
        print("="*60)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("⚠️ No se encontraron datos. Revisa tu conexión o si la página cambió.")