@echo off
echo =======================================================
echo      INICIANDO COMPILACION DE EASYFIND
echo =======================================================

:: 1. Limpiar residuos de compilaciones anteriores
echo [*] Limpiando carpetas 'build' y 'dist'...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

:: 2. Ejecutar PyInstaller
:: --noconfirm: Sobrescribe sin preguntar
:: --onefile: Genera un solo archivo .exe
:: --windowed: No muestra la consola negra al abrir la App
:: --add-data: Incluye tus carpetas de bots y tiendas (Formato: "origen;destino")
:: --hidden-import: Asegura que EasyFind se incluya

echo [*] Compilando... Por favor espera.
echo [!] NOTA: Este proceso tomara varios minutos debido al tamano de los navegadores (~640MB)
pyinstaller --noconfirm --onefile --windowed ^
    --name "EasyFind_Suite" ^
    --add-data "Bots_recolectores;Bots_recolectores" ^
    --add-data "TIENDAS;TIENDAS" ^
    --add-data "browsers;browsers" ^
    --hidden-import "EasyFind" ^
    --collect-all "EasyFind" ^
    "App.py"

echo.
echo =======================================================
echo      COMPILACION FINALIZADA CON EXITO
echo =======================================================
echo.
echo Tu ejecutable esta listo en la carpeta: dist/EasyFind_Suite.exe
echo.
pause