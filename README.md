# EasyFind - Automated Price Comparison Suite

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Async-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-FF6F00?style=for-the-badge&logo=python&logoColor=white)

## Description

EasyFind is an automated price comparison system for electrical products from Chilean suppliers. It combines a Tkinter GUI with an asynchronous Playwright-based scraping engine to search prices across multiple stores simultaneously.

## Key Features

- Intelligent search with fuzzy matching
- Parallel processing of up to 8 products simultaneously
- Bulk database updates via collector bots
- GUI with real-time monitoring
- Automatic saving every 100 products

## Requirements

- Python 3.10 or higher
- Playwright browsers (Chromium)
- Internet connection

## Installation

```bash
# Navigate to project directory
cd Easy_Find_Proyecto

# Install dependencies
pip install pandas playwright beautifulsoup4 openpyxl requests python-dotenv urllib3

# Install Playwright browsers
playwright install chromium
```

## Project Structure

```
Easy_Find_Proyecto/
│
├── App.py                          # Main application with GUI
├── EasyFind.py                     # Search and scraping engine
│
├── PRODUCTOS.xlsx                  # Input file with products to search
│
├── TIENDAS/                        # Vendor databases
│   ├── Base_Datos_Store1.xlsx
│   ├── Base_Datos_Store2.xlsx
│   ├── Base_Datos_Store3.xlsx
│   └── ...
│
└── Bots_recolectores/              # Scripts to update databases
    ├── Bot-recolector-Store1.py
    ├── Bot-recolector-Store2.py
    └── ...
```

## File Formats

### PRODUCTOS.xlsx (Input)

Must contain a column named `ItemName`, `Descripcion`, or `Producto`:

| ItemName |
|----------|
| CABLE UTP CAT6 305M AZUL |
| PATCH CORD CAT6A 3M GRIS |
| FIBRA OPTICA 24F MONOMODO |

### Databases (TIENDAS/ Folder)

`.xlsx` or `.csv` files with `Nombre` and `Link` columns:

| Nombre | Link |
|--------|------|
| CABLE UTP CAT6 AZUL 305M | https://tienda.cl/producto/123 |
| PATCH CORD CAT6A 3M | https://tienda.cl/producto/456 |

File naming pattern: `Base_Datos_[STORE_NAME].xlsx`

### Resultado.xlsx (Output)

Generated file contains additional columns per store:

| ItemName | ARTILEC Link | ARTILEC Marca | ARTILEC Precio | LK Link | LK Marca | LK Precio |
|----------|--------------|---------------|----------------|---------|----------|-----------|
| CABLE UTP CAT6... | https://... | 3M | 45000 | https://... | PANDUIT | 48000 |

**Special values in price columns:**
- Number: Price in CLP (without VAT when applicable)
- `Link no encontrado`: Product not found in database
- `Ver Web / Login`: Store requires login (only brand extracted)
- `ERROR / NO DETECTADO`: Could not extract price from page

## Usage

### Run the Application

```bash
python App.py
```

### Available Operations

#### 1. Search Prices

1. Ensure `PRODUCTOS.xlsx` file exists in root folder
2. Click **"BUSCAR PRECIOS"** button
3. Wait for process to complete
4. Review generated `Resultado.xlsx` file

**Process:**
- Reads `PRODUCTOS.xlsx` file
- Searches for matches in local databases (`TIENDAS/` folder)
- Scrapes found URLs to get prices and brands
- Saves results to `Resultado.xlsx`

#### 2. Update Databases

1. Place bot scripts in `Bots_recolectores/` folder
2. Scripts must follow pattern: `Bot-recolector-[NAME].py`
3. Click **"ACTUALIZAR BD"** button
4. Confirm operation
5. Monitor progress of each bot in the interface

**Features:**
- Executes up to 4 bots in parallel
- Shows real-time progress for each bot
- Captures output from each script

#### 3. Stop Process

- Click **"DETENER"** during any operation
- Confirm stop action
- Processed data is automatically saved

## Configuration

### Adjust Scraping Speed

Edit `EasyFind.py`, `Config` class:

```python
CONCURRENCIA_GLOBAL = 8          # Total simultaneous tabs (default: 8)
CONCURRENCIA_POR_TIENDA = 2      # Maximum per domain (default: 2)
TAMANO_LOTE_GUARDADO = 100       # Save every N products (default: 100)
```

## Usage Examples

### Example 1: Basic Search

**PRODUCTOS.xlsx file:**
```
ItemName
CABLE UTP CAT6 305M
PATCH CORD CAT5E 2M
```

**Command:**
```bash
python App.py
# Click "BUSCAR PRECIOS"
```

**Expected result:**
- `Resultado.xlsx` file with prices from all configured stores
- `Resultado_Parcial.xlsx` file with intermediate saves

### Example 2: Update Store Database

**Structure:**
```
Bots_recolectores/
└── Bot-recolector-Store1.py
```

**Command:**
```bash
python App.py
# Click "ACTUALIZAR BD"
```

**Expected result:**
- Bot executes and updates `TIENDAS/Base_Datos_Store1.xlsx`
- Progress visible in GUI

## Notes

- `PRODUCTOS.xlsx` file is required for price search
- System automatically saves every 100 processed products
- If process is stopped, processed data is saved to `Resultado.xlsx`
- Internet connection required for scraping and USD/CLP exchange rate
- Partial files saved as `Resultado_Parcial.xlsx`

---

## Descripción

EasyFind es un sistema automatizado de comparación de precios para productos eléctricos de proveedores chilenos. Combina una interfaz gráfica Tkinter con un motor de scraping asíncrono basado en Playwright para buscar precios en múltiples tiendas simultáneamente.

## Características Principales

- Búsqueda inteligente con coincidencia difusa
- Procesamiento paralelo de hasta 8 productos simultáneamente
- Actualización masiva de bases de datos mediante bots recolectores
- Interfaz gráfica con monitoreo en tiempo real
- Guardado automático cada 100 productos

## Requisitos

- Python 3.10 o superior
- Navegadores de Playwright (Chromium)
- Conexión a internet

## Instalación

```bash
# Navegar al directorio del proyecto
cd Easy_Find_Proyecto

# Instalar dependencias
pip install pandas playwright beautifulsoup4 openpyxl requests python-dotenv urllib3

# Instalar navegadores de Playwright
playwright install chromium
```

## Estructura del Proyecto

```
Easy_Find_Proyecto/
│
├── App.py                          # Aplicación principal con interfaz gráfica
├── EasyFind.py                     # Motor de búsqueda y scraping
│
├── PRODUCTOS.xlsx                  # Archivo de entrada con productos a buscar
│
├── TIENDAS/                        # Bases de datos de proveedores
│   ├── Base_Datos_Tienda1.xlsx
│   ├── Base_Datos_Tienda2.xlsx
│   ├── Base_Datos_Tienda3.xlsx
│   └── ...
│
└── Bots_recolectores/              # Scripts para actualizar bases de datos
    ├── Bot-recolector-Tienda1.py
    ├── Bot-recolector-Tienda2.py
    └── ...
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

| ItemName | ARTILEC Link | ARTILEC Marca | ARTILEC Precio | LK Link | LK Marca | LK Precio |
|----------|--------------|---------------|----------------|---------|----------|-----------|
| CABLE UTP CAT6... | https://... | 3M | 45000 | https://... | PANDUIT | 48000 |

**Valores especiales en columnas de precio:**
- Número: Precio en CLP (sin IVA cuando aplica)
- `Link no encontrado`: No se encontró el producto en la base de datos
- `Ver Web / Login`: La tienda requiere login (solo se extrajo la marca)
- `ERROR / NO DETECTADO`: No se pudo extraer el precio de la página

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

**Proceso:**
- Lee el archivo `PRODUCTOS.xlsx`
- Busca coincidencias en las bases de datos locales (carpeta `TIENDAS/`)
- Hace scraping de las URLs encontradas para obtener precios y marcas
- Guarda los resultados en `Resultado.xlsx`

#### 2. Actualizar Bases de Datos

1. Colocar los scripts de bots en la carpeta `Bots_recolectores/`
2. Los scripts deben seguir el patrón: `Bot-recolector-[NOMBRE].py`
3. Hacer clic en **"ACTUALIZAR BD"**
4. Confirmar la operación
5. Monitorear el progreso de cada bot en la interfaz

**Características:**
- Ejecuta hasta 4 bots en paralelo
- Muestra el progreso de cada bot en tiempo real
- Captura la salida de cada script

#### 3. Detener Proceso

- Hacer clic en **"DETENER"** durante cualquier operación
- Confirmar la detención
- Los datos procesados hasta el momento se guardan automáticamente

## Configuración

### Ajustar Velocidad de Scraping

Editar `EasyFind.py`, clase `Config`:

```python
CONCURRENCIA_GLOBAL = 8          # Total de pestañas simultáneas (default: 8)
CONCURRENCIA_POR_TIENDA = 2      # Máximo por dominio (default: 2)
TAMANO_LOTE_GUARDADO = 100       # Guardar cada N productos (default: 100)
```

## Ejemplos de Uso

### Ejemplo 1: Búsqueda Básica

**Archivo PRODUCTOS.xlsx:**
```
ItemName
CABLE UTP CAT6 305M
PATCH CORD CAT5E 2M
```

**Comando:**
```bash
python App.py
# Hacer clic en "BUSCAR PRECIOS"
```

**Resultado esperado:**
- Archivo `Resultado.xlsx` con precios de todas las tiendas configuradas
- Archivo `Resultado_Parcial.xlsx` con guardados intermedios

### Ejemplo 2: Actualizar Base de Datos de una Tienda

**Estructura:**
```
Bots_recolectores/
└── Bot-recolector-Tienda1.py
```

**Comando:**
```bash
python App.py
# Hacer clic en "ACTUALIZAR BD"
```

**Resultado esperado:**
- El bot se ejecuta y actualiza `TIENDAS/Base_Datos_Tienda1.xlsx`
- Progreso visible en la interfaz gráfica

## Notas

- El archivo `PRODUCTOS.xlsx` es obligatorio para la búsqueda de precios
- El sistema guarda automáticamente cada 100 productos procesados
- Si se detiene el proceso, los datos procesados se guardan en `Resultado.xlsx`
- Se requiere conexión a internet para scraping y obtener la tasa de cambio USD/CLP
- Los archivos parciales se guardan como `Resultado_Parcial.xlsx`

---

## Author / Autor

**Camilo Hernández**

## License / Licencia

Internal use only. All rights reserved. / Uso interno. Todos los derechos reservados.