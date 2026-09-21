# Plex Bulk Metadata Locker / Unlocker 🎬

Script en Python para **bloquear o desbloquear masivamente** el estado de metadatos de ítems (películas, series, música, etc.) en tu servidor de **Plex Media Server**.

---

## 📌 ¿Para qué sirve?

En Plex, cuando editas un campo de metadatos manualmente (como la sinopsis, póster, título de ordenación o colecciones), Plex marca ese campo como **bloqueado (locked)** con un icono de candado anaranjado 🔒.

* **Desbloquear (Unlock):** Permite que los agentes de metadatos de Plex (TMDB, TVDB, Plex Movie, Plex Music) vuelvan a actualizar y sobrescribir automáticamente la información del ítem al hacer un "Refresh Metadata".
* **Bloquear (Lock):** Protege los campos de metadatos para evitar que Plex modifique tus cambios personalizados al escanear.

---

## 🛠️ Requisitos e Instalación

1. Asegúrate de tener **Python 3.8+** instalado.
2. Clona o descarga los archivos en tu equipo.
3. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

---

## 🔑 Cómo obtener tu Plex Token (X-Plex-Token)

Para conectar el script con tu servidor Plex necesitas tu token personal:
1. Abre Plex Web y selecciona cualquier película o serie.
2. Haz clic en el menú de tres puntos `...` y selecciona **Ver XML** (Get Info / View XML).
3. En la barra de direcciones de tu navegador, busca el parámetro al final de la URL: `X-Plex-Token=XXXXXX`.
4. Copia el valor de ese token.

*(Opcional: Puedes crear un archivo `.env` en la misma carpeta basándote en `.env.example` con tu URL y Token para no tener que ingresarlos cada vez).*

---

## 🚀 Formas de uso

El script soporta **Modo Interactivo** (guía paso a paso) y **Modo Línea de Comandos (CLI)**.

### 1️⃣ Modo Interactivo (Recomendado para principiantes)
Simplemente ejecuta el script sin argumentos y te guiará mediante un menú accesible:

```bash
python plex_bulk_locker.py
```

Te pedirá:
* Acción: Desbloquear o Bloquear.
* Selección de la biblioteca (Películas, Series, etc. o TODAS).
* Campos a procesar (Título, Sinopsis, Póster, Colecciones, Año, o TODOS los campos).

---

### 2️⃣ Modo Línea de Comandos (CLI)

Puedes automatizar o ejecutar comandos directos pasándole parámetros:

#### 🔹 Desbloquear TODOS los campos de una biblioteca completa:
```bash
python plex_bulk_locker.py --action unlock --library "Películas" --all-fields
```

#### 🔹 Bloquear solo campos específicos (`title` y `summary`) en la biblioteca 'Series':
```bash
python plex_bulk_locker.py --action lock --library "Series" --fields title summary
```

#### 🔹 Desbloquear el póster (`thumb` y `poster`) en películas específicas filtrando por nombre:
```bash
python plex_bulk_locker.py --action unlock --library "Películas" --fields thumb poster --search "Batman"
```

#### 🧪 Modo Simulación (Dry Run)
Puedes agregar `--dry-run` o `-d` a cualquier comando para probar y ver qué se modificaría **sin realizar ningún cambio real** en Plex:
```bash
python plex_bulk_locker.py --action unlock --library "Películas" --all-fields --dry-run
```

---

## 📋 Lista de Campos de Metadatos Disponibles

| Campo Plex | Descripción en Español |
| :--- | :--- |
| `title` | Título del contenido |
| `titleSort` | Título de ordenación (Sort Title) |
| `originalTitle` | Título original |
| `summary` | Sinopsis / Resumen |
| `contentRating` | Clasificación por edad (PG-13, TV-MA, etc.) |
| `userRating` | Calificación otorgada por el usuario |
| `rating` | Calificación de la crítica (Rotten Tomatoes, IMDb) |
| `studio` | Estudio / Productora |
| `tagline` | Lema / Frase publicitaria |
| `year` | Año de estreno |
| `originallyAvailableAt` | Fecha exacta de estreno |
| `thumb` | Póster / Miniatura principal |
| `art` | Fondo / Fanart de pantalla |
| `banner` | Banner promocional |
| `collection` | Colecciones asignadas |
| `genre` | Géneros |
| `director` | Directores |
| `writer` | Guionistas |
| `producer` | Productores |
| `country` | País de origen |
