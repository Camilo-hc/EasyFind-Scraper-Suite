$version = "1.0.0"
$zipName = "..\EasyFind_Software_$version.zip"
$sourceDir = "..\Distribucion"

# Rutas relativas desde scripts/ hacia la raiz del proyecto
$rootDir = ".."

echo "========================================="
echo " Creando paquete de distribucion v$version"
echo "========================================="

# Crear carpeta temporal
mkdir $sourceDir -Force | Out-Null
mkdir "$sourceDir\TIENDAS" -Force | Out-Null
mkdir "$sourceDir\Bots_recolectores" -Force | Out-Null

# 1. Ejecutable (ya tiene browsers y Python dentro)
echo "[1/4] Copiando ejecutable..."
if (Test-Path "$rootDir\dist\EasyFind_Suite.exe") {
    Copy-Item "$rootDir\dist\EasyFind_Suite.exe" -Destination $sourceDir
}
else {
    echo "ERROR: No se encuentra dist\EasyFind_Suite.exe"
    echo "       Ejecuta primero COMPILAR.bat"
    pause
    exit
}

# 2. Bases de datos de tiendas
echo "[2/4] Copiando bases de datos (TIENDAS)..."
Copy-Item "$rootDir\TIENDAS\*" -Destination "$sourceDir\TIENDAS" -Recurse -ErrorAction SilentlyContinue

# 3. Bots recolectores
echo "[3/4] Copiando bots recolectores..."
Copy-Item "$rootDir\Bots_recolectores\*" -Destination "$sourceDir\Bots_recolectores" -Recurse -ErrorAction SilentlyContinue

# 4. Archivo de productos
echo "[4/4] Copiando PRODUCTOS.xlsx..."
if (Test-Path "$rootDir\PRODUCTOS.xlsx") {
    Copy-Item "$rootDir\PRODUCTOS.xlsx" -Destination $sourceDir
}

# 5. Manual de Usuario
echo "[5/5] Copiando MANUAL_USUARIO.md..."
if (Test-Path "$rootDir\docs\MANUAL_USUARIO.md") {
    Copy-Item "$rootDir\docs\MANUAL_USUARIO.md" -Destination $sourceDir
}

# Crear ZIP
echo ""
echo "Comprimiendo..."
if (Test-Path $zipName) { Remove-Item $zipName }
Compress-Archive -Path "$sourceDir\*" -DestinationPath $zipName

# Limpiar
Remove-Item $sourceDir -Recurse -Force

echo ""
echo "========================================="
echo " LISTO: EasyFind_Software_$version.zip"
echo " Ubicacion: carpeta raiz del proyecto"
echo ""
echo " Contenido:"
echo "   - EasyFind_Suite.exe"
echo "   - TIENDAS/ (bases de datos)"
echo "   - Bots_recolectores/ (scripts)"
echo "   - PRODUCTOS.xlsx"
echo "   - MANUAL_USUARIO.md"
echo "========================================="
echo ""
pause
