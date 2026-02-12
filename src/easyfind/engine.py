"""
Motor principal de EasyFind.

Orquesta la carga de bases de datos, la coincidencia de doble precisión
y el scraping concurrente de URLs para comparación de precios.
"""

import asyncio
import os
import sys
import random

import pandas as pd
from collections import defaultdict

from .config import Config, TASA_DOLAR, RAPIDFUZZ_DISPONIBLE
from .data_manager import DataManager
from .web_scraper import WebScraper
from .content_parser import ContentParser

# Necesitamos acceso mutable a TASA_DOLAR del módulo config
from . import config as _config_module


async def procesar_tarea_segura(sem_global, sem_dominio, scraper, tienda, url, row_idx, metodo_origen):
    """Wrapper para scraping concurrente con limitación de tasa basada en semáforos."""
    async with sem_global:
        async with sem_dominio:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            precio, marca, err = await scraper.procesar_url(url)
            return row_idx, tienda, url, marca, precio, err, metodo_origen


async def main(callback_log=None, callback_progress=None, stop_event=None):
    """Orquestador principal: carga bases de datos, realiza coincidencia de doble precisión y hace scraping de URLs concurrentemente."""
    
    def log(mensaje):
        print(mensaje)
        if callback_log:
            msg_limpio = str(mensaje).replace("\n", "")
            callback_log(msg_limpio)

    if getattr(sys, 'frozen', False):
        carpeta_root = os.path.dirname(sys.executable)
    else:
        carpeta_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Actualizar tasa del dólar globalmente
    _config_module.TASA_DOLAR = Config.obtener_dolar_oficial()
    
    if RAPIDFUZZ_DISPONIBLE:
        log(f"--- Iniciando EasyFind ---")
    else:
        log(f"--- Iniciando EasyFind (modo legacy) ---")
    
    scraper = WebScraper()
    await scraper.start()
    
    try:
        log("Cargando bases de datos de TIENDAS")
        df_db = DataManager.cargar_bases_datos(os.path.join(carpeta_root, Config.CARPETA_TIENDAS))
        if df_db.empty: 
            log("Error: Sin bases de datos en la carpeta TIENDAS.")
            return

        # Cargar archivo de Productos
        try:
            ruta_xlsx = os.path.join(carpeta_root, "PRODUCTOS.xlsx")
            ruta_csv = os.path.join(carpeta_root, "PRODUCTOS.csv")
            
            if os.path.exists(ruta_xlsx):
                df_pedido = pd.read_excel(ruta_xlsx)
            elif os.path.exists(ruta_csv):
                df_pedido = pd.read_csv(ruta_csv)
            else:
                log("No se encontró PRODUCTOS.xlsx ni PRODUCTOS.csv")
                return
        except Exception as e:
            log(f"Error leyendo archivo de productos: {e}")
            return
            
        col_desc = next((c for c in df_pedido.columns if c.lower() in ['itemname', 'descripcion', 'producto']), None)
        if not col_desc: 
            log("Falta columna ItemName/Descripcion en el Excel.")
            return

        tiendas = sorted(df_db['Tienda'].unique())
        # Preparar columnas de salida
        for t in tiendas:
            for campo in ['Link', 'Marca', 'Precio']:
                if f"{t} {campo}" not in df_pedido.columns:
                    df_pedido[f"{t} {campo}"] = ""

        # --- FASE 1: GENERACIÓN DE TAREAS DUALES ---
        log(f"⚙️ Analizando {len(df_pedido)} productos")
        
        tareas_pendientes = []
        
        # Inicializar Semáforos
        sem_global = asyncio.Semaphore(Config.CONCURRENCIA_GLOBAL)
        sems_dominio = defaultdict(lambda: asyncio.Semaphore(Config.CONCURRENCIA_POR_TIENDA))
        
        cache_tiendas = {t: df_db[df_db['Tienda'] == t] for t in tiendas}

        count_alta = 0
        count_media = 0
        count_baja = 0
        count_fail = 0

        for idx, row in df_pedido.iterrows():
            producto = str(row[col_desc])
            
            for tienda in tiendas:
                df_subset = cache_tiendas[tienda]
                
                # 1. INTENTO ALTA PRECISIÓN
                url_final, _ = DataManager.buscar_match_alta_precision(producto, df_subset)
                metodo = "Alta Precisión"

                # 2. INTENTO MEDIA PRECISIÓN
                if not url_final:
                    url_final, _ = DataManager.buscar_match_media_precision(producto, df_subset)
                    metodo = "Media Precisión"
                
                # 3. INTENTO BAJA PRECISIÓN
                if not url_final:
                    url_final, _ = DataManager.buscar_match_baja_precision(producto, df_subset)
                    metodo = "Baja Precisión"
                
                # 4. RESULTADO
                if url_final:
                    dominio_base = url_final.split('/')[2] if '//' in url_final else 'generic'
                    t = procesar_tarea_segura(
                        sem_global, 
                        sems_dominio[dominio_base], 
                        scraper, 
                        tienda, 
                        url_final, 
                        idx,
                        metodo
                    )
                    tareas_pendientes.append(t)
                    
                    if metodo == "Alta Precisión": count_alta += 1
                    elif metodo == "Media Precisión": count_media += 1
                    else: count_baja += 1
                else:
                    # Escribir directamente "Link no encontrado"
                    df_pedido.at[idx, f"{tienda} Link"] = Config.TEXTO_SIN_LINK
                    df_pedido.at[idx, f"{tienda} Precio"] = Config.TEXTO_SIN_LINK
                    df_pedido.at[idx, f"{tienda} Marca"] = "-"
                    count_fail += 1

        log(f"Resumen de Búsqueda en DB:")
        log(f"Alta Precisión: {count_alta}")
        log(f"Media Precisión: {count_media}")
        log(f"Baja Precisión: {count_baja}")
        log(f"No encontrados: {count_fail}")
        log(f"Iniciando scraping de {len(tareas_pendientes)} URLs...")
        
        # --- FASE 2: EJECUCIÓN ASÍNCRONA ---
        total_tareas = len(tareas_pendientes)
        completados = 0
        ultimo_guardado = 0
        
        if total_tareas > 0:
            for corrutina in asyncio.as_completed(tareas_pendientes):
                
                # VERIFICACIÓN DE DETENCIÓN 
                if stop_event and stop_event.is_set():
                    log("Proceso detenido por el usuario.")
                    break 
                
                row_idx, tienda, url_final, marca, precio, err, metodo_usado = await corrutina
                
                # Reglas de IVA y Login
                precio_final = 0
                es_tienda_login = tienda in Config.TIENDAS_SOLO_MARCA

                if precio > 0:
                    if tienda in Config.TIENDAS_CON_IVA:
                        precio_final = int(precio / 1.19)
                    else:
                        precio_final = precio
                
                valor_para_excel = ""
                tag_log = ""

                if precio_final > 0:
                    valor_para_excel = precio_final
                    tag_log = f"$ {precio_final:,.0f}"
                elif es_tienda_login:
                    valor_para_excel = Config.TEXTO_LOGIN
                    tag_log = "Login Req"
                else:
                    valor_para_excel = Config.TEXTO_ERROR
                    tag_log = "No detectado"
                
                if err: tag_log += f" ({err})"

                # Escribir en DF 
                df_pedido.at[row_idx, f"{tienda} Link"] = url_final
                df_pedido.at[row_idx, f"{tienda} Marca"] = marca
                df_pedido.at[row_idx, f"{tienda} Precio"] = valor_para_excel

                completados += 1
                
                # ACTUALIZACIÓN DE BARRA DE PROGRESO
                if callback_progress:
                    callback_progress(completados, total_tareas)

                if completados % 5 == 0 or completados == total_tareas:
                    log(f"[{completados}/{total_tareas}] {tienda} ({metodo_usado}) -> {tag_log}")

                # Guardado Parcial
                if completados - ultimo_guardado >= Config.TAMANO_LOTE_GUARDADO:
                    try:
                        df_pedido.to_excel(os.path.join(carpeta_root, "Resultado_Parcial.xlsx"), index=False)
                        ultimo_guardado = completados
                    except: pass

        # Guardado Final
        output = os.path.join(carpeta_root, "Resultado.xlsx")
        df_pedido.to_excel(output, index=False)
        
        if stop_event and stop_event.is_set():
            log(f"Proceso detenido. Se guardó lo avanzado en: Resultado.xlsx")
        else:
            log(f"Busqueda terminada. Archivo guardado: Resultado.xlsx")

    except KeyboardInterrupt:
        log("Interrumpido por usuario.")
        try:
            df_pedido.to_excel(os.path.join(carpeta_root, "Resultado_Interrumpido.xlsx"), index=False)
        except: pass
    except Exception as e:
        log(f"Error General: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()
