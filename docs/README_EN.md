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

| ItemName | STORE1 Link | STORE1 Marca | STORE1 Precio | STORE2 Link | STORE2 Marca | STORE2 Precio |
|----------|-------------|--------------|---------------|-------------|--------------|---------------|
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

## Author / Autor

**Camilo Hernández**

## License / Licencia

Internal use only. All rights reserved. / Uso interno. Todos los derechos reservados.
