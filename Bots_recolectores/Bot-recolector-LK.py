"""
Bot Recolector de Productos - LK Chile

Este script automatiza la recolección de información de productos desde el sitio web
de LK (https://lk.cl), una tienda especializada en materiales eléctricos, iluminación
y productos para la construcción en Chile.

Tecnología utilizada:
    - Selenium WebDriver: Para navegación y carga de contenido AJAX
    - BeautifulSoup: Para parsear el HTML renderizado
    - pandas: Para estructurar y exportar datos a Excel
    - webdriver_manager: Para gestión automática del ChromeDriver
    
Características principales:
    - Navegación en modo headless (invisible)
    - Extracción automática de categorías desde el menú principal
    - Sistema de scroll progresivo para cargar productos AJAX
    - Selectores CSS flexibles para diferentes layouts (lista/cuadrícula)
    - Detección automática de estructura de menú jerárquico
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Carga Dinámica:
    Este bot implementa scroll automático para cargar productos que se
    cargan mediante AJAX al hacer scroll. Realiza hasta 3 scrolls por página
    para asegurar la carga completa de productos.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoria: Categoría principal del producto
    - Tienda: Nombre de la tienda (LK)

Dependencias:
    pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Uso:
    python Bot-recolector-LK.py
    
Salida:
    Genera el archivo 'Base_Datos_LK.xlsx' en la carpeta 'TIENDAS/'

"""

import time
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "LK"
DOMAIN = "https://lk.cl"

def iniciar_navegador():
    chrome_options = Options()
    # MODO INVISIBLE (Headless)
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

print(f"--- INICIANDO RECOLECCIÓN LK (Versión Reparada de Selectores) ---")
print("Cargando menú principal...")

driver = iniciar_navegador()
datos_totales = []

try:
    # 1. OBTENER CATEGORÍAS (Padres)
    driver.get(DOMAIN)
    time.sleep(1)  # Optimizado: antes 3s
    
    soup_menu = BeautifulSoup(driver.page_source, 'html.parser')
    mapa_categorias = {}
    
    # Buscar items padres del menú
    items_padre = soup_menu.find_all('li', class_='licat')
    
    for item in items_padre:
        nombre_categoria_grande = item.text.strip()
        id_cat = item.get('data-cat')
        if not id_cat: continue
        
        # Buscar submenú oculto
        id_submenu = f"sm_{id_cat}"
        submenu = soup_menu.find('span', id=id_submenu)
        
        urls_hijas = []
        if submenu:
            enlaces = submenu.find_all('a')
            for a in enlaces:
                href = a.get('href')
                if href:
                    full_url = f"{DOMAIN}/{href.lstrip('/')}" if not href.startswith('http') else href
                    urls_hijas.append(full_url)
        
        if urls_hijas:
            mapa_categorias[nombre_categoria_grande] = urls_hijas

    print(f"Detectadas {len(mapa_categorias)} líneas de negocio.")
    print("-" * 60)
    
    # 2. RECORRER CATEGORÍAS
    for i, (categoria_grande, lista_urls) in enumerate(mapa_categorias.items(), 1):
        print(f"GRUPO [{i}/{len(mapa_categorias)}]: {categoria_grande.upper()}")
        
        total_grupo = 0
        
        for url_sub in lista_urls:
            try:
                driver.get(url_sub)
                
                # --- SCROLL PARA CARGA AJAX ---
                # Importante: LK carga productos al bajar
                last_height = driver.execute_script("return document.body.scrollHeight")
                intentos_scroll = 0
                while intentos_scroll < 3:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    intentos_scroll += 1
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # --- CORRECCIÓN DE SELECTORES ---
                bloques = soup.select('.item.lista')
                
                if not bloques:
                    bloques = soup.select('.caluga_prod')
                
                conteo_url = 0
                nombre_sub = url_sub.split('/')[-1] # Nombre corto para mostrar

                for bloque in bloques:
                    try:
                        nombre = "Sin Nombre"
                        link_final = ""

                        # Extracción ESTRATEGIA A (Lista)
                        clases_bloque = bloque.get('class', [])
                        
                        if 'lista' in clases_bloque:
                            div_titulo = bloque.find('div', class_='tituloItem')
                            if div_titulo:
                                tag_a = div_titulo.find('a')
                                if tag_a:
                                    nombre = tag_a.text.strip()
                                    href = tag_a.get('href', '')
                                    link_final = href if href.startswith('http') else f"{DOMAIN}/{href.lstrip('/')}"

                        # Extracción ESTRATEGIA B (Cuadrícula / Caluga)
                        else:
                            div_titulo = bloque.find('div', class_='titulo_prod')
                            nombre = div_titulo.text.strip() if div_titulo else "Sin Nombre"
                            
                            tag_a = bloque.find('a', class_='cargaProd')
                            if tag_a:
                                href = tag_a.get('href', '')
                                link_final = href if href.startswith('http') else f"{DOMAIN}/{href.lstrip('/')}"

                        # GUARDAR SOLO LAS 4 COLUMNAS PEDIDAS
                        if link_final:
                            datos_totales.append({
                                'Producto': nombre,
                                'Link': link_final,
                                'Categoria': categoria_grande,
                                'Tienda': NOMBRE_TIENDA
                            })
                            conteo_url += 1

                    except Exception:
                        continue
                
                total_grupo += conteo_url
                print(f"   |-- '{nombre_sub}': {conteo_url} productos.")

            except Exception:
                print(f"   |-- Error cargando URL")
                continue
        
        print(f"   >>> Total Grupo: {total_grupo}\n")

except Exception as e:
    print(f"Error crítico: {e}")

finally:
    if driver: driver.quit()

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    # 1. Asegurar orden exacto de columnas
    columnas_deseadas = ['Producto', 'Link', 'Categoria', 'Tienda']
    # Filtro defensivo por si alguna columna no se creó
    cols_existentes = [c for c in columnas_deseadas if c in df.columns]
    df = df[cols_existentes]
    
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

    nombre_archivo = "Base_Datos_LK.xlsx"
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
        print(f"Archivo guardado en: {ruta_completa}")
        print("="*50)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("No se encontraron datos.")