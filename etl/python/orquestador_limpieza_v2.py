import csv
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

# Configuración de logging limpio y profesional
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# 1. Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Raíz del repositorio
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_HISTORIC = BASE_DIR / "data" / "historic"

# Crear directorios si no existen
for path in [DATA_RAW, DATA_PROCESSED, DATA_HISTORIC]:
    path.mkdir(parents=True, exist_ok=True)


# 2. Funciones auxiliares de limpieza y normalización
def sanitizar_texto(valor):
    """Elimina saltos de línea y espacios residuales."""
    if isinstance(valor, str):
        return valor.replace('\n', ' ').replace('\r', ' ').strip()
    return valor


def limpiar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza celdas y descarta registros vacíos."""
    # Compatibilidad con pandas moderno (.map) y legacy (.applymap)
    df_clean = df.map(sanitizar_texto) if hasattr(df, "map") else df.applymap(sanitizar_texto)
    
    # Eliminar filas totalmente nulas o con strings vacíos
    df_clean = df_clean.dropna(how='all')
    filtro_validos = df_clean.astype(str).apply(lambda row: any(row.str.strip() != ''), axis=1)
    return df_clean[filtro_validos]


def procesar_csv(origen: Path, destino: Path, on_bad_lines: str = 'skip'):
    """Lee con fallback de codificación, limpia y exporta a UTF-8 BOM."""
    df = None
    for encoding in ['cp1252', 'latin1', 'utf-8']:
        try:
            df = pd.read_csv(origen, sep=';', encoding=encoding, dtype=str, on_bad_lines=on_bad_lines)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError(f"Codificación no compatible para el archivo: {origen.name}")

    df_procesado = limpiar_dataframe(df)
    df_procesado.to_csv(
        destino,
        sep=';',
        index=False,
        encoding='utf-8-sig',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL
    )


# 3. Pipeline de ejecución
def ejecutar_pipeline():
    archivos_crudos = list(DATA_RAW.glob("*.csv"))
    
    if not archivos_crudos:
        logging.info("No hay archivos CSV pendientes en 'data/raw'.")
        return

    for archivo in archivos_crudos:
        nombre_lower = archivo.name.lower()
        destino_procesado = DATA_PROCESSED / f"CLEAN_{archivo.name}"
        destino_historico = DATA_HISTORIC / f"{datetime.now().strftime('%Y%m%d')}_{archivo.name}"

        try:
            logging.info(f"Procesando: {archivo.name}")
            
            # Tolerancia a líneas corruptas según tipo de dataset
            bad_lines_mode = 'skip' if any(k in nombre_lower for k in ["cd1", "cenares", "dataset"]) else 'error'
            procesar_csv(archivo, destino_procesado, on_bad_lines=bad_lines_mode)
            
            # Archivar archivo crudo procesado en histórico
            archivo.rename(destino_historico)
            logging.info(f"Completado: Guardado en 'data/processed' y archivado en 'data/historic'.")

        except Exception as e:
            logging.error(f"Fallo al procesar {archivo.name}: {e}")


if __name__ == "__main__":
    ejecutar_pipeline()