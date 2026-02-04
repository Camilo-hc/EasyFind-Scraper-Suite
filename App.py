"""EasyFind - Suite de Precios.

Aplicación de escritorio para la gestión automatizada de búsqueda de precios
y actualización de bases de datos mediante bots recolectores.

Este módulo implementa una interfaz gráfica de usuario (GUI) basada en Tkinter
que permite:
    - Ejecutar múltiples bots recolectores en paralelo para actualizar bases de datos
    - Realizar búsquedas masivas de precios de productos
    - Monitorear el progreso de cada bot en tiempo real
    - Gestionar procesos de forma segura con capacidad de detención forzada

Arquitectura:
    El código está organizado en tres clases principales siguiendo el principio
    de separación de responsabilidades:
    
    1. SystemUtils: Utilidades de bajo nivel del sistema operativo
    2. BotManager: Lógica de negocio para gestión de procesos de bots
    3. EasyFindApp: Interfaz gráfica de usuario y coordinación de eventos

Dependencias:
    - tkinter: Interfaz gráfica de usuario
    - EasyFind: Módulo personalizado para búsqueda de precios
    - subprocess: Ejecución de scripts de bots externos
    - threading: Procesamiento asíncrono sin bloquear la UI
    - asyncio: Soporte para operaciones asíncronas en EasyFind

Autor: Camilo Hernández
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import time
import threading
import asyncio
import queue 
import sys
import os
import glob
import subprocess
import concurrent.futures
import ctypes
import EasyFind 

# =============================================================================
# CLASE 1: UTILIDADES DEL SISTEMA (Lógica de OS)
# =============================================================================
class SystemUtils:
    """Utilidades de bajo nivel para interacción con el sistema operativo.
    
    Esta clase proporciona métodos estáticos para gestionar aspectos del sistema
    operativo como la prevención de suspensión y la terminación de procesos.
    
    Todas las operaciones están diseñadas para ser seguras y manejar errores
    de forma silenciosa cuando sea apropiado.
    """
    
    @staticmethod
    def toggle_sleep_prevention(enable):
        """Controla la prevención de suspensión del sistema Windows.
        
        Utiliza la API de Windows (SetThreadExecutionState) para evitar que
        el sistema entre en modo de suspensión durante operaciones largas.
        Esto es crítico para procesos de actualización que pueden tardar horas.
        
        Args:
            enable (bool): True para prevenir suspensión, False para permitirla.
        
        Note:
            - Solo funciona en sistemas Windows
            - Los errores se registran pero no interrumpen la ejecución
            - ES_CONTINUOUS (0x80000000): Mantiene el estado hasta que se cambie
            - ES_SYSTEM_REQUIRED (0x00000001): Requiere que el sistema esté activo
        
        Example:
            >>> SystemUtils.toggle_sleep_prevention(True)  # Prevenir suspensión
            >>> # ... realizar operación larga ...
            >>> SystemUtils.toggle_sleep_prevention(False)  # Restaurar comportamiento normal
        """
        try:
            if enable:
                # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
                # Previene que el sistema entre en suspensión
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
            else:
                # ES_CONTINUOUS
                # Restaura el comportamiento normal de energía
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        except Exception as e:
            print(f"Warning energía: {e}")

    @staticmethod
    def kill_process_tree(pid):
        """Termina un proceso y todos sus procesos hijos.
        
        Utiliza comandos específicos del sistema operativo para garantizar
        que tanto el proceso padre como todos sus hijos sean terminados.
        
        Args:
            pid (int): ID del proceso a terminar.
        
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        
        Note:
            - En Windows: Usa 'taskkill' con flags /F (forzar) y /T (árbol)
            - En Unix/Linux: Usa señal SIGKILL (9)
            - Los errores se manejan silenciosamente retornando False
        
        Example:
            >>> pid = 12345
            >>> if SystemUtils.kill_process_tree(pid):
            ...     print("Proceso terminado exitosamente")
            ... else:
            ...     print("No se pudo terminar el proceso")
        """
        try:
            if sys.platform == "win32":
                # Windows: taskkill con flags para terminar árbol de procesos
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Unix/Linux: señal SIGKILL
                os.kill(pid, 9)
            return True
        except Exception:
            return False

# =============================================================================
# CLASE 2: GESTOR DE BOTS (Lógica de Negocio y Procesos)
# =============================================================================
class BotManager:
    """Gestor de procesos de bots recolectores.
    
    Esta clase maneja la ejecución paralela de múltiples scripts de bots
    recolectores, coordinando su ejecución, monitoreando su salida y
    gestionando su ciclo de vida completo.
    
    Attributes:
        queue (queue.Queue): Cola de mensajes para comunicación con la UI.
        stop_event (threading.Event): Evento para señalizar detención de procesos.
        active_processes (list): Lista de procesos subprocess.Popen activos.
        list_lock (threading.Lock): Lock para acceso thread-safe a active_processes.
    
    Note:
        - Ejecuta hasta 4 bots en paralelo usando ThreadPoolExecutor
        - Captura y redirige la salida de cada bot a la UI
        - Maneja la terminación forzada de procesos de forma segura
    """
    
    def __init__(self, message_queue, stop_event):
        """Inicializa el gestor de bots.
        
        Args:
            message_queue (queue.Queue): Cola para enviar mensajes a la UI.
            stop_event (threading.Event): Evento para controlar detención de procesos.
        """
        self.queue = message_queue
        self.stop_event = stop_event
        self.active_processes = []
        self.list_lock = threading.Lock()

    def log(self, msg):
        """Envía un mensaje de log a la cola de mensajes.
        
        Args:
            msg (str): Mensaje a registrar en el log de la UI.
        """
        self.queue.put(("LOG", msg))

    def run_update_logic(self):
        """Ejecuta múltiples bots recolectores en paralelo.
        
        Este método es el punto de entrada principal para la actualización de
        bases de datos. Busca todos los scripts de bots en la carpeta designada
        y los ejecuta en paralelo usando un ThreadPoolExecutor.
        
        Flujo de ejecución:
            1. Previene suspensión del sistema
            2. Busca scripts Bot-recolector-*.py en carpeta Bots_recolectores
            3. Ejecuta hasta 4 bots simultáneamente
            4. Monitorea progreso y maneja señales de detención
            5. Restaura configuración de energía al finalizar
        
        Note:
            - Se ejecuta en un thread separado para no bloquear la UI
            - Envía mensajes de progreso a través de la cola de mensajes
            - Respeta el stop_event para detención controlada
            - Siempre envía FIN_ACTUALIZACION al terminar (éxito o error)
        
        Raises:
            Exception: Los errores se capturan, registran y no se propagan.
        """
        SystemUtils.toggle_sleep_prevention(True)
        try:
            carpeta_bots = "Bots_recolectores"
            patron = os.path.join(carpeta_bots, "Bot-recolector-*.py")
            archivos_bots = glob.glob(patron)
            
            if not archivos_bots:
                self.log(f"❌ No se encontraron bots en '{carpeta_bots}'.")
                self.queue.put(("FIN_ACTUALIZACION", None))
                return

            total_bots = len(archivos_bots)
            self.log(f"🚀 Iniciando actualización paralela: {total_bots} bots.")

            completed_count = 0
            # Ejecutor con máximo 6 workers para paralelización balanceada
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                # Crear futures para cada bot
                futures = {executor.submit(self._ejecutar_script_individual, f): f for f in archivos_bots}
                
                # Procesar bots a medida que completan
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_event.is_set():
                        # Detención solicitada: cancelar futures pendientes
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    completed_count += 1
                    self.queue.put(("PROGRESO", (completed_count, total_bots)))
                    
        except Exception as e:
            self.log(f"Error grave ejecutando bots: {e}")
        finally:
            SystemUtils.toggle_sleep_prevention(False)
            self.queue.put(("FIN_ACTUALIZACION", None))

    def _ejecutar_script_individual(self, script_path):
        """Ejecuta un script de bot individual y captura su salida.
        
        Este método privado maneja la ejecución de un único bot recolector,
        capturando su salida estándar y enviándola a la UI en tiempo real.
        
        Args:
            script_path (str): Ruta completa al script Python del bot.
        
        Proceso:
            1. Verifica si se solicitó detención antes de iniciar
            2. Configura el proceso con salida sin buffer y sin ventana
            3. Determina el ejecutable Python correcto (importante para PyInstaller)
            4. Captura salida línea por línea y la envía a la UI
            5. Limpia recursos al finalizar
        
        Note:
            - Se ejecuta en un thread del ThreadPoolExecutor
            - Usa CREATE_NO_WINDOW en Windows para ejecución silenciosa
            - PYTHONUNBUFFERED=1 garantiza salida en tiempo real
            - Thread-safe: usa lock para modificar active_processes
        
        Manejo de PyInstaller:
            Si la aplicación está empaquetada con PyInstaller, sys.executable
            apunta al .exe, no a Python. En ese caso, usa 'python' del sistema.
        """
        if self.stop_event.is_set(): 
            return

        # Extraer nombre limpio del bot para display
        nombre_bot = os.path.basename(script_path).replace("Bot-recolector-", "").replace(".py", "")
        
        # Configuración de ejecución del proceso
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW en Windows
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # Desactiva buffering para salida en tiempo real
        
        # Determinar ejecutable Python correcto
        if getattr(sys, 'frozen', False):
            # Aplicación empaquetada con PyInstaller
            # sys.executable es el .exe, necesitamos Python del sistema
            executable = "python"
        else:
            # Ejecución normal desde script Python
            executable = sys.executable

        cmd = [executable, script_path]

        proc = None
        try:
            # Crear proceso con salida capturada
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,      # Capturar stdout
                stderr=subprocess.STDOUT,     # Redirigir stderr a stdout
                text=True,                    # Modo texto (no bytes)
                bufsize=1,                    # Line buffering
                creationflags=flags,          # Flags específicos de plataforma
                env=env,                      # Variables de entorno
                encoding='utf-8',             # Codificación explícita
                errors='replace'              # Reemplazar caracteres inválidos
            )
            
            # Registrar proceso activo (thread-safe)
            with self.list_lock:
                self.active_processes.append(proc)
            
            # Notificar inicio del bot a la UI
            self.queue.put(("BOT_START", nombre_bot))

            # Leer y transmitir salida línea por línea
            for line in proc.stdout:
                if self.stop_event.is_set():
                    proc.terminate()
                    break
                line = line.strip()
                if line:
                    self.queue.put(("BOT_UPDATE", (nombre_bot, line)))
            
            # Esperar finalización del proceso
            proc.wait()
            self.queue.put(("BOT_FINISH", nombre_bot))
            
        except Exception as e:
            self.log(f"Error en {nombre_bot}: {e}")
        finally:
            # Limpieza: remover de lista de procesos activos
            if proc:
                with self.list_lock:
                    if proc in self.active_processes:
                        self.active_processes.remove(proc)

    def kill_all(self):
        """Termina forzosamente todos los procesos de bots activos.
        
        Este método se invoca cuando el usuario solicita detener la ejecución.
        Termina todos los procesos y sus hijos de forma segura y thread-safe.
        
        Returns:
            int: Número de procesos terminados exitosamente.
        
        Note:
            - Crea una copia de la lista de procesos para evitar problemas de concurrencia
            - Usa SystemUtils.kill_process_tree para terminar árbol completo
            - Thread-safe: usa lock solo para copiar la lista
        
        Example:
            >>> killed_count = bot_manager.kill_all()
            >>> print(f"Se terminaron {killed_count} procesos")
        """
        # Copiar lista de procesos de forma thread-safe
        with self.list_lock:
            procesos_copia = list(self.active_processes)
        
        # Terminar cada proceso y contar éxitos
        count = 0
        for proc in procesos_copia:
            if SystemUtils.kill_process_tree(proc.pid):
                count += 1
        return count

# =============================================================================
# CLASE 3: INTERFAZ GRÁFICA (Solo UI)
# =============================================================================
class EasyFindApp:
    """Aplicación principal de interfaz gráfica para EasyFind.
    
    Esta clase implementa la interfaz de usuario completa usando Tkinter,
    coordinando la ejecución de bots recolectores y búsquedas de precios,
    y proporcionando feedback visual en tiempo real al usuario.
    
    Arquitectura de la UI:
        - Header: Título y descripción de la aplicación
        - Monitor: Área scrollable con widgets individuales por cada bot
        - Progress Area: Barra de progreso y etiqueta de estado global
        - Buttons: Botones de acción (Actualizar BD, Buscar Precios, Detener)
        - Footer: Información de versión
        - Log Area: Consola de texto para mensajes generales
    
    Comunicación con threads:
        Usa un patrón producer-consumer con queue.Queue para comunicación
        thread-safe entre workers y la UI. Los threads de trabajo envían
        mensajes a la cola, y check_queue() los procesa en el thread principal.
    
    Attributes:
        root (tk.Tk): Ventana principal de Tkinter.
        stop_event (threading.Event): Evento para señalizar detención.
        message_queue (queue.Queue): Cola de mensajes desde threads workers.
        active_bot_widgets (dict): Mapeo de nombre_bot -> widgets UI.
        bot_manager (BotManager): Instancia del gestor de bots.
        
        Widgets principales:
            - canvas: Canvas con scrollbar para monitor de bots
            - frame_bots_container: Contenedor de widgets de bots
            - text_area: Área de texto para logs generales
            - progress_bar: Barra de progreso global
            - lbl_progreso: Etiqueta de estado de progreso
            - btn_actualizar: Botón "Actualizar BD"
            - btn_iniciar: Botón "Buscar Precios"
            - btn_detener: Botón "Detener"
    
    Note:
        - La UI se actualiza solo desde el thread principal (via check_queue)
        - Todas las operaciones largas se ejecutan en threads separados
        - La ventana se maximiza automáticamente al iniciar
    """
    
    def __init__(self, root):
        """Inicializa la aplicación EasyFind.
        
        Configura la ventana principal, inicializa variables de estado,
        construye todos los componentes de la UI y comienza el loop de
        procesamiento de mensajes.
        
        Args:
            root (tk.Tk): Instancia de la ventana principal de Tkinter.
        
        Proceso de inicialización:
            1. Configura geometría de ventana (maximizada)
            2. Inicializa variables de estado y cola de mensajes
            3. Crea instancia de BotManager
            4. Construye todos los componentes de UI
            5. Inicia loop de procesamiento de mensajes (check_queue)
        """
        self.root = root
        self.root.title("EasyFind - Suite de Precios")
        self._setup_window_geometry()
        
        # Variables de estado
        self.stop_event = threading.Event()
        self.message_queue = queue.Queue()
        self.active_bot_widgets = {}  # {nombre_bot: {frame, status, pb}}
        
        # Instancia del gestor de lógica
        self.bot_manager = BotManager(self.message_queue, self.stop_event)

        # Construcción de UI
        self._build_header()
        self._build_monitor()
        self._build_progress_area()
        self._build_buttons()
        self._build_footer()

        # Iniciar loop de mensajes
        self.root.after(100, self.check_queue)

    def _setup_window_geometry(self):
        """Configura la geometría de la ventana principal.
        
        Intenta maximizar la ventana usando el método 'zoomed'. Si falla
        (en algunos sistemas), establece el tamaño manualmente al tamaño
        de la pantalla.
        
        Note:
            - La ventana es redimensionable por el usuario
            - En Windows, 'zoomed' maximiza la ventana correctamente
        """
        try:
            self.root.state('zoomed')
        except:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}")
        self.root.resizable(True, True)

    # --- UI BUILDERS (Métodos para crear widgets) ---
    def _build_header(self):
        """Construye el encabezado de la aplicación.
        
        Crea un frame con el título principal y una descripción breve
        de la funcionalidad de la aplicación.
        """
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Label(frame, text="🔎 EasyFind Control Panel", font=("Segoe UI", 18, "bold"), fg="#333").pack()
        tk.Label(frame, text="Actualiza bases de datos y busca precios masivamente.", font=("Segoe UI", 10), fg="#666").pack(pady=2)

    def _build_monitor(self):
        """Construye el área de monitoreo de bots.
        
        Crea un canvas scrollable que contendrá widgets individuales para
        cada bot en ejecución, mostrando su estado y progreso en tiempo real.
        También incluye un área de texto scrollable para logs generales.
        
        Componentes:
            - Canvas con scrollbar vertical para widgets de bots
            - Frame contenedor dentro del canvas
            - ScrolledText para logs generales en la parte inferior
        
        Note:
            - El canvas se redimensiona automáticamente según el contenido
            - Los logs están deshabilitados para edición por el usuario
        """
        # Frame principal del monitor
        self.frame_monitor = tk.Frame(self.root)
        self.frame_monitor.pack(padx=15, pady=5, expand=True, fill='both')

        # Canvas con Scrollbar para widgets de bots
        self.canvas = tk.Canvas(self.frame_monitor, borderwidth=0, background="#f0f0f0")
        self.frame_bots_container = tk.Frame(self.canvas, background="#f0f0f0")
        vsb = tk.Scrollbar(self.frame_monitor, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame_bots_container, anchor="nw")
        
        # Actualizar scrollregion cuando cambia el contenido
        self.frame_bots_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Área de logs general (abajo)
        self.text_area = scrolledtext.ScrolledText(self.root, width=80, height=5, font=("Consolas", 8), state='disabled')
        self.text_area.pack(padx=15, pady=(0,5), fill='x')

    def _build_progress_area(self):
        """Construye el área de progreso global.
        
        Crea una etiqueta de estado y una barra de progreso que muestran
        el progreso general de la operación en curso.
        """
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=5, fill=tk.X)
        self.lbl_progreso = tk.Label(frame, text="Sistema listo.", font=("Segoe UI", 9), fg="#444")
        self.lbl_progreso.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=2)

    def _build_buttons(self):
        """Construye los botones de acción principales.
        
        Crea tres botones:
            - Actualizar BD: Ejecuta bots recolectores para actualizar bases de datos
            - Buscar Precios: Ejecuta búsqueda masiva de precios
            - Detener: Detiene la operación en curso
        
        Note:
            - El botón Detener está deshabilitado por defecto
            - Los botones cambian de estado según la operación en curso
        """
        frame = tk.Frame(self.root, pady=15)
        frame.pack()
        
        # Estilos comunes
        btn_config = {"font": ("Segoe UI", 11, "bold"), "width": 20, "height": 2}
        
        self.btn_actualizar = tk.Button(frame, text="ACTUALIZAR BD", bg="#28a745", fg="white", 
                                        command=self.action_start_update, **btn_config)
        self.btn_actualizar.pack(side=tk.LEFT, padx=10)

        self.btn_iniciar = tk.Button(frame, text="BUSCAR PRECIOS", bg="#007bff", fg="white", 
                                     command=self.action_start_search, **btn_config)
        self.btn_iniciar.pack(side=tk.LEFT, padx=10)

        self.btn_detener = tk.Button(frame, text="DETENER", bg="#dc3545", fg="white", state="disabled",
                                     command=self.action_stop, font=("Segoe UI", 11, "bold"), width=15, height=2)
        self.btn_detener.pack(side=tk.LEFT, padx=10)

    def _build_footer(self):
        """Construye el pie de página con información de versión."""
        tk.Label(self.root, text="Integración de Bots Recolectores", font=("Segoe UI", 8), fg="#aaa").pack(side=tk.BOTTOM, pady=5)

    # --- LÓGICA DE COLA Y EVENTOS ---
    def log(self, mensaje):
        """Registra un mensaje en el área de texto de logs.
        
        Args:
            mensaje (str): Mensaje a mostrar en el log.
        
        Note:
            - Habilita temporalmente el widget para insertar texto
            - Auto-scroll al final para mostrar el mensaje más reciente
            - Deshabilita el widget para prevenir edición del usuario
        """
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, str(mensaje) + "\n")
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')

    def update_progress(self, actual, total, extra=""):
        """Actualiza la barra de progreso y etiqueta de estado.
        
        Args:
            actual (int): Número de tareas completadas.
            total (int): Número total de tareas.
            extra (str, optional): Texto adicional para mostrar. Por defecto "".
        
        Note:
            - Calcula el porcentaje automáticamente
            - Solo actualiza si total > 0 para evitar división por cero
        """
        if total > 0:
            pct = (actual / total) * 100
            self.progress_bar['value'] = pct
            self.lbl_progreso.config(text=f"Progreso: {actual}/{total} ({pct:.0f}%) {extra}")

    def check_queue(self):
        """Procesa mensajes de la cola de comunicación con threads.
        
        Este método se ejecuta periódicamente (cada 100ms) en el thread
        principal de Tkinter para procesar mensajes enviados por threads
        workers. Implementa el patrón producer-consumer para comunicación
        thread-safe.
        
        Tipos de mensajes procesados:
            - LOG: Mensaje de log general
            - PROGRESO: Actualización de barra de progreso (actual, total)
            - BOT_START: Inicio de un bot (crea widget)
            - BOT_UPDATE: Actualización de estado de un bot
            - BOT_FINISH: Finalización de un bot
            - FIN_BUSQUEDA: Finalización de búsqueda de precios
            - FIN_ACTUALIZACION: Finalización de actualización de BD
            - ERROR_CRITICO: Error crítico (muestra messagebox)
        
        Note:
            - Se re-programa a sí mismo cada 100ms usando root.after()
            - Procesa todos los mensajes disponibles en cada iteración
            - Maneja queue.Empty de forma silenciosa
        """
        try:
            while True:
                tipo, dato = self.message_queue.get_nowait()
                if tipo == "LOG": 
                    self.log(dato)
                elif tipo == "PROGRESO": 
                    self.update_progress(*dato)
                elif tipo == "BOT_START": 
                    self._ui_add_bot_row(dato)
                elif tipo == "BOT_UPDATE": 
                    self._ui_update_bot_row(dato)
                elif tipo == "BOT_FINISH": 
                    self._ui_finish_bot_row(dato)
                elif tipo == "FIN_BUSQUEDA": 
                    self._on_search_finished(dato)
                elif tipo == "FIN_ACTUALIZACION": 
                    self._on_update_finished()
                elif tipo == "ERROR_CRITICO": 
                    messagebox.showerror("Error", dato)
        except queue.Empty:
            pass
        finally:
            # Re-programar para ejecutar nuevamente en 100ms
            self.root.after(100, self.check_queue)

    # --- MÉTODOS UI ESPECÍFICOS PARA BOTS ---
    def _ui_add_bot_row(self, nombre):
        """Crea y muestra un widget de monitoreo para un bot.
        
        Args:
            nombre (str): Nombre del bot (sin prefijo "Bot-recolector-").
        
        Componentes del widget:
            - Frame contenedor con borde
            - Label con nombre del bot
            - Progressbar indeterminada (animada)
            - Label de estado (muestra mensajes del bot)
        
        Note:
            - Si el bot ya tiene un widget, no crea uno nuevo
            - El widget se almacena en active_bot_widgets para actualizaciones
        """
        if nombre in self.active_bot_widgets: 
            return
        
        # Crear frame contenedor
        f = tk.Frame(self.frame_bots_container, bg="white", bd=1, relief="solid")
        f.pack(fill="x", pady=2, padx=5)
        
        # Label con nombre del bot
        tk.Label(f, text=nombre, font=("Segoe UI", 9, "bold"), width=15, anchor="w", bg="white").pack(side="left", padx=5)
        
        # Barra de progreso indeterminada
        pb = ttk.Progressbar(f, orient="horizontal", mode="indeterminate", length=200)
        pb.pack(side="left", padx=5)
        pb.start(10)  # Iniciar animación
        
        # Label de estado
        lbl = tk.Label(f, text="Iniciando...", font=("Segoe UI", 9), width=40, anchor="w", bg="white", fg="#555")
        lbl.pack(side="left", padx=5, fill="x", expand=True)

        # Almacenar referencias a widgets
        self.active_bot_widgets[nombre] = {"frame": f, "status": lbl, "pb": pb}

    def _ui_update_bot_row(self, data):
        """Actualiza el mensaje de estado de un bot.
        
        Args:
            data (tuple): Tupla (nombre_bot, mensaje) donde:
                - nombre_bot (str): Nombre del bot
                - mensaje (str): Nuevo mensaje de estado a mostrar
        
        Note:
            - Si el bot no tiene widget, no hace nada
            - El mensaje se muestra en el label de estado del bot
        """
        nombre, msj = data
        if nombre in self.active_bot_widgets:
            self.active_bot_widgets[nombre]["status"].config(text=msj)

    def _ui_finish_bot_row(self, nombre):
        """Marca un bot como finalizado en la UI.
        
        Args:
            nombre (str): Nombre del bot que finalizó.
        
        Cambios visuales:
            - Detiene la animación de la barra de progreso
            - Cambia a modo determinado y establece valor al 100%
            - Actualiza el mensaje a "✅ Finalizado" en verde
        
        Note:
            - Si el bot no tiene widget, no hace nada
        """
        if nombre in self.active_bot_widgets:
            w = self.active_bot_widgets[nombre]
            w["pb"].stop() 
            w["pb"].config(mode="determinate", value=100)  
            w["status"].config(text="Finalizado", fg="green")

    def _reset_ui(self, running_title=None):
        """Reinicia el estado de la UI para iniciar o finalizar una operación.
        
        Este método maneja dos modos de operación según el parámetro:
        
        Modo Ejecución (running_title != None):
            - Limpia el área de logs
            - Destruye todos los widgets de bots anteriores
            - Deshabilita botones de acción (Actualizar/Buscar)
            - Habilita botón Detener
            - Limpia el evento de detención
            - Registra mensaje de inicio
        
        Modo Idle (running_title == None):
            - Habilita botones de acción
            - Deshabilita botón Detener
            - Resetea barra de progreso a 0
            - Actualiza etiqueta de estado
            - Registra mensaje de finalización
        
        Args:
            running_title (str, optional): Título de la operación que inicia.
                Si es None, resetea a modo idle. Por defecto None.
        
        Example:
            >>> self._reset_ui("ACTUALIZACIÓN BD")  # Iniciar actualización
            >>> # ... operación en progreso ...
            >>> self._reset_ui(None)  # Volver a estado idle
        """
        if running_title:
            # Modo Ejecución: preparar UI para operación
            self.text_area.configure(state='normal')
            self.text_area.delete('1.0', tk.END)
            self.text_area.configure(state='disabled')
            
            # Limpiar widgets de bots anteriores
            for w in self.active_bot_widgets.values(): 
                w["frame"].destroy()
            self.active_bot_widgets.clear()
            
            # Deshabilitar botones de acción
            self.btn_iniciar.config(state="disabled", bg="#cccccc")
            self.btn_actualizar.config(state="disabled", bg="#cccccc")
            # Habilitar botón detener
            self.btn_detener.config(state="normal", bg="#dc3545", text="DETENER")
            self.stop_event.clear()
            self.log(f"--- INICIANDO: {running_title} ---")
        else:
            # Modo Idle: restaurar UI a estado inicial
            self.btn_iniciar.config(state="normal", bg="#007bff")
            self.btn_actualizar.config(state="normal", bg="#28a745")
            self.btn_detener.config(state="disabled")
            self.lbl_progreso.config(text="Esperando orden...")
            self.progress_bar['value'] = 0
            self.log("--- PROCESO FINALIZADO ---")

    # --- ACCIONES ---
    def action_start_search(self):
        """Inicia la búsqueda masiva de precios.
        
        Valida que exista el archivo de productos (PRODUCTOS.xlsx o .csv)
        antes de iniciar. Si existe, resetea la UI y lanza un thread
        para ejecutar la búsqueda sin bloquear la interfaz.
        
        Validaciones:
            - Verifica existencia de PRODUCTOS.xlsx o PRODUCTOS.csv
            - Muestra error si no se encuentra ningún archivo
        
        Note:
            - La búsqueda se ejecuta en un thread daemon separado
            - Usa el módulo EasyFind para la lógica de búsqueda
            - Los callbacks permiten comunicación con la UI via cola
        """
        if not (os.path.exists("PRODUCTOS.xlsx") or os.path.exists("PRODUCTOS.csv")):
            messagebox.showerror("Error", "Falta archivo PRODUCTOS.xlsx/csv")
            return
        
        self._reset_ui("BÚSQUEDA DE PRECIOS")
        
        threading.Thread(target=self._run_search_thread, daemon=True).start()

    def _run_search_thread(self):
        """Thread worker para ejecutar la búsqueda de precios.
        
        Este método se ejecuta en un thread separado y coordina la
        ejecución del módulo EasyFind, pasando callbacks para logging
        y actualización de progreso.
        
        Flujo:
            1. Define callbacks para log y progreso
            2. Ejecuta EasyFind.main() de forma asíncrona
            3. Captura errores y los envía a la UI
            4. Envía mensaje de finalización (con o sin error)
        
        Note:
            - Usa asyncio.run() para ejecutar código asíncrono
            - Los callbacks envían mensajes a la cola thread-safe
            - Siempre envía FIN_BUSQUEDA al terminar
        """
        error = False
        try:
            # Funciones auxiliares para pasar callbacks a EasyFind
            def _log_cb(m): 
                self.message_queue.put(("LOG", m))
            def _prog_cb(a, t): 
                self.message_queue.put(("PROGRESO", (a, t)))
            
            # Ejecutar búsqueda asíncrona
            asyncio.run(EasyFind.main(
                callback_log=_log_cb, 
                callback_progress=_prog_cb, 
                stop_event=self.stop_event
            ))
        except Exception as e:
            error = True
            self.message_queue.put(("ERROR_CRITICO", str(e)))
        finally:
            self.message_queue.put(("FIN_BUSQUEDA", error))

    def action_start_update(self):
        """Inicia la actualización masiva de bases de datos.
        
        Solicita confirmación al usuario antes de iniciar la actualización.
        Si se confirma, resetea la UI y lanza un thread para ejecutar
        los bots recolectores en paralelo.
        
        Note:
            - Muestra diálogo de confirmación antes de proceder
            - La actualización se ejecuta en un thread daemon separado
            - Delega la lógica de ejecución a BotManager
        """
        if messagebox.askyesno("Confirmar", "¿Ejecutar actualización masiva de bots?"):
            self._reset_ui("ACTUALIZACIÓN BD")
            threading.Thread(target=self.bot_manager.run_update_logic, daemon=True).start()

    def action_stop(self):
        """Detiene forzosamente la operación en curso.
        
        Solicita confirmación al usuario antes de detener. Si se confirma,
        deshabilita el botón detener y lanza un thread para ejecutar
        la lógica de detención forzada.
        
        Note:
            - Muestra diálogo de confirmación antes de proceder
            - La detención se ejecuta en un thread separado
            - Deshabilita el botón inmediatamente para evitar clics múltiples
        """
        if messagebox.askyesno("Stop", "¿Detener proceso forzosamente?"):
            self.log("DETENIENDO...")
            self.btn_detener.config(state="disabled")
            threading.Thread(target=self._force_stop_logic).start()

    def _force_stop_logic(self):
        """Lógica de detención forzada de procesos.
        
        Este método se ejecuta en un thread separado y realiza:
            1. Establece el evento de detención (stop_event)
            2. Termina todos los procesos activos via BotManager
            3. Registra cuántos procesos fueron terminados
            4. Espera 1 segundo para limpieza
            5. Resetea la UI a estado idle
        
        Note:
            - Se ejecuta en un thread separado para no bloquear la UI
            - Usa root.after(0, ...) para resetear UI en el thread principal
        """
        self.stop_event.set()
        killed = self.bot_manager.kill_all()
        if killed: 
            self.log(f"{killed} procesos eliminados.")
        time.sleep(1)
        # Resetear UI en el thread principal
        self.root.after(0, lambda: self._reset_ui(None))

    def _on_search_finished(self, error):
        """Callback cuando finaliza la búsqueda de precios.
        
        Args:
            error (bool): True si hubo un error, False si fue exitosa.
        
        Note:
            - Resetea la UI a estado idle
            - Muestra mensaje de éxito solo si no hubo error ni detención
        """
        self._reset_ui(None)
        if not error and not self.stop_event.is_set():
            messagebox.showinfo("Listo", "Búsqueda finalizada.")

    def _on_update_finished(self):
        """Callback cuando finaliza la actualización de bases de datos.
        
        Note:
            - Resetea la UI a estado idle
            - Muestra mensaje de éxito solo si no hubo detención
        """
        self._reset_ui(None)
        if not self.stop_event.is_set():
            messagebox.showinfo("Listo", "Actualización completada.")

if __name__ == "__main__":
    """Punto de entrada principal de la aplicación.
    
    Crea la ventana principal de Tkinter, instancia la aplicación EasyFind
    y comienza el loop de eventos de Tkinter.
    
    Example:
        Para ejecutar la aplicación:
        $ python App.py
    """
    ventana = tk.Tk()
    app = EasyFindApp(ventana)
    ventana.mainloop()