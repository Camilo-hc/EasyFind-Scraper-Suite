@echo off
echo =======================================================
echo      INICIANDO COMPILACION DE EASYFIND
echo =======================================================

:: 1. Limpiar residuos de compilaciones anteriores
echo [*] Limpiando carpetas 'build' y 'dist'...
if exist ..\build rmdir /s /q ..\build
if exist ..\dist rmdir /s /q ..\dist
if exist *.spec del *.spec

:: 2. Ejecutar PyInstaller
:: --distpath ..\dist: Guardar el exe en la carpeta raiz/dist
:: --workpath ..\build: Guardar temporales en la carpeta raiz/build
:: --specpath .: Guardar el .spec en la carpeta actual (scripts)

echo [*] Compilando... Por favor espera.
echo [!] NOTA: Este proceso tomara varios minutos debido al tamano de los navegadores (~640MB)

:: Usamos el shim App.py en la raiz como punto de entrada
:: Agregamos src como ruta de busqueda para que encuentre easyfind
:: hidden-import easyfind asegura que el paquete se incluya

pyinstaller --noconfirm --onefile --windowed ^
    --name "EasyFind_Suite" ^
    --distpath "..\dist" ^
    --workpath "..\build" ^
    --specpath "." ^
    --paths "..\src" ^
    --add-data "..\Bots_recolectores;Bots_recolectores" ^
    --add-data "..\TIENDAS;TIENDAS" ^
    --add-data "..\browsers;browsers" ^
    --hidden-import "easyfind" ^
    --collect-all "easyfind" ^
    "..\App.py"

echo.
echo =======================================================
echo      COMPILACION FINALIZADA CON EXITO
echo =======================================================
echo.
echo Tu ejecutable esta listo en la carpeta: dist/EasyFind_Suite.exe (en la raiz del proyecto)
echo.
pause