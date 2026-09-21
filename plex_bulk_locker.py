#!/usr/bin/env python3
"""
Script de Python para cambiar el estado de bloqueado (lock / unlock) de items en Plex Media Server de forma masiva.

Requisitos:
    pip install plexapi python-dotenv tqdm colorama

Uso:
    - Modo interactivo: python plex_bulk_locker.py
    - Modo CLI (ejemplos):
        python plex_bulk_locker.py --action unlock --library "Películas" --all-fields
        python plex_bulk_locker.py --action lock --library "Películas" --fields title summary year
        python plex_bulk_locker.py --action unlock --library "Series" --fields poster thumb --dry-run
"""

import os
import sys
import argparse
from typing import List, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from plexapi.server import PlexServer
    from plexapi.exceptions import BadRequest, NotFound, Unauthorized
except ImportError:
    print("❌ Error: La librería 'plexapi' no está instalada.")
    print("   Por favor instala las dependencias ejecutando: pip install -r requirements.txt")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    # Fallback si tqdm no está instalado
    def tqdm(iterable, **kwargs):
        return iterable

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
except ImportError:
    GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = BOLD = ""

# Lista de campos de metadatos bloqueables en Plex
PLEX_FIELDS = [
    "title",
    "titleSort",
    "originalTitle",
    "summary",
    "contentRating",
    "userRating",
    "rating",
    "studio",
    "tagline",
    "year",
    "originallyAvailableAt",
    "thumb",
    "art",
    "banner",
    "theme",
    "collection",
    "genre",
    "director",
    "writer",
    "producer",
    "country",
    "mood",
    "style"
]

NOMBRES_CAMPOS_ES = {
    "title": "Título",
    "titleSort": "Título de ordenación",
    "originalTitle": "Título original",
    "summary": "Sinopsis / Resumen",
    "contentRating": "Clasificación por edad",
    "userRating": "Calificación de usuario",
    "rating": "Calificación (Crítica)",
    "studio": "Estudio",
    "tagline": "Lema / Frase",
    "year": "Año",
    "originallyAvailableAt": "Fecha de estreno",
    "thumb": "Póster / Miniatura",
    "art": "Fondo / Fanart",
    "banner": "Banner",
    "theme": "Tema musical",
    "collection": "Colecciones",
    "genre": "Géneros",
    "director": "Directores",
    "writer": "Guionistas",
    "producer": "Productores",
    "country": "País",
    "mood": "Estado de ánimo",
    "style": "Estilo"
}


def conectar_plex(url: Optional[str] = None, token: Optional[str] = None) -> PlexServer:
    """Establece conexión con el servidor Plex."""
    plex_url = url or os.getenv("PLEX_URL")
    plex_token = token or os.getenv("PLEX_TOKEN")

    if not plex_url:
        plex_url = input(f"{CYAN}Ingrese la URL de su servidor Plex (ej. http://127.0.0.1:32400): {RESET}").strip()
    if not plex_token:
        plex_token = input(f"{CYAN}Ingrese su Plex Token (X-Plex-Token): {RESET}").strip()

    if not plex_url or not plex_token:
        print(f"{RED}❌ Error: Se requieren la URL y el Token de Plex.{RESET}")
        sys.exit(1)

    print(f"\n{CYAN}Conectando a Plex Server en {plex_url}...{RESET}")
    try:
        plex = PlexServer(plex_url, plex_token)
        print(f"{GREEN}✓ Conectado exitosamente a: {BOLD}{plex.friendlyName}{RESET} (Versión {plex.version})\n")
        return plex
    except Unauthorized:
        print(f"{RED}❌ Error de autenticación: El Plex Token ingresado no es válido.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}❌ Error al conectar con Plex: {e}{RESET}")
        sys.exit(1)


def seleccionar_biblioteca(plex: PlexServer, biblioteca_nombre: Optional[str] = None):
    """Obtiene la sección de la biblioteca seleccionada o permite elegirla interactivamente."""
    secciones = plex.library.sections()
    if not secciones:
        print(f"{RED}❌ No se encontraron bibliotecas en el servidor Plex.{RESET}")
        sys.exit(1)

    if biblioteca_nombre:
        if biblioteca_nombre.lower() == "all":
            return secciones
        try:
            return [plex.library.section(biblioteca_nombre)]
        except NotFound:
            print(f"{RED}❌ No se encontró la biblioteca '{biblioteca_nombre}'.{RESET}")
            print(f"{YELLOW}Bibliotecas disponibles:{RESET} {[s.title for s in secciones]}")
            sys.exit(1)

    print(f"{BOLD}Bibliotecas disponibles:{RESET}")
    print(f"  [0] TODAS LAS BIBLIOTECAS")
    for idx, sec in enumerate(secciones, 1):
        print(f"  [{idx}] {sec.title} ({sec.type.capitalize()})")

    while True:
        try:
            opcion = input(f"\n{CYAN}Seleccione una biblioteca (0-{len(secciones)}): {RESET}").strip()
            num = int(opcion)
            if num == 0:
                return secciones
            elif 1 <= num <= len(secciones):
                return [secciones[num - 1]]
            else:
                print(f"{RED}Opción inválida. Intente de nuevo.{RESET}")
        except ValueError:
            print(f"{RED}Por favor ingrese un número válido.{RESET}")


def seleccionar_campos(campos_cli: Optional[List[str]] = None, todos_campos: bool = False) -> List[str]:
    """Determina los campos de metadatos a procesar."""
    if todos_campos:
        return PLEX_FIELDS

    if campos_cli:
        campos_invalidos = [f for f in campos_cli if f not in PLEX_FIELDS]
        if campos_invalidos:
            print(f"{YELLOW}⚠️ Advertencia: Los siguientes campos no son estándar en Plex y podrían ignorarse: {campos_invalidos}{RESET}")
        return campos_cli

    print(f"\n{BOLD}Selección de Campos a procesar:{RESET}")
    print(f"  [0] TODOS LOS CAMPOS METADATA ({len(PLEX_FIELDS)} campos)")
    for idx, f in enumerate(PLEX_FIELDS, 1):
        nombre_es = NOMBRES_CAMPOS_ES.get(f, f)
        print(f"  [{idx:2d}] {f:<22} ({nombre_es})")

    print(f"\n{YELLOW}Puede ingresar múltiples números separados por comas (ej: 1,2,5) o 0 para todos.{RESET}")
    while True:
        resp = input(f"{CYAN}Selección: {RESET}").strip()
        if resp == "0":
            return PLEX_FIELDS
        
        partes = [p.strip() for p in resp.split(",") if p.strip()]
        seleccionados = []
        valido = True
        for p in partes:
            if p.isdigit():
                idx = int(p)
                if 1 <= idx <= len(PLEX_FIELDS):
                    seleccionados.append(PLEX_FIELDS[idx - 1])
                else:
                    valido = False
                    break
            else:
                valido = False
                break
        
        if valido and seleccionados:
            return seleccionados
        print(f"{RED}Selección inválida. Ingrese números válidos del 1 al {len(PLEX_FIELDS)} separados por comas.{RESET}")


def ejecutar_bloqueo_masivo(
    plex: PlexServer,
    bibliotecas: list,
    campos: List[str],
    bloquear: bool,
    filtro_busqueda: Optional[str] = None,
    dry_run: bool = False
):
    """Ejecuta el proceso de bloqueo o desbloqueo masivo en Plex."""
    accion_str = "BLOQUEAR" if bloquear else "DESBLOQUEAR"
    color_accion = GREEN if bloquear else MAGENTA
    
    print("\n" + "="*60)
    print(f"{BOLD}RESUMEN DE OPERACIÓN{RESET}")
    print("="*60)
    print(f" Accion:               {color_accion}{BOLD}{accion_str}{RESET}")
    print(f" Modo Simulación:      {YELLOW}SÍ (Dry Run - No se modificarán datos){RESET}" if dry_run else f"{GREEN}NO (Se aplicarán cambios en Plex){RESET}")
    print(f" Bibliotecas:          {', '.join([b.title for b in bibliotecas])}")
    print(f" Campos seleccionados: {', '.join(campos)}")
    if filtro_busqueda:
        print(f" Filtro de búsqueda:   '{filtro_busqueda}'")
    print("="*60 + "\n")

    if not dry_run:
        confirm = input(f"{RED}{BOLD}¿Está seguro de continuar con esta operación masiva en Plex? (s/n): {RESET}").strip().lower()
        if confirm not in ['s', 'si', 'yes', 'y']:
            print(f"{YELLOW}Operación cancelada por el usuario.{RESET}")
            return

    for sec in bibliotecas:
        print(f"\n{CYAN}📂 Procesando Biblioteca: {BOLD}{sec.title}{RESET} ({sec.type})")
        
        # Caso 1: Si se procesa TODA la biblioteca sin filtro de búsqueda
        if not filtro_busqueda and len(campos) == len(PLEX_FIELDS) and not dry_run:
            # Si se desea desbloquear o bloquear todos los campos de toda la biblioteca,
            # usaremos los métodos nativos acelerados de LibrarySection si están disponibles.
            print(f"  ⚡ Aplicando cambio masivo de nivel de biblioteca...")
            for f in campos:
                try:
                    if bloquear:
                        sec.lockAllField(f)
                    else:
                        sec.unlockAllField(f)
                    print(f"   {GREEN}✓ Campo '{f}' {accion_str.lower()}do masivamente para toda la biblioteca.{RESET}")
                except Exception as e:
                    print(f"   {YELLOW}⚠️ No se pudo aplicar lockAllField para '{f}': {e}. Usando iteración individual...{RESET}")
                    _procesar_items_individuales(sec, sec.all(), campos, bloquear, dry_run, accion_str)
                    break
            continue

        # Caso 2: Iteración item por item (con filtro o campos específicos o dry-run)
        if filtro_busqueda:
            print(f"  🔍 Buscando ítems que coincidan con '{filtro_busqueda}'...")
            items = sec.search(title=filtro_busqueda)
        else:
            items = sec.all()

        if not items:
            print(f"  {YELLOW}No se encontraron ítems para procesar.{RESET}")
            continue

        _procesar_items_individuales(sec, items, campos, bloquear, dry_run, accion_str)


def _procesar_items_individuales(sec, items: list, campos: List[str], bloquear: bool, dry_run: bool, accion_str: str):
    """Procesa una lista de ítems de Plex uno a uno notificando progresos."""
    total_items = len(items)
    print(f"  📦 Procesando {total_items} ítems...")
    
    exitos = 0
    errores = 0

    val_lock = "1" if bloquear else "0"

    for item in tqdm(items, desc=f"  Progreso ({sec.title})", unit="item"):
        titulo_item = getattr(item, 'title', f"Item {item.ratingKey}")
        
        if dry_run:
            exitos += 1
            continue

        # Para modificar locks en Plex API sin alterar el valor actual:
        # Enviamos un edit batch con los parámetros de lock activados/desactivados
        edits = {f"{f}.locked": val_lock for f in campos}
        try:
            # Iniciar batch edits si la versión de plexapi lo permite
            if hasattr(item, '_edit'):
                item._edit(**edits)
                exitos += 1
            else:
                for f in campos:
                    if hasattr(item, 'editField'):
                        item.editField(f, locked=bloquear)
                exitos += 1
        except Exception as e:
            errores += 1
            # Imprimir error si falla
            tqdm.write(f"   {RED}❌ Error en '{titulo_item}': {e}{RESET}")

    if dry_run:
        print(f"  {GREEN}✓ [DRY RUN] Se habrían procesado {total_items} ítems en '{sec.title}'.{RESET}")
    else:
        print(f"  {GREEN}✓ Finalizado en '{sec.title}': {exitos} exitosos, {errores} errores.{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Script masivo para bloquear o desbloquear metadatos en Plex Media Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Desbloquear TODOS los campos de la biblioteca 'Películas'
  python plex_bulk_locker.py --action unlock --library "Películas" --all-fields

  # Bloquear solo los campos 'title' y 'summary' en la biblioteca 'Series'
  python plex_bulk_locker.py --action lock --library "Series" --fields title summary

  # Simular (Dry Run) desbloqueo de poster en películas que contienen 'Batman'
  python plex_bulk_locker.py --action unlock --library "Películas" --fields thumb poster --search "Batman" --dry-run
        """
    )
    
    parser.add_argument("--url", help="URL del servidor Plex (ej. http://127.0.0.1:32400)")
    parser.add_argument("--token", help="Plex Token (X-Plex-Token)")
    parser.add_argument("--action", choices=["lock", "unlock"], help="Acción a realizar: 'lock' (bloquear) o 'unlock' (desbloquear)")
    parser.add_argument("--library", help="Nombre de la biblioteca en Plex (o 'all' para todas)")
    parser.add_argument("--fields", nargs="+", help=f"Campos a modificar. Opciones válidas: {', '.join(PLEX_FIELDS[:8])}...")
    parser.add_argument("--all-fields", action="store_true", help="Selecciona todos los campos de metadatos disponibles")
    parser.add_argument("--search", help="Filtrar por título/nombre de ítem")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Modo simulación: muestra lo que cambiaría sin modificar Plex")

    args = parser.parse_args()

    print(f"{BOLD}{CYAN}===================================================={RESET}")
    print(f"{BOLD}{CYAN}   PLEX BULK METADATA LOCKER / UNLOCKER (ESPAÑOL)   {RESET}")
    print(f"{BOLD}{CYAN}===================================================={RESET}\n")

    # 1. Conexión a Plex
    plex = conectar_plex(url=args.url, token=args.token)

    # 2. Determinar Acción (Lock vs Unlock)
    bloquear = None
    if args.action:
        bloquear = (args.action == "lock")
    else:
        print(f"{BOLD}¿Qué acción desea realizar?{RESET}")
        print(f"  [1] {MAGENTA}DESBLOQUEAR campos (Permite que Plex actualice metadatos automáticamente){RESET}")
        print(f"  [2] {GREEN}BLOQUEAR campos (Evita que los agentes de Plex sobrescriban tus cambios){RESET}")
        while True:
            act_opt = input(f"\n{CYAN}Seleccione opción (1 o 2): {RESET}").strip()
            if act_opt == "1":
                bloquear = False
                break
            elif act_opt == "2":
                bloquear = True
                break
            print(f"{RED}Opción inválida. Ingrese 1 o 2.{RESET}")

    # 3. Selección de Biblioteca
    bibliotecas = seleccionar_biblioteca(plex, biblioteca_nombre=args.library)

    # 4. Selección de Campos
    campos = seleccionar_campos(campos_cli=args.fields, todos_campos=args.all_fields)

    # 5. Ejecución
    ejecutar_bloqueo_masivo(
        plex=plex,
        bibliotecas=bibliotecas,
        campos=campos,
        bloquear=bloquear,
        filtro_busqueda=args.search,
        dry_run=args.dry_run
    )

    print(f"\n{GREEN}{BOLD}✨ ¡Proceso completado con éxito!{RESET}\n")


if __name__ == "__main__":
    main()
