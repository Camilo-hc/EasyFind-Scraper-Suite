# Script PowerShell para crear ZIP de distribución automáticamente
# EasyFind Suite - Paquete de Distribución

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     CREANDO ZIP DE DISTRIBUCION - EasyFind Suite" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuración
$packageName = "EasyFind_Suite_Package"
$zipName = "EasyFind_Suite_v2.2_CORREGIDO.zip"

# 1. Verificar que existe el ejecutable compilado
if (-not (Test-Path "dist\EasyFind_Suite.exe")) {
    Write-Host "[ERROR] No se encuentra el ejecutable compilado." -ForegroundColor Red
    Write-Host "Por favor ejecuta COMPILAR.bat primero." -ForegroundColor Yellow
    pause
    exit 1
}

# 2. Limpiar carpeta de paquete anterior
Write-Host "[*] Limpiando paquete anterior..." -ForegroundColor Yellow
if (Test-Path $packageName) {
    Remove-Item $packageName -Recurse -Force
}

# 3. Crear carpeta de paquete
Write-Host "[*] Creando carpeta de paquete..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $packageName | Out-Null

# 4. Copiar ejecutable
Write-Host "[*] Copiando ejecutable..." -ForegroundColor Yellow
Copy-Item "dist\EasyFind_Suite.exe" -Destination $packageName

# 5. Copiar archivos de configuración
Write-Host "[*] Copiando archivos de configuracion..." -ForegroundColor Yellow
Copy-Item "PRODUCTOS.xlsx" -Destination $packageName
Copy-Item "INSTRUCCIONES_INSTALACION.txt" -Destination $packageName
Copy-Item "requirements.txt" -Destination $packageName

# 6. Copiar carpetas completas
Write-Host "[*] Copiando carpeta Bots_recolectores..." -ForegroundColor Yellow
Copy-Item "Bots_recolectores" -Destination $packageName -Recurse

Write-Host "[*] Copiando carpeta TIENDAS..." -ForegroundColor Yellow
Copy-Item "TIENDAS" -Destination $packageName -Recurse

Write-Host "[*] Copiando carpeta browsers (esto puede tardar un poco, ~640 MB)..." -ForegroundColor Yellow
Copy-Item "browsers" -Destination $packageName -Recurse

# 7. Verificar contenido
Write-Host ""
Write-Host "[*] Verificando contenido del paquete..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Archivos en el paquete:" -ForegroundColor Cyan
Get-ChildItem $packageName | Select-Object Name, Length | Format-Table -AutoSize

# 8. Crear ZIP
Write-Host "[*] Creando archivo ZIP..." -ForegroundColor Yellow
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

Compress-Archive -Path $packageName -DestinationPath $zipName -CompressionLevel Optimal

# 9. Mostrar resultado
$zipSize = (Get-Item $zipName).Length / 1MB
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "     ZIP CREADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Archivo creado: $zipName" -ForegroundColor Cyan
Write-Host "Tamaño: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "El archivo está listo para distribuir!" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
