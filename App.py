"""
EasyFind - Suite de Precios.

Este archivo es un shim de compatibilidad que lanza la aplicación
desde el paquete reorganizado en src/easyfind/.

Uso:
    python App.py
"""

import sys
import os

# Agregar src/ al path para encontrar el paquete easyfind
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from easyfind.__main__ import main

if __name__ == "__main__":
    main()