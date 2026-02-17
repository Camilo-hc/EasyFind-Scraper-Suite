# Manual de Usuario - EasyFind

Este documento explica cómo instalar y utilizar el software EasyFind para la comparación de precios.

## 1. Instalación y Primeros Pasos

### 1.1 Descarga
Cuando recibas el archivo `EasyFind_Software_vX.X.X.zip`:

1.  **Descomprimir**: Haz clic derecho sobre el archivo ZIP y selecciona "Extraer todo..." o usa tu programa de descompresión favorito (WinRAR, 7-Zip).
2.  **Ubicación**: Coloca la carpeta extraída en una ubicación accesible (por ejemplo, en Documentos o Escritorio). **No** ejecutes el programa directamente desde dentro del ZIP sin extraerlo primero.

### 1.2 Contenido de la Carpeta
Dentro de la carpeta encontrarás:

*   `EasyFind_Suite.exe`: El programa principal.
*   `PRODUCTOS.xlsx`: Archivo Excel donde debes ingresar los productos a buscar.
*   `TIENDAS/`: Carpeta que contiene las bases de datos de productos por tienda.
*   `Bots_recolectores/`: Carpeta que contiene los scripts para actualizar los precios.

## 2. Buscar Precios

Para buscar precios de productos en las tiendas configuradas:

1.  **Preparar el archivo Excel**:
    *   Abre el archivo `PRODUCTOS.xlsx`.
    *   En la columna `ItemName` (o `Descripcion`), escribe los nombres de los productos que deseas buscar.
    *   Guarda y cierra el archivo.
2.  **Ejecutar EasyFind**:
    *   Haz doble clic en `EasyFind_Suite.exe`.
    *   Espera unos segundos a que se abra la ventana principal.
3.  **Iniciar Búsqueda**:
    *   Haz clic en el botón azul **"BUSCAR PRECIOS"**.
    *   El programa leerá `PRODUCTOS.xlsx`, buscará coincidencias en las bases de datos y luego consultará los precios en internet.
4.  **Resultados**:
    *   Al finalizar, se generará un archivo `Resultado.xlsx` con los precios encontrados.
    *   Si detienes el proceso antes, se guardará un `Resultado_Interrumpido.xlsx` o `Resultado_Parcial.xlsx`.

## 3. Actualizar Bases de Datos

Si necesitas actualizar la lista de productos y enlaces de las tiendas:

1.  **Ejecutar EasyFind**: Abre `EasyFind_Suite.exe`.
2.  **Iniciar Actualización**:
    *   Haz clic en el botón verde **"ACTUALIZAR BD"**.
    *   Se abrirá una ventana para seleccionar qué tiendas actualizar.
    *   Selecciona las tiendas deseadas y haz clic en "Aceptar".
3.  **Proceso**:
    *   Se abrirán ventanas de navegador (controladas por el bot) para extraer la información. **No cierres estas ventanas manualmente**; el programa lo hará.
    *   Al finalizar, los archivos en la carpeta `TIENDAS/` se habrán actualizado.

## 4. Solución de Problemas

*   **El programa no abre**:
    *   Asegúrate de haber extraído todo el contenido del ZIP.
    *   Si tu antivirus bloquea el archivo, añade una excepción para `EasyFind_Suite.exe`.
*   **Error "Falta archivo PRODUCTOS.xlsx"**:
    *   Asegúrate de que el archivo `PRODUCTOS.xlsx` esté en la misma carpeta que el ejecutable.
*   **Resultados vacíos o "Link no encontrado"**:
    *   El nombre del producto en `PRODUCTOS.xlsx` podría no coincidir con los de las bases de datos. Intenta usar nombres más generales o verificar cómo están escritos en las tiendas.

## Notas Adicionales / Requisitos
*   Sistema Operativo: Windows 10 o superior.
*   Conexión a Internet estable requerida para la búsqueda de precios.
