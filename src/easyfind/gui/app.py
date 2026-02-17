"""
Clase principal de la aplicación GUI de EasyFind.

Coordina la interfaz gráfica con Tkinter, la ejecución de bots recolectores
y la lógica de búsqueda de precios.
"""

import os
import glob
import threading
import asyncio
import queue
import time

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

from ..engine import main as easyfind_main
from .system_utils import BotManager
from .dialogs import StoreSelectionDialog


# Paleta de colores
COLOR_BG         = "#0F172A"   # Azul noche profundo
COLOR_BG_DARK    = "#020617"   # Casi negro (para panels internos)
COLOR_CARD       = "#1E293B"   # Card / panel intermedio
COLOR_TEXT       = "#E2E8F0"   # Texto claro principal
COLOR_TEXT_DIM   = "#94A3B8"   # Texto secundario / dim
COLOR_GREEN      = "#22C55E"   # Verde neón (Matrix)
COLOR_CYAN       = "#06B6D4"   # Cian neón
COLOR_RED        = "#FF1744"   # Rojo neón brillante
COLOR_DISABLED   = "#334155"   # Botón deshabilitado
COLOR_ACCENT     = "#3B82F6"   # Azul acento (progress)
COLOR_FOOTER     = "#6B7280"   # Gris sutil footer


class EasyFindApp:
    """Clase principal de la aplicación para la GUI de EasyFind.

    Attributes:
        root (tk.Tk): La ventana principal de Tkinter.
        stop_event (threading.Event): Evento global para señalar la detención.
        message_queue (queue.Queue): Cola para recibir actualizaciones de hilos.
        active_bot_widgets (dict): Mapea nombres de bots a sus widgets.
        bot_manager (BotManager): Instancia del BotManager.
    """

    def __init__(self, root):
        """Inicializa la aplicación EasyFind.

        Args:
            root (tk.Tk): La instancia de la ventana raíz de Tkinter.
        """
        self.root = root
        self.root.title("EasyFind")
        self.root.configure(bg=COLOR_BG)
        self._setup_window_geometry()

        self.stop_event = threading.Event()
        self.message_queue = queue.Queue()
        self.active_bot_widgets = {}

        self.bot_manager = BotManager(self.message_queue, self.stop_event)

        # Estilo ttk para barras de progreso
        self._configure_styles()

        self._build_header()
        self._build_monitor()
        self._build_progress_area()
        self._build_buttons()
        self._build_footer()

        self.root.after(100, self.check_queue)

    def _configure_styles(self):
        """Configura estilos ttk personalizados para el tema oscuro."""
        style = ttk.Style()
        style.theme_use('default')

        # Barra de progreso global – cian sobre fondo oscuro
        style.configure("Hacker.Horizontal.TProgressbar",
                        troughcolor=COLOR_BG_DARK,
                        background=COLOR_CYAN,
                        thickness=8)

        # Barra de progreso de bots – verde
        style.configure("Bot.Horizontal.TProgressbar",
                        troughcolor=COLOR_BG_DARK,
                        background=COLOR_GREEN,
                        thickness=6)

    def _setup_window_geometry(self):
        """Configura la geometría de la ventana principal."""
        try:
            self.root.state('zoomed')
        except:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}")
        self.root.resizable(True, True)

    def _build_header(self):
        """Construye el encabezado de la aplicación con título y descripción."""
        frame = tk.Frame(self.root, bg=COLOR_BG)
        frame.pack(pady=(20, 10))
        tk.Label(frame, text="EasyFind Control Panel",
                 font=("Consolas", 22, "bold"), fg=COLOR_GREEN, bg=COLOR_BG).pack()
        tk.Label(frame, text="Actualiza bases de datos y busca precios masivamente.",
                 font=("Consolas", 10), fg=COLOR_TEXT_DIM, bg=COLOR_BG).pack(pady=4)

    def _build_monitor(self):
        """Construye el área de monitoreo."""
        self.frame_monitor = tk.Frame(self.root, bg=COLOR_BG)
        self.frame_monitor.pack(padx=20, pady=5, expand=True, fill='both')

        self.canvas = tk.Canvas(self.frame_monitor, borderwidth=0,
                                background=COLOR_CARD, highlightthickness=1,
                                highlightbackground=COLOR_CYAN)
        self.frame_bots_container = tk.Frame(self.canvas, background=COLOR_CARD)
        vsb = tk.Scrollbar(self.frame_monitor, orient="vertical",
                           command=self.canvas.yview,
                           bg=COLOR_CARD, troughcolor=COLOR_BG_DARK,
                           activebackground=COLOR_CYAN)
        
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame_bots_container, anchor="nw")
        
        self.frame_bots_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Terminal de logs – fondo negro, texto verde matrix
        self.text_area = scrolledtext.ScrolledText(
            self.root, width=80, height=5,
            font=("Consolas", 9), state='disabled',
            bg="#000000", fg=COLOR_GREEN,
            insertbackground=COLOR_GREEN,
            selectbackground=COLOR_CYAN, selectforeground="#000000",
            relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=COLOR_CYAN)
        self.text_area.pack(padx=20, pady=(5,5), fill='x')

    def _build_progress_area(self):
        """Construye la barra de progreso global y la etiqueta de estado."""
        frame = tk.Frame(self.root, bg=COLOR_BG)
        frame.pack(padx=20, pady=5, fill=tk.X)
        self.lbl_progreso = tk.Label(frame, text="Sistema listo.",
                                     font=("Consolas", 9), fg=COLOR_TEXT_DIM, bg=COLOR_BG)
        self.lbl_progreso.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal",
                                            mode="determinate",
                                            style="Hacker.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=2)

    def _build_buttons(self):
        """Construye los botones de acción principales."""
        frame = tk.Frame(self.root, pady=15, bg=COLOR_BG)
        frame.pack()

        btn_common = {
            "font": ("Consolas", 11, "bold"),
            "width": 20, "height": 2,
            "relief": tk.FLAT,
            "cursor": "hand2",
            "activeforeground": "#FFFFFF",
        }

        # ── ACTUALIZAR BD  (borde verde neón) ──
        self.btn_actualizar = tk.Button(
            frame, text="⚙  ACTUALIZAR BD",
            bg=COLOR_BG_DARK, fg=COLOR_GREEN,
            activebackground="#064E3B",
            highlightbackground=COLOR_GREEN, highlightthickness=2,
            command=self.action_start_update, **btn_common)
        self.btn_actualizar.pack(side=tk.LEFT, padx=10)

        # ── BUSCAR PRECIOS  (borde cian neón) ──
        self.btn_iniciar = tk.Button(
            frame, text="◉  BUSCAR PRECIOS",
            bg=COLOR_BG_DARK, fg=COLOR_CYAN,
            activebackground="#164E63",
            highlightbackground=COLOR_CYAN, highlightthickness=2,
            command=self.action_start_search, **btn_common)
        self.btn_iniciar.pack(side=tk.LEFT, padx=10)

        # ── DETENER  (borde rojo neón) ──
        self.btn_detener = tk.Button(
            frame, text="⏻  DETENER",
            bg=COLOR_BG_DARK, fg=COLOR_RED,
            activebackground="#4C0519",
            highlightbackground=COLOR_RED, highlightthickness=2,
            state="disabled",
            command=self.action_stop,
            font=("Consolas", 11, "bold"),
            width=15, height=2,
            relief=tk.FLAT, cursor="hand2")
        self.btn_detener.pack(side=tk.LEFT, padx=10)

    def _build_footer(self):
        """Construye el pie de página de la aplicación."""
        footer = tk.Frame(self.root, bg=COLOR_BG_DARK)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.lbl_status = tk.Label(
            footer,
            text="Status: Sistema activo. Integración de Bots Recolectores.",
            font=("Consolas", 9), fg=COLOR_FOOTER, bg=COLOR_BG_DARK,
            anchor="w", padx=10, pady=4)
        self.lbl_status.pack(fill=tk.X)

    def log(self, mensaje):
        """Añade un mensaje al área de log desplazable."""
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, str(mensaje) + "\n")
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')

    def update_progress(self, actual, total, extra=""):
        """Actualiza la barra de progreso global y la etiqueta."""
        if total > 0:
            pct = (actual / total) * 100
            self.progress_bar['value'] = pct
            self.lbl_progreso.config(text=f"Progreso: {actual}/{total} ({pct:.0f}%) {extra}")

    def check_queue(self):
        """Sondea la cola de mensajes para actualizaciones de hilos en segundo plano."""
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
            self.root.after(100, self.check_queue)

    def _ui_add_bot_row(self, nombre):
        """Añade una nueva fila de progreso para un bot específico."""
        if nombre in self.active_bot_widgets: 
            return
        
        f = tk.Frame(self.frame_bots_container, bg=COLOR_BG, bd=0,
                     highlightthickness=1, highlightbackground=COLOR_CARD)
        f.pack(fill="x", pady=2, padx=5)
        
        tk.Label(f, text=nombre, font=("Consolas", 9, "bold"), width=15,
                 anchor="w", bg=COLOR_BG, fg=COLOR_CYAN).pack(side="left", padx=5)
        
        pb = ttk.Progressbar(f, orient="horizontal", mode="indeterminate",
                             length=200, style="Bot.Horizontal.TProgressbar")
        pb.pack(side="left", padx=5)
        pb.start(10)
        
        lbl = tk.Label(f, text="Iniciando...", font=("Consolas", 9), width=40,
                       anchor="w", bg=COLOR_BG, fg=COLOR_TEXT_DIM)
        lbl.pack(side="left", padx=5, fill="x", expand=True)

        self.active_bot_widgets[nombre] = {"frame": f, "status": lbl, "pb": pb}

    def _ui_update_bot_row(self, data):
        """Actualiza el texto de estado de una fila de bot específica."""
        nombre, msj = data
        if nombre in self.active_bot_widgets:
            self.active_bot_widgets[nombre]["status"].config(text=msj)

    def _ui_finish_bot_row(self, nombre):
        """Marca la fila de un bot específico como finalizada."""
        if nombre in self.active_bot_widgets:
            w = self.active_bot_widgets[nombre]
            w["pb"].stop() 
            w["pb"].config(mode="determinate", value=100)  
            w["status"].config(text="Finalizado", fg=COLOR_GREEN)

    def _reset_ui(self, running_title=None):
        """Reinicia el estado de la UI entre modos 'Ejecutando' e 'Inactivo'."""
        try:
            if running_title:
                self.text_area.configure(state='normal')
                self.text_area.delete('1.0', tk.END)
                self.text_area.configure(state='disabled')
                
                for w in self.active_bot_widgets.values(): 
                    try:
                        w["frame"].destroy()
                    except:
                        pass
                self.active_bot_widgets.clear()
                
                self.btn_iniciar.config(state="disabled", bg=COLOR_DISABLED, fg=COLOR_TEXT_DIM)
                self.btn_actualizar.config(state="disabled", bg=COLOR_DISABLED, fg=COLOR_TEXT_DIM)
                self.btn_detener.config(state="normal", bg=COLOR_BG_DARK, fg=COLOR_RED)
                self.stop_event.clear()
                self.log(f"--- INICIANDO: {running_title} ---")
            else:
                self.btn_iniciar.config(state="normal", bg=COLOR_BG_DARK, fg=COLOR_CYAN)
                self.btn_actualizar.config(state="normal", bg=COLOR_BG_DARK, fg=COLOR_GREEN)
                self.btn_detener.config(state="disabled", bg=COLOR_DISABLED, fg=COLOR_TEXT_DIM)
                self.lbl_progreso.config(text="Esperando orden...")
                self.progress_bar['value'] = 0
                self.log("--- PROCESO FINALIZADO ---")
        except Exception as e:
            print(f"Error en _reset_ui: {e}")

    def action_start_search(self):
        """Inicia el proceso de búsqueda masiva de precios."""
        if not (os.path.exists("PRODUCTOS.xlsx") or os.path.exists("PRODUCTOS.csv")):
            messagebox.showerror("Error", "Falta archivo PRODUCTOS.xlsx/csv")
            return
        
        self._reset_ui("BÚSQUEDA DE PRECIOS")
        threading.Thread(target=self._run_search_thread, daemon=True).start()

    def _run_search_thread(self):
        """Hilo en segundo plano para ejecutar la lógica de búsqueda de precios."""
        error = False
        try:
            def _log_cb(m): 
                self.message_queue.put(("LOG", m))
            def _prog_cb(a, t): 
                self.message_queue.put(("PROGRESO", (a, t)))
            
            asyncio.run(easyfind_main(
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
        """Inicia el proceso de actualización de la base de datos."""
        carpeta_bots = "Bots_recolectores"
        patron = os.path.join(carpeta_bots, "Bot-recolector-*.py")
        archivos_bots = glob.glob(patron)
        
        if not archivos_bots:
            messagebox.showerror("Error", f"No se encontraron bots en '{carpeta_bots}'.")
            return
        
        dialog = StoreSelectionDialog(self.root, archivos_bots)
        self.root.wait_window(dialog)
        
        if dialog.result is None:
            return
        
        selected_bots = dialog.result
        
        self._reset_ui("ACTUALIZACIÓN BD")
        threading.Thread(
            target=lambda: self.bot_manager.run_update_logic(selected_bots),
            daemon=True
        ).start()

    def action_stop(self):
        """Acción del usuario para detener forzosamente el proceso en ejecución."""
        if messagebox.askyesno("Stop", "¿Detener proceso forzosamente?"):
            self.log("DETENIENDO...")
            self.btn_detener.config(state="disabled")
            threading.Thread(target=self._force_stop_logic, daemon=True).start()

    def _force_stop_logic(self):
        """Lógica en segundo plano para detener todos los procesos."""
        try:
            self.stop_event.set()
            killed = self.bot_manager.kill_all()
            if killed: 
                self.log(f"{killed} procesos eliminados.")
            time.sleep(1)

            try:
                self.root.after(0, lambda: self._reset_ui(None))
            except Exception as e:
                print(f"Warning: No se pudo resetear UI via after: {e}")
                self._reset_ui(None)
        except Exception as e:
            print(f"Error en _force_stop_logic: {e}")
            try:
                self.log(f"Error al detener: {e}")
            except:
                pass

    def _on_search_finished(self, error):
        """Manejador de callback para cuando finaliza el proceso de búsqueda."""
        self._reset_ui(None)
        if not error and not self.stop_event.is_set():
            messagebox.showinfo("Listo", "Búsqueda finalizada.")

    def _on_update_finished(self):
        """Manejador de callback para cuando finaliza el proceso de actualización."""
        self._reset_ui(None)
        if not self.stop_event.is_set():
            messagebox.showinfo("Listo", "Actualización completada.")
