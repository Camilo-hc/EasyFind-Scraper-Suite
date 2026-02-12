"""
Diálogos modales de la aplicación EasyFind.

Contiene la ventana de selección de tiendas para la actualización
de bases de datos.
"""

import os
import tkinter as tk
from tkinter import messagebox


class StoreSelectionDialog(tk.Toplevel):
    """Una ventana de diálogo modal para seleccionar qué tiendas (bots) actualizar.

    Attributes:
        result (list): Almacena la lista de rutas de bots seleccionados después de cerrar el diálogo.
    """

    def __init__(self, parent, bot_files):
        """Inicializa el diálogo.

        Args:
            parent (tk.Widget): El widget padre (usualmente la ventana principal).
            bot_files (list): Lista de rutas de archivos de bots disponibles para mostrar.
        """
        super().__init__(parent)
        self.title("Seleccionar Tiendas a Actualizar")
        self.geometry("500x600")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()
        
        self.bot_files = bot_files
        self.result = None
        self.checkboxes = {}
        
        self._build_ui()
        
    def _build_ui(self):
        """Construye la interfaz de usuario del diálogo."""

        header_frame = tk.Frame(self, bg="#f8f9fa", pady=15)
        header_frame.pack(fill=tk.X)
        tk.Label(
            header_frame, 
            text="🏪 Selecciona las tiendas a actualizar",
            font=("Segoe UI", 14, "bold"),
            bg="#f8f9fa",
            fg="#333"
        ).pack()
        tk.Label(
            header_frame,
            text="Marca las tiendas que deseas actualizar",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#666"
        ).pack()
        
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(
            btn_frame,
            text="✓ Seleccionar Todas",
            command=self._select_all,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="✗ Deseleccionar Todas",
            command=self._deselect_all,
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="#ddd")
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for bot_file in sorted(self.bot_files):
            bot_name = os.path.basename(bot_file).replace("Bot-recolector-", "").replace(".py", "")

            var = tk.BooleanVar(value=True)
            self.checkboxes[bot_file] = var
            
            cb_frame = tk.Frame(scrollable_frame, bg="white", pady=5)
            cb_frame.pack(fill=tk.X, padx=10)
            
            cb = tk.Checkbutton(
                cb_frame,
                text=bot_name,
                variable=var,
                font=("Segoe UI", 10),
                bg="white",
                activebackground="white",
                anchor="w"
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.count_label = tk.Label(
            self,
            text=self._get_count_text(),
            font=("Segoe UI", 9),
            fg="#666"
        )
        self.count_label.pack(pady=5)

        for var in self.checkboxes.values():
            var.trace_add("write", lambda *args: self._update_count())

        action_frame = tk.Frame(self, pady=15)
        action_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(
            action_frame,
            text="Aceptar",
            command=self._on_accept,
            bg="#007bff",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            height=2
        ).pack(side=tk.LEFT, padx=5, expand=True)
        
        tk.Button(
            action_frame,
            text="Cancelar",
            command=self._on_cancel,
            bg="#6c757d",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            height=2
        ).pack(side=tk.LEFT, padx=5, expand=True)
    
    def _select_all(self):
        """Selecciona todos los checkboxes en la lista."""
        for var in self.checkboxes.values():
            var.set(True)
    
    def _deselect_all(self):
        """Deselecciona todos los checkboxes en la lista."""
        for var in self.checkboxes.values():
            var.set(False)
    
    def _get_count_text(self):
        """Retorna la cadena formateada mostrando el conteo de ítems seleccionados."""
        selected = sum(1 for var in self.checkboxes.values() if var.get())
        total = len(self.checkboxes)
        return f"Seleccionadas: {selected} de {total} tiendas"
    
    def _update_count(self):
        """Actualiza la etiqueta de conteo de selección."""
        self.count_label.config(text=self._get_count_text())
    
    def _on_accept(self):
        """Maneja el clic en el botón 'Aceptar'."""
        selected = [bot_file for bot_file, var in self.checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning(
                "Sin selección",
                "Debes seleccionar al menos una tienda para actualizar.",
                parent=self
            )
            return
        
        self.result = selected
        self.destroy()
    
    def _on_cancel(self):
        """Maneja el clic en el botón 'Cancelar'."""
        self.result = None
        self.destroy()
