"""
Entry point para ejecutar EasyFind como módulo: python -m easyfind

Soporta:
  - Modo GUI normal (sin argumentos)
  - Modo dispatcher para PyInstaller (con argumento .py)
"""

import sys
import runpy

# Importar bot_dependencies para forzar inclusión en PyInstaller
from . import bot_dependencies  # noqa: F401


def main():
    """Punto de entrada principal de la aplicación."""
    # --- LÓGICA DE DISPATCHER (Para ejecutar bots sin Python instalado) ---
    if len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
        script_to_run = sys.argv[1]
        try:
            sys.argv.pop(0)
            runpy.run_path(script_to_run, run_name="__main__")
        except Exception as e:
            print(f"Error crítico ejecutando script interno: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()  # Asegurar que el error se envíe al proceso padre
        
        # IMPORTANTE: No usar input() aquí, ya que congela el subproceso
        # si no hay terminal interactiva (caso PyInstaller --noconsole)
        sys.exit(1)
    
    # --- INICIO NORMAL DE LA GUI ---
    import tkinter as tk
    from .gui.app import EasyFindApp
    
    ventana = tk.Tk()
    app = EasyFindApp(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
