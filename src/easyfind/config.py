"""
Configuración global del motor EasyFind.

Contiene la clase Config con todos los parámetros ajustables del sistema,
la configuración de rutas de navegadores para PyInstaller, y la gestión
de la tasa de cambio USD/CLP.
"""

import os
import sys
import time
import requests
import urllib3

# ========== IMPORTAR RAPIDFUZZ ==========
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_DISPONIBLE = True
except ImportError:
    print(" RapidFuzz no instalado. Usando método legacy.")
    print("   Instala con: pip install rapidfuzz")
    RAPIDFUZZ_DISPONIBLE = False
# =========================================

# Configuración de ruta de navegadores para ejecutable empaquetado
if getattr(sys, 'frozen', False):
    # Cuando está empaquetado con PyInstaller
    # _MEIPASS es la carpeta temporal donde PyInstaller extrae los archivos
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "browsers")
else:
    # En desarrollo, usar la carpeta browsers del proyecto
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Subir dos niveles: src/easyfind/ -> raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(base_path))
    if os.path.exists(os.path.join(project_root, "browsers")):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(project_root, "browsers")


class Config:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # --- AJUSTES DE VELOCIDAD Y CONCURRENCIA ---
    CONCURRENCIA_GLOBAL = 8   # Total de pestañas simultáneas
    CONCURRENCIA_POR_TIENDA = 2 # Máximo de pestañas por dominio 
    TAMANO_LOTE_GUARDADO = 100 # Guardar Excel cada 100 productos procesados
    
    CARPETA_TIENDAS = "TIENDAS"
    
    # UMBRALES DE SIMILITUD 
    UMBRAL_ALTA_PRECISION = 85      # Similitud mínima para match confiable
    UMBRAL_MEDIA_PRECISION = 75     # Similitud para match probable
    UMBRAL_BAJA_PRECISION = 65      # Similitud mínima aceptable
    
    
    # Textos de Salida
    TEXTO_LOGIN = "Ver Web / Login"
    TEXTO_ERROR = "Error / No Detectado"
    TEXTO_SIN_LINK = "Link no encontrado"

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    TIENDAS_CON_IVA = ['COMPRATECNO', 'COMDIEL', 'DARTEL', 'EECOL', 'GOBANTES', 'VITEL']
    TIENDAS_SOLO_MARCA = ['SONEPAR', 'TRANSWORLD', 'INTCOMEX']
    
    PALABRAS_IGNORAR = [
        'ODF', 'JUMPER', 'MUFA', 'MANGUITO', 'BANDEJA', 'SPLITTER', 'NAP', 'ROSETA',
        'PIGTAIL', 'PATCHCORD', 'PATCH', 'CORD', 'CONNECTOR', 'ADAPTER', 'DISTRIBUIDOR',
        'TERMINAL', 'CAJA', 'GABINETE', 'RACK', 'ORGANIZADOR', 'FACEPLATE', 'KEYSTONE',
        'FIBRA', 'CABLE', 'CONECTOR', 'BOBINA', 'KIT', 'HERRAMIENTA', 'TESTER', 
        'MODULO', 'MÓDULO', 'UNIDAD', 'TRANSCEIVER', 'SFP', 'MEDIA', 'CONVERTER',
        'TAMAÑO', 'TAMANO', 'DIMENSIONES', 'PESO', 'MEDIDA', 'LONGITUD', 'ANCHO', 'ALTO',
        'PRECIO', 'VALOR', 'DESCRIPCION', 'DETALLE', 'SKU', 'CODIGO', 'INTERNET', 
        'NORMAL', 'OFERTA', 'OFERTAS', 'OUTLET', 'CATEGORIA', 'PRODUCTO', 
        'RELACIONADOS', 'INGRESAR', 'REGISTRARSE', 'CUENTA', 'CARRITO', 'MENU', 
        'BUSCAR', 'CONTACTO', 'INICIO', 'HOME', 'LOGIN', 'FICHA', 'TECNICA', 
        'DESCARGAR', 'PDF', 'STOCK', 'DISPONIBLE', 'AGOTADO', 'ENVIO', 'RETIRO',
        'ESPECIFICACIONES', 'CARACTERISTICAS', 'OPINIONES', 'COMENTARIOS', 
        'REFERENCIA', 'NUMERO', 'SERIE', 'MODELO', 'PART', 'NUMBER', 'CANTIDAD'
    ]

    @staticmethod
    def obtener_dolar_oficial() -> int:
        """Obtiene la tasa de cambio oficial USD/CLP desde la API de mindicador.cl.
        
        Realiza hasta 3 intentos de conexión a la API pública de mindicador.cl
        para obtener el valor actualizado del dólar. Si todos los intentos fallan,
        retorna un valor por defecto de 880 CLP.
        
        Returns:
            int: Tasa de cambio USD/CLP. Valor por defecto 880 si falla la API.
        """
        print("🌎 Obteniendo valor del Dólar")
        url = "https://mindicador.cl/api"
        for intento in range(1, 4):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    valor = int(data['dolar']['valor'])
                    print(f"Dólar: ${valor} CLP")
                    return valor
            except Exception as e:
                print(f"Intento {intento} fallido: {e}")
                time.sleep(2)
        
        print("Fallaron todos los intentos. Usando valor por defecto $880")
        return 880


TASA_DOLAR = 880
