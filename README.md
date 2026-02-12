# EasyFind - Suite de Comparación de Precios Automatizada

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Async-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-FF6F00?style=for-the-badge&logo=python&logoColor=white)

> 🌐 [English version](README_EN.md)

## Descripción

EasyFind es un sistema automatizado de comparación de precios para productos eléctricos de proveedores chilenos. Combina una interfaz gráfica Tkinter con un motor de scraping asíncrono basado en Playwright para buscar precios en múltiples tiendas simultáneamente.

## Características Principales

- 🔍 Búsqueda inteligente con coincidencia difusa (RapidFuzz)
- ⚡ Procesamiento paralelo de hasta 8 productos simultáneamente
- 🤖 Actualización masiva de bases de datos mediante bots recolectores
- 📊 Interfaz gráfica con monitoreo en tiempo real
- 💾 Guardado automático cada 100 productos

## Requisitos

- Python 3.10 o superior
- Navegadores de Playwright (Chromium)
- Conexión a internet

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Camilo-hc/EasyFind-Scraper-Suite.git
cd EasyFind-Scraper-Suite

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install chromium
```

## Estructura del Proyecto

```
EasyFind-Scraper-Suite/
│
├── README.md                           # Este archivo
├── README_EN.md                        # Documentación en inglés
├── LICENSE                             # Licencia MIT
├── requirements.txt                    # Dependencias Python
├── .gitignore
│
├── App.py                              # Entry point (shim → src/easyfind)
├── EasyFind.py                         # Shim de compatibilidad
│
├── src/                                # Código fuente modular
│   └── easyfind/
│       ├── __init__.py                 # Paquete principal (versión, exports)
│       ├── __main__.py                 # python -m easyfind
│       ├── config.py                   # Configuración y constantes
│       ├── utils.py                    # Normalización de texto y precios
│       ├── store_strategies.py         # Estrategias por tienda
│       ├── content_parser.py           # Parseo genérico de HTML
│       ├── web_scraper.py              # Scraping con Playwright
│       ├── data_manager.py             # Carga de BD y matching difuso
│       ├── engine.py                   # Orquestador principal
│       ├── bot_dependencies.py         # Helper para PyInstaller
│       └── gui/                        # Interfaz gráfica
│           ├── __init__.py
│           ├── app.py                  # Ventana principal
│           ├── dialogs.py              # Diálogos modales
│           └── system_utils.py         # Gestión de procesos y SO
│
├── TIENDAS/                            # Bases de datos de proveedores
│   └── Base_Datos_*.xlsx
│
├── Bots_recolectores/                  # Scripts de actualización
│   └── Bot-recolector-*.py
│
└── scripts/                            # Herramientas de build
    ├── COMPILAR.bat
    └── CREAR_ZIP.ps1
```

## Formato de Archivos

### PRODUCTOS.xlsx (Entrada)

Debe contener una columna llamada `ItemName`, `Descripcion` o `Producto`:

| ItemName |
|----------|
| CABLE UTP CAT6 305M AZUL |
| PATCH CORD CAT6A 3M GRIS |
| FIBRA OPTICA 24F MONOMODO |

### Bases de Datos (Carpeta TIENDAS/)

Archivos `.xlsx` o `.csv` con las columnas `Nombre` y `Link`:

| Nombre | Link |
|--------|------|
| CABLE UTP CAT6 AZUL 305M | https://tienda.cl/producto/123 |
| PATCH CORD CAT6A 3M | https://tienda.cl/producto/456 |

Patrón de nombres: `Base_Datos_[NOMBRE_TIENDA].xlsx`

### Resultado.xlsx (Salida)

El archivo generado contiene columnas adicionales por cada tienda:

| ItemName | TIENDA1 Link | TIENDA1 Marca | TIENDA1 Precio | TIENDA2 Link | TIENDA2 Marca | TIENDA2 Precio |
|----------|--------------|---------------|----------------|--------------|---------------|----------------|
| CABLE UTP CAT6... | https://... | 3M | 45000 | https://... | PANDUIT | 48000 |

**Valores especiales en columnas de precio:**
- Número: Precio en CLP (sin IVA cuando aplica)
- `Link no encontrado`: No se encontró el producto en la base de datos
- `Ver Web / Login`: La tienda requiere login (solo se extrajo la marca)
- `Error / No Detectado`: No se pudo extraer el precio de la página

## Uso

### Ejecutar la Aplicación

```bash
python App.py
```

### Operaciones Disponibles

#### 1. Buscar Precios

1. Asegurarse de tener el archivo `PRODUCTOS.xlsx` en la carpeta raíz
2. Hacer clic en el botón **"BUSCAR PRECIOS"**
3. Esperar a que termine el proceso
4. Revisar el archivo `Resultado.xlsx` generado

#### 2. Actualizar Bases de Datos

1. Colocar los scripts de bots en la carpeta `Bots_recolectores/`
2. Los scripts deben seguir el patrón: `Bot-recolector-[NOMBRE].py`
3. Hacer clic en **"ACTUALIZAR BD"**
4. Seleccionar las tiendas y confirmar
5. Monitorear el progreso de cada bot en la interfaz

#### 3. Detener Proceso

- Hacer clic en **"DETENER"** durante cualquier operación
- Los datos procesados hasta el momento se guardan automáticamente

## Configuración

### Ajustar Velocidad de Scraping

Editar `src/easyfind/config.py`, clase `Config`:

```python
CONCURRENCIA_GLOBAL = 8          # Total de pestañas simultáneas (default: 8)
CONCURRENCIA_POR_TIENDA = 2      # Máximo por dominio (default: 2)
TAMANO_LOTE_GUARDADO = 100       # Guardar cada N productos (default: 100)
```

---

## Autor

**Camilo Hernández**

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).
