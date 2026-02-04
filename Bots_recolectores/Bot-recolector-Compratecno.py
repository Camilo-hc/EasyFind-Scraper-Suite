"""
Bot Recolector de Productos - Compratecno Chile

Este script automatiza la recolección de información de productos desde el sitio web
de Compratecno (https://compratecno.cl), una tienda especializada en redes, cableado
estructurado, seguridad y productos de telecomunicaciones en Chile.

Tecnología utilizada:
    - requests: Para realizar peticiones HTTP con sesiones persistentes
    - BeautifulSoup: Para parsear y extraer datos del HTML
    - pandas: Para estructurar y exportar datos a Excel
    
Características principales:
    - Sistema anti-CAPTCHA con pausas largas entre requests (6-12 segundos)
    - Detección automática de bloqueos (403, 429, 503)
    - Pausa manual interactiva cuando se detecta CAPTCHA
    - Paginación automática mediante enlaces "next"
    - Uso de sesiones HTTP para mantener cookies
    - Eliminación automática de duplicados
    - Exportación a formato Excel (.xlsx)

IMPORTANTE - Sistema Anti-Ban:
    Este bot implementa esperas largas entre páginas para evitar ser bloqueado.
    El proceso es más lento pero más seguro. Si se detecta un CAPTCHA, el script
    pausará y pedirá intervención manual del usuario.

Estructura de datos generada:
    - Producto: Nombre del producto
    - Link: URL completa del producto
    - Categoría: Categoría del producto
    - Tienda: Nombre de la tienda (Compratecno)

Dependencias:
    pip install requests beautifulsoup4 pandas openpyxl

Uso:
    python Bot-recolector-Compratecno.py
    
Salida:
    Genera el archivo 'Base_Datos_Compratecno.xlsx' en la carpeta 'TIENDAS/'

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# --- CONFIGURACIÓN ---
NOMBRE_TIENDA = "Compratecno"
DOMAIN = "https://compratecno.cl"

# CONFIGURACIÓN DE TIEMPOS (SEGURO ANTI-CAPTCHA) - Optimizado
TIEMPO_MINIMO = 3   # Segundos mínimos de espera (antes: 6)
TIEMPO_MAXIMO = 6   # Segundos máximos de espera (antes: 12)

categorias = [
    ("Redes", "https://compratecno.cl/596-redes"),
    ("HDMI VGA HD SD TV PC", "https://compratecno.cl/121-hdmi-vga-hd-sd-tv-pc"),
    ("Antenas", "https://compratecno.cl/588-inalambrico-antenas"),
    ("Fibra Optica", "https://compratecno.cl/53-fibra-optica-insumos"),
    ("Canalización e Insumos", "https://compratecno.cl/12-canalizacion-caja-perfora"),
    ("Electricidad/Energia", "https://compratecno.cl/10-electricidad-energia"),
    ("Cableado", "https://compratecno.cl/573-cableado-compratecno"),
    ("Rack Comunicación Servidores", "https://compratecno.cl/49-rack-gabinete-bastidor"),
    ("Corte/Etiqueta", "https://compratecno.cl/130-corte-etiqueta"),
    ("Seguridad", "https://compratecno.cl/108-seguridad-camara-alarma"),
    ("Fuente de Poder/POE", "https://compratecno.cl/4-poe-fuentes-de-poder"),
    ("Conectores", "https://compratecno.cl/574-conectores"),
    ("Herramientas", "https://compratecno.cl/126-herramientas"),
    ("Poste/Mastil", "https://compratecno.cl/183-poste-mastil-otros"),
    ("Patch/Panel/Faceplate", "https://compratecno.cl/72-patch-panel-faceplate"),
    ("Otros", "https://compratecno.cl/598-otros-productos"),
    ("Software", "https://compratecno.cl/605-software"),
    ("Computación/Accesorios", "https://compratecno.cl/610-computo"),
    ("Iluminación/Control", "https://compratecno.cl/632-iluminacion-control"),
    ("Articulo Personal/Protección", "https://compratecno.cl/679-art-personal-proteccion"),
    ("No catalogado", "https://compratecno.cl/748-no-catalogado")
]

datos_totales = []
conteo_por_categoria = {}

session = requests.Session()
# Headers más completos para parecer navegador real
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://compratecno.cl/"
})

def esperar_humano():
    """Espera aleatoria para evitar detección"""
    t = random.uniform(TIEMPO_MINIMO, TIEMPO_MAXIMO)
    time.sleep(t)

def obtener_sopa_manual(url):
    """
    Intenta descargar. Si detecta bloqueo/captcha (403/429),
    PAUSA el script y pide ayuda al usuario.
    """
    while True:
        try:
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            
            elif response.status_code == 404:
                print("   [404 - No existe]")
                return None
            
            elif response.status_code in [403, 429, 503]:
                # 403: Forbidden (Captcha), 429: Too Many Requests
                print("\n" + "!"*60)
                print(f"!!! ALERTA DE BLOQUEO/CAPTCHA (Código {response.status_code}) !!!")
                print(f"URL: {url}")
                print("1. Abre tu navegador y entra a esa URL.")
                print("2. Resuelve el CAPTCHA manualmente si aparece.")
                print("3. Vuelve aquí y presiona ENTER para continuar...")
                print("!"*60)
                input() # Pausa infinita hasta que el usuario de Enter
                print("Reintentando conexión...")
                continue # Vuelve a intentar el request
            
            else:
                print(f"   [Error {response.status_code}] reintentando en 3s...")
                time.sleep(3)  # Optimizado: antes 10s
        
        except Exception as e:
            print(f"   [Error Red: {e}] reintentando en 3s...")
            time.sleep(3)  # Optimizado: antes 10s

# --- BLOQUE PRINCIPAL ---
print(f"--- INICIANDO RECOLECCIÓN LENTA (ANTI-BAN) ---")
print(f"Velocidad: Una página cada {TIEMPO_MINIMO}-{TIEMPO_MAXIMO} segundos.")

for nombre_cat, url_cat in categorias:
    print(f"\n>>> Procesando Categoría: {nombre_cat}")
    conteo_por_categoria[nombre_cat] = 0
    
    url_actual = url_cat
    pagina_num = 1
    
    while url_actual:
        print(f"   Pág {pagina_num}...", end=" ")
        
        # LLAMADA SEGURA CON PAUSA MANUAL
        soup = obtener_sopa_manual(url_actual)
        
        if not soup:
            print("-> Fin o error fatal en esta categoría.")
            break

        # --- EXTRACCIÓN ---
        contenedor_principal = soup.find('div', id='js-product-list')
        bloques = []
        if contenedor_principal:
            bloques = contenedor_principal.find_all('article', class_='product-miniature')

        cantidad_en_pagina = len(bloques)
        print(f"({cantidad_en_pagina} prods)", end=" ")

        if cantidad_en_pagina > 0:
            for bloque in bloques:
                try:
                    etiqueta_titulo = bloque.find('h5', class_='product-name')

                    if etiqueta_titulo and etiqueta_titulo.find('a'):
                        link_obj = etiqueta_titulo.find('a')
                        nombre = link_obj.text.strip()
                        link_parcial = link_obj['href']
                    else:
                        link_obj = bloque.find('div', class_='thumbnail-container').find('a')
                        nombre = link_obj.text.strip() if link_obj and link_obj.text else "Sin Nombre"
                        link_parcial = link_obj['href'] if link_obj else ""

                    if link_parcial and not link_parcial.startswith('http'):
                        link_final = f"{DOMAIN}{link_parcial}"
                    else:
                        link_final = link_parcial

                    datos_totales.append({
                        'Producto': nombre,
                        'Link': link_final,
                        'Categoría': nombre_cat,
                        'Tienda': NOMBRE_TIENDA
                    })
                    conteo_por_categoria[nombre_cat] += 1

                except Exception:
                    continue
        else:
            no_products = soup.find('section', class_='no-products')
            if no_products:
                print("[Vacía]", end=" ")

        # --- SIGUIENTE PÁGINA ---
        boton_siguiente = soup.find('a', rel='next')

        if boton_siguiente and 'href' in boton_siguiente.attrs:
            url_actual = boton_siguiente['href']
            pagina_num += 1
            print("-> OK. Esperando...")
            esperar_humano() # <--- PAUSA IMPORTANTE AQUÍ
        else:
            print("-> Fin Cat.")
            url_actual = None
            esperar_humano() # Pausa entre categorías también

    print(f"   Total acumulado '{nombre_cat}': {conteo_por_categoria[nombre_cat]}")

# --- GUARDADO FINAL ---
if datos_totales:
    df = pd.DataFrame(datos_totales)
    
    cols = ['Producto', 'Link', 'Categoría', 'Tienda']
    # Asegurar que existan las columnas en el DF
    cols = [c for c in cols if c in df.columns]
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

    nombre_archivo = "Base_Datos_Compratecno.xlsx"
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
        print(f"Archivo guardado en: {ruta_completa}")
        print("="*50)
    except Exception as e:
        print(f"Error al guardar Excel: {e}")
else:
    print("No se encontraron datos.")