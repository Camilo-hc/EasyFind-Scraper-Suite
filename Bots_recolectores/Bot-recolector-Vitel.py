"""
Bot Recolector de Productos - Vitel Energía Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Vitel Energía (https://vitelenergia.com), una empresa especializada en conductores,
canalización, protecciones, automatización, iluminación y energías renovables en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y renderizado de JavaScript
    - BeautifulSoup: Para parsear el HTML renderizado
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación real (NO headless) para evitar bloqueos
    - Sistema robusto de reintentos (3 intentos por página)
    - Guardado automático de backups parciales por categoría
    - Detección de bloqueos Cloudflare con espera automática
    - Scroll automático para lazy loading
    - Paginación mediante botón "Siguiente"
    - Reinicio automático del navegador ante fallos críticos
    - Esperas aleatorias entre páginas (3-5 segundos)
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Sistema de Backup:
    Este bot guarda backups automáticos después de cada categoría en
    'Backup_Vitel_Progreso.xlsx' para evitar pérdida de datos ante fallos.
    El backup se elimina automáticamente al completar exitosamente.

IMPORTANTE - Detección de Bloqueos:
    Si detecta un bloqueo de Cloudflare ("Just a moment"), espera 20
    segundos automáticamente y reintenta la carga.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Vitel Energia)

Dependencias:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-Vitel.py
    
Salida:
    Genera el archivo 'Base_Datos_Vitel.xlsx' en la carpeta 'TIENDAS/'

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
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Vitel Energia"
MAX_INTENTOS = 3  # Número de veces que reintentará si falla una página

# Categorías de VITEL
categorias = [
    ("Conductores", "https://vitelenergia.com/es/conductores.html"),
    ("Canalización", "https://vitelenergia.com/es/canalizacion.html"),
    ("Protecciones y Comandos", "https://vitelenergia.com/es/protecciones-y-comandos.html"),
    ("Tableros y Gabinetes", "https://vitelenergia.com/es/tableros-y-gabinetes.html"),
    ("Automatización", "https://vitelenergia.com/es/automatizacion.html"),
    ("Enchufes e Interruptores", "https://vitelenergia.com/es/enchufes-e-interruptores.html"),
    ("Iluminación", "https://vitelenergia.com/es/iluminacion.html"),
    ("Energías Renovables", "https://vitelenergia.com/es/energias-renovables.html"),
    ("Electromovilidad", "https://vitelenergia.com/es/electromovilidad.html"),
    ("Redes", "https://vitelenergia.com/es/redes.html"),
    ("Herramientas", "https://vitelenergia.com/es/herramientas.html")
]

# Definición de rutas
nombre_carpeta = "TIENDAS"
ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)

# Crear carpeta si no existe
if not os.path.exists(ruta_carpeta):
    try:
        os.makedirs(ruta_carpeta)
        print(f"Carpeta creada: {ruta_carpeta}")
    except OSError as e:
        print(f"Error creando carpeta: {e}")

def iniciar_navegador():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")  # Descomenta para modo segundo plano 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def guardar_backup(datos):
    """Guarda un archivo temporal dentro de la carpeta TIENDAS para no perder datos si falla"""
    try:
        if datos:
            df_temp = pd.DataFrame(datos)
            df_temp = df_temp.drop_duplicates(subset=['Link'])
            
            # Guardamos el backup en la misma carpeta TIENDAS para orden
            ruta_backup = os.path.join(ruta_carpeta, "Backup_Vitel_Progreso.xlsx")
            
            df_temp.to_excel(ruta_backup, index=False)
            print(f"   [SEGURIDAD] Backup guardado ({len(df_temp)} productos) en {ruta_backup}")
    except Exception as e:
        print(f"   [Error guardando backup] {e}")

print(f"--- INICIANDO RECOLECCIÓN EN VITEL (MODO ROBUSTO CON REINTENTOS) ---")
print("NOTA: Se realizarán guardados parciales para evitar pérdida de datos.")

datos_totales = []
driver = iniciar_navegador()

try:
    for nombre_cat, url_cat in categorias:
        print(f"\n" + "="*60)
        print(f">>> CATEGORÍA: {nombre_cat}")
        print("="*60)
        
        # Lógica para reiniciar navegador si se cerró inesperadamente
        try:
            driver.current_url
        except:
            print("   [!] Navegador perdido. Reiniciando...")
            driver = iniciar_navegador()

        # Intentar cargar la categoría inicial
        driver.get(url_cat)
        pagina_actual = 1
        
        while True:
            intentos = 0
            exito_pagina = False
            
            while intentos < MAX_INTENTOS:
                try:
                    print(f"   -> Procesando Página {pagina_actual} (Intento {intentos+1})...", end=" ")
                    
                    # 1. Esperar carga
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "product-item"))
                        )
                    except TimeoutException:
                        print(" [Tiempo de espera agotado, reintentando carga...]")
                        driver.refresh()
                        time.sleep(5)
                        intentos += 1
                        continue

                    # 2. Scroll para Lazy Loading
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # 3. Analizar HTML
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    bloques = soup.select(".product-item")
                    
                    if not bloques:
                        # Verificación Cloudflare o Error
                        if "Just a moment" in soup.text:
                            print("\n   [ALERTA] Bloqueo detectado. Esperando...")
                            time.sleep(3)  # Optimizado: antes 20s
                            driver.refresh()
                            intentos += 1
                            continue
                        
                        print(" [0 productos - Fin de categoría]")
                        exito_pagina = True # Se considera éxito porque simplemente no hay más
                        break
                    
                    # 4. Extraer Datos
                    conteo_pag = 0
                    for item in bloques:
                        try:
                            tag_a = item.find('a', class_='product-item-link')
                            if tag_a:
                                nombre = tag_a.get_text(strip=True)
                                link = tag_a['href']
                                datos_totales.append({
                                    'Producto': nombre,
                                    'Link': link,
                                    'Categoría': nombre_cat,
                                    'Tienda': NOMBRE_TIENDA
                                })
                                conteo_pag += 1
                        except:
                            continue
                    
                    print(f"({conteo_pag} productos extraídos)")
                    exito_pagina = True
                    break # Salir del bucle de intentos si todo salió bien

                except (WebDriverException, Exception) as e:
                    print(f"\n      [Error: {e}] - Reintentando...")
                    intentos += 1
                    time.sleep(5)
                    try:
                        driver.refresh() # Intentar refrescar para arreglar errores
                    except:
                        # Si no puede refrescar, reinicia el navegador
                        driver.quit()
                        driver = iniciar_navegador()
                        driver.get(url_cat) # Volver al inicio de categoría si es necesario
            
            # Si falló después de todos los intentos en esta página
            if not exito_pagina:
                print(f"      [X] Fallo crítico en página {pagina_actual}. Saltando a siguiente categoría...")
                break # Rompe el while de páginas para ir a la siguiente categoría
            
            # Si no hubo productos (fin de paginación normal), salir
            if 'bloques' in locals() and not bloques:
                break

            # 5. Ir a la siguiente página
            try:
                # Intentamos encontrar el botón next
                boton_siguiente = driver.find_elements(By.CSS_SELECTOR, "a.action.next")
                
                if boton_siguiente and boton_siguiente[0].is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView();", boton_siguiente[0])
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", boton_siguiente[0])
                    pagina_actual += 1
                    time.sleep(random.uniform(1.5, 2.5))  # Optimizado: antes 3.0-5.0s
                else:
                    print("      [Fin] Última página alcanzada.")
                    break
            except Exception as e:
                print(f"      [Info] No se pudo pasar de página: {e}")
                break
        
        # GUARDADO PARCIAL AL TERMINAR CADA CATEGORÍA
        guardar_backup(datos_totales)

except Exception as e:
    print(f"\n[ERROR CRÍTICO GLOBAL] {e}")

finally:
    try:
        driver.quit()
    except:
        pass
    print("\nCerrando navegador...")

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    df = df.drop_duplicates(subset=['Link']) 
    
    print("\n" + "="*50)
    print(" RESUMEN FINAL:")
    print("="*50)
    print(df['Categoría'].value_counts().to_string())
    
    nombre_archivo = "Base_Datos_Vitel.xlsx"
    ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
    
    # ELIMINAR ARCHIVO SI YA EXISTE (Para asegurar reemplazo)
    if os.path.exists(ruta_completa):
        try:
            os.remove(ruta_completa)
            print(f"Archivo previo eliminado para ser reemplazado: {nombre_archivo}")
        except PermissionError:
            print(f"⚠️ ADVERTENCIA: El archivo '{nombre_archivo}' está abierto. Ciérralo para permitir el reemplazo.")

    try:
        df.to_excel(ruta_completa, index=False)
        print(f"\n¡ÉXITO! Archivo final guardado en: {ruta_completa}")
        
        # Opcional: Eliminar el backup si todo salió bien
        ruta_backup = os.path.join(ruta_carpeta, "Backup_Vitel_Progreso.xlsx")
        if os.path.exists(ruta_backup):
            os.remove(ruta_backup)
            
    except Exception as e:
        print(f"Error al guardar Excel final: {e}")
else:
    print("No se encontraron datos.")