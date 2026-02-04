"""
Bot Recolector de Productos - Gobantes Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Gobantes (https://gobantes.cl), una tienda especializada en conductores eléctricos,
iluminación, canalización y distribución eléctrica en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación real con soporte anti-detección
    - BeautifulSoup: Para parsear el HTML renderizado
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación real (NO headless) para evitar detección
    - Sistema anti-automatización desactivado
    - Detección y pausa manual para resolver CAPTCHAs
    - Scroll inteligente para activar lazy loading de imágenes
    - Paginación mediante botón "Siguiente" real
    - Esperas aleatorias entre páginas (2-3.5 segundos)
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Interacción Manual:
    Este bot puede mostrar el navegador y pausar si detecta un CAPTCHA.
    El usuario debe resolver el CAPTCHA manualmente y presionar ENTER
    para que el script continúe.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Gobantes)

Dependencias:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Gobantes.py
    
Salida:
    Genera el archivo 'Base_Datos_Gobantes.xlsx' en la carpeta 'TIENDAS/'

"""

import time
import pandas as pd
import random
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Gobantes"
DOMAIN = "https://gobantes.cl"

categorias = [
    ("Conductores Eléctricos", "https://gobantes.cl/12-conductores-electricos"),
    ("Iluminación", "https://gobantes.cl/13-iluminacion"),
    ("Residencial", "https://gobantes.cl/17-residencial"),
    ("Canalización", "https://gobantes.cl/15-canalizacion"),
    ("Control y Potencia", "https://gobantes.cl/16-control-y-potencia"),
    ("Distribución", "https://gobantes.cl/14-distribucion"),
    ("Ferretería Eléctrica", "https://gobantes.cl/18-ferreteria-electrica"),
    ("Seguridad Industrial", "https://gobantes.cl/19-seguridad-industrial-")
]

def iniciar_navegador():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")  # Descomenta para modo segundo plano
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

print(f"--- INICIANDO MODO NAVEGACIÓN REAL (SIN PRECIOS): {NOMBRE_TIENDA} ---")
print("NOTA: Si sale un Captcha, resuélvelo en el navegador y pulsa ENTER aquí.")

datos_totales = []
driver = iniciar_navegador()

try:
    for nombre_cat, url_cat in categorias:
        print(f"\n" + "="*60)
        print(f">>> CATEGORÍA: {nombre_cat}")
        print("="*60)
        
        # Navegar a la primera página
        driver.get(url_cat)
        pagina_actual = 1
        
        while True:
            print(f"   -> Procesando Página {pagina_actual}...", end=" ")
            
            try:
                # 1. ESPERA INTELIGENTE (Hasta que carguen los productos)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article.product-miniature, .products"))
                    )
                except:
                    pass 

                # 2. SCROLL PARA CARGAR IMÁGENES (Lazy Load)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)

                # 3. LEER HTML
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                bloques = soup.find_all('article', class_='product-miniature')
                
                # --- VERIFICACIÓN DE SEGURIDAD (CAPTCHA / VACÍO) ---
                if not bloques:
                    if "No hay productos" in soup.text:
                        print(" [Fin: No hay más productos]")
                        break
                    
                    print("\n" + "!"*50)
                    print(f"   [ALERTA] No veo productos en Pág {pagina_actual}.")
                    print("   ¿Hay un CAPTCHA o la página no cargó bien?")
                    input("   >>> Resuélvelo en el navegador y presiona ENTER para reintentar... ")
                    print("!"*50)
                    # Reintentar lectura tras la pausa
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    bloques = soup.find_all('article', class_='product-miniature')

                # 4. EXTRAER DATOS (SIN PRECIO)
                conteo = 0
                for item in bloques:
                    try:
                        # Título y Link
                        tag_titulo = item.select_one('.product-title a')
                        if not tag_titulo: continue
                        
                        nombre = tag_titulo.get_text(strip=True)
                        link = tag_titulo['href']
                        
                        datos_totales.append({
                            'Producto': nombre,
                            'Link': link,
                            'Categoría': nombre_cat,
                            'Tienda': NOMBRE_TIENDA
                        })
                        conteo += 1
                    except:
                        continue
                
                print(f"({conteo} productos OK)")

                # 5. BUSCAR EL BOTÓN "SIGUIENTE" REAL
                try:
                    boton_siguiente = driver.find_element(By.CSS_SELECTOR, "a.next")
                    url_siguiente = boton_siguiente.get_attribute("href")
                    
                    if url_siguiente and url_siguiente != driver.current_url:
                        # Navegamos a la URL del botón
                        driver.get(url_siguiente)
                        pagina_actual += 1
                        time.sleep(random.uniform(0.8, 1.5))  # Optimizado: antes 2.0-3.5s 
                    else:
                        print("      [Fin] No hay botón 'Siguiente' válido.")
                        break
                except:
                    print("      [Fin] Se acabaron las páginas (Botón 'Siguiente' no encontrado).")
                    break
                
            except Exception as e:
                print(f"\n      [Error en página] {e}")
                opcion = input("      ¿Presiona ENTER para reintentar página o escribe 'saltar' para pasar de categoría?: ")
                if 'saltar' in opcion.lower():
                    break

except Exception as e:
    print(f"\n[ERROR CRÍTICO] {e}")

finally:
    driver.quit()
    print("\nCerrando navegador...")

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    # Ordenar columnas
    columnas_deseadas = ['Producto', 'Link', 'Categoría', 'Tienda']
    cols = [c for c in columnas_deseadas if c in df.columns]
    df = df[cols]
    
    # Limpieza final
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

    nombre_archivo = "Base_Datos_Gobantes.xlsx"
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
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("No se encontraron datos.")