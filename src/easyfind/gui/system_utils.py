"""
Utilidades del sistema y gestión de procesos de bots.

Contiene clases para operaciones de bajo nivel del SO (prevención de suspensión,
terminación de procesos) y gestión del ciclo de vida de bots recolectores.
"""

import os
import sys
import glob
import subprocess
import threading
import concurrent.futures

from .dialogs import StoreSelectionDialog


class SystemUtils:
    """Clase de utilidad para operaciones relacionadas con el sistema.

    Proporciona métodos estáticos para interactuar con el sistema operativo,
    específicamente para la gestión de energía y gestión de procesos.
    """

    @staticmethod
    def toggle_sleep_prevention(enable):
        """Alterna el estado de prevención de suspensión del sistema (Solo Windows)."""
        try:
            import ctypes
            if enable:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        except Exception as e:
            print(f"Warning energía: {e}")

    @staticmethod
    def kill_process_tree(pid):
        """Termina un proceso y todos sus procesos hijos.

        Args:
            pid (int): El ID del Proceso (PID) del proceso padre a terminar.

        Returns:
            bool: True si la terminación fue exitosa, False en caso contrario.
        """
        try:
            if sys.platform == "win32":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.kill(pid, 9)
            return True
        except Exception:
            return False


class BotManager:
    """Gestiona la ejecución y el ciclo de vida de los procesos de bots.

    Maneja la ejecución de múltiples scripts de bots en paralelo, capturando su salida,
    y proporcionando un mecanismo para detenerlos de forma segura.

    Attributes:
        queue (queue.Queue): Cola thread-safe para enviar mensajes a la UI.
        stop_event (threading.Event): Bandera de evento para señalar la detención de procesos.
        active_processes (list): Lista de objetos de subprocesos ejecutándose actualmente.
        list_lock (threading.Lock): Bloqueo para asegurar acceso seguro a active_processes.
    """

    def __init__(self, message_queue, stop_event):
        """Inicializa el BotManager.

        Args:
            message_queue (queue.Queue): Cola para comunicación con la UI.
            stop_event (threading.Event): Evento para controlar el flujo de ejecución.
        """
        self.queue = message_queue
        self.stop_event = stop_event
        self.active_processes = []
        self.list_lock = threading.Lock()

    def log(self, msg):
        """Envía un mensaje de log a la UI."""
        self.queue.put(("LOG", msg))

    def run_update_logic(self, selected_bots=None):
        """Lógica principal para ejecutar bots de actualización de base de datos.

        Ejecuta los bots seleccionados en paralelo usando un ThreadPoolExecutor.

        Args:
            selected_bots (list, optional): Lista de rutas de archivos de bots a ejecutar.
        """
        SystemUtils.toggle_sleep_prevention(True)
        try:
            if selected_bots is None:
                carpeta_bots = "Bots_recolectores"
                patron = os.path.join(carpeta_bots, "Bot-recolector-*.py")
                archivos_bots = glob.glob(patron)
            else:
                archivos_bots = selected_bots
            
            if not archivos_bots:
                self.log(f"❌ No se encontraron bots para ejecutar.")
                self.queue.put(("FIN_ACTUALIZACION", None))
                return

            total_bots = len(archivos_bots)
            self.log(f"🚀 Iniciando actualización paralela: {total_bots} bots.")

            completed_count = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(self._ejecutar_script_individual, f): f for f in archivos_bots}
                
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_event.is_set():
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

        Args:
            script_path (str): Ruta completa al script de python a ejecutar.
        """
        if self.stop_event.is_set(): 
            return

        nombre_bot = os.path.basename(script_path).replace("Bot-recolector-", "").replace(".py", "")

        flags = 0x08000000 if sys.platform == "win32" else 0
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        executable = sys.executable
        cmd = [executable, script_path]

        proc = None
        try:
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,      
                stderr=subprocess.STDOUT,     
                text=True,                    
                bufsize=1,                    
                creationflags=flags,          
                env=env,                      
                encoding='utf-8',             
                errors='replace'              
            )

            with self.list_lock:
                self.active_processes.append(proc)

            self.queue.put(("BOT_START", nombre_bot))

            for line in proc.stdout:
                if self.stop_event.is_set():
                    proc.terminate()
                    break
                line = line.strip()
                if line:
                    self.queue.put(("BOT_UPDATE", (nombre_bot, line)))

            proc.wait()
            self.queue.put(("BOT_FINISH", nombre_bot))
            
        except Exception as e:
            self.log(f"Error en {nombre_bot}: {e}")
        finally:
            if proc:
                with self.list_lock:
                    if proc in self.active_processes:
                        self.active_processes.remove(proc)

    def kill_all(self):
        """Termina forzosamente todos los procesos de bots activos.

        Returns:
            int: La cantidad de procesos terminados exitosamente.
        """
        with self.list_lock:
            procesos_copia = list(self.active_processes)
        
        count = 0
        for proc in procesos_copia:
            if SystemUtils.kill_process_tree(proc.pid):
                count += 1
        return count
