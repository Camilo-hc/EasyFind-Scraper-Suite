# EasyFind - Automated Price Comparison Suite

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Async-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-FF6F00?style=for-the-badge&logo=python&logoColor=white)

> 🌐 [Versión en español](README.md)

## Description

EasyFind is an automated price comparison system for electrical products from Chilean suppliers. It combines a Tkinter GUI with an asynchronous Playwright-based scraping engine to search prices across multiple stores simultaneously.

## Key Features

- 🔍 Intelligent search with fuzzy matching (RapidFuzz)
- ⚡ Parallel processing of up to 8 products simultaneously
- 🤖 Bulk database updates via collector bots
- 📊 GUI with real-time monitoring
- 💾 Automatic saving every 100 products

## Requirements

- Python 3.10 or higher
- Playwright browsers (Chromium)
- Internet connection

## Installation

```bash
# Clone the repository
git clone https://github.com/Camilo-hc/EasyFind-Scraper-Suite.git
cd EasyFind-Scraper-Suite

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Project Structure

```
EasyFind-Scraper-Suite/
│
├── README.md                           # Documentation (Spanish)
├── README_EN.md                        # This file
├── LICENSE                             # MIT License
├── requirements.txt                    # Python dependencies
├── .gitignore
│
├── App.py                              # Entry point (shim → src/easyfind)
├── EasyFind.py                         # Compatibility shim
│
├── src/                                # Modular source code
│   └── easyfind/
│       ├── __init__.py                 # Main package (version, exports)
│       ├── __main__.py                 # python -m easyfind
│       ├── config.py                   # Configuration and constants
│       ├── utils.py                    # Text normalization and price parsing
│       ├── store_strategies.py         # Per-store extraction strategies
│       ├── content_parser.py           # Generic HTML parsing
│       ├── web_scraper.py              # Playwright-based scraping
│       ├── data_manager.py             # Database loading and fuzzy matching
│       ├── engine.py                   # Main orchestrator
│       ├── bot_dependencies.py         # PyInstaller helper
│       └── gui/                        # Graphical interface
│           ├── __init__.py
│           ├── app.py                  # Main window
│           ├── dialogs.py              # Modal dialogs
│           └── system_utils.py         # Process and OS management
│
├── TIENDAS/                            # Vendor databases
│   └── Base_Datos_*.xlsx
│
├── Bots_recolectores/                  # Update scripts
│   └── Bot-recolector-*.py
│
└── scripts/                            # Build tools
    ├── COMPILAR.bat
    └── CREAR_ZIP.ps1
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
- `Error / No Detectado`: Could not extract price from page

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

#### 2. Update Databases

1. Place bot scripts in `Bots_recolectores/` folder
2. Scripts must follow pattern: `Bot-recolector-[NAME].py`
3. Click **"ACTUALIZAR BD"** button
4. Select stores and confirm
5. Monitor progress of each bot in the interface

#### 3. Stop Process

- Click **"DETENER"** during any operation
- Processed data is automatically saved

## Configuration

### Adjust Scraping Speed

Edit `src/easyfind/config.py`, `Config` class:

```python
CONCURRENCIA_GLOBAL = 8          # Total simultaneous tabs (default: 8)
CONCURRENCIA_POR_TIENDA = 2      # Maximum per domain (default: 2)
TAMANO_LOTE_GUARDADO = 100       # Save every N products (default: 100)
```

---

## Author

**Camilo Hernández**

## License

This project is licensed under the [MIT License](LICENSE).
