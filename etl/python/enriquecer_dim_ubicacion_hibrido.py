import logging
import os
import re
import urllib.parse
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configuración de logging limpio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# 1. Configuración de conexión y rutas relativas
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

RUTA_CSV_RENIPRESS = BASE_DIR / "data" / "processed" / "RENIPRESS_LIMPIO.csv"

# Conexión con SQLAlchemy
pass_encoded = urllib.parse.quote_plus(DB_PASS)
conn_str = f"postgresql://{DB_USER}:{pass_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(conn_str)


# 2. Funciones de normalización para coincidencia difusa / semántica
def normalizar_nombre(nombre: str) -> str:
    """Remueve tildes, caracteres especiales y palabras de ruido institucional."""
    if not isinstance(nombre, str):
        return ""
    nombre = nombre.lower()
    
    # Reemplazo de caracteres especiales
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n'}
    for k, v in reemplazos.items():
        nombre = nombre.replace(k, v)
    
    # Eliminación de palabras de ruido
    ruido = [
        "hospital", "nacional", "essalud", "puesto de salud", "centro de salud",
        "p.s.", "c.s.", "red de salud", "clinica", "instituto", "de", "del", "la", "el", "y"
    ]
    for palabra in ruido:
        nombre = re.sub(rf'\b{palabra}\b', '', nombre)
        
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    return " ".join(nombre.split())


# 3. Pipeline de enriquecimiento de la dimensión
def enriquecer_dim_ubicacion():
    if not RUTA_CSV_RENIPRESS.exists():
        logging.error(f"No se encontró el archivo maestro: {RUTA_CSV_RENIPRESS}")
        return

    logging.info("Cargando maestro RENIPRESS y registros de Dim_Ubicacion...")
    df_renipress = pd.read_csv(RUTA_CSV_RENIPRESS, sep=';', encoding='utf-8-sig', dtype=str)
    df_renipress['norm_nombre'] = df_renipress['NOMBRE'].apply(normalizar_nombre)

    with engine.connect() as conn:
        df_db = pd.read_sql(
            "SELECT id_ubicacion, codigo_destino, punto_destino FROM datamart.dim_ubicacion WHERE id_ubicacion > 0",
            conn
        )

    actualizaciones = []
    metricas = {"codigo": 0, "nombre": 0, "externo": 0}

    # Búsqueda híbrida: Capa 1 (Código UE) -> Capa 2 (Nombre Semántico)
    for _, row in df_db.iterrows():
        id_ub = int(row['id_ubicacion'])
        cod_dest = row['codigo_destino']
        norm_p_dest = normalizar_nombre(row['punto_destino'])

        # Capa 1: Coincidencia exacta por código
        match = df_renipress[df_renipress['COD_UE'] == cod_dest]
        tipo_match = "codigo"

        # Capa 2: Coincidencia por nombre si falla el código
        if match.empty and norm_p_dest:
            match = df_renipress[df_renipress['norm_nombre'] == norm_p_dest]
            tipo_match = "nombre"

            if match.empty:
                tokens = [w for w in norm_p_dest.split() if len(w) > 3]
                if tokens:
                    condicion = pd.Series(True, index=df_renipress.index)
                    for t in tokens:
                        condicion &= df_renipress['norm_nombre'].str.contains(t, na=False)
                    match = df_renipress[condicion]

        if not match.empty:
            item = match.iloc[0]
            lat = pd.to_numeric(str(item.get('NORTE', '')).replace(',', '.'), errors='coerce')
            lon = pd.to_numeric(str(item.get('ESTE', '')).replace(',', '.'), errors='coerce')

            actualizaciones.append({
                "id_ubicacion": id_ub,
                "departamento": str(item.get('DEPARTAMENTO', '')).upper().strip(),
                "provincia": str(item.get('PROVINCIA', '')).upper().strip(),
                "distrito": str(item.get('DISTRITO', '')).upper().strip(),
                "latitud": float(lat) if pd.notna(lat) else None,
                "longitud": float(lon) if pd.notna(lon) else None
            })
            metricas[tipo_match] += 1
        else:
            actualizaciones.append({
                "id_ubicacion": id_ub,
                "departamento": "INSTITUCIÓN EXTERNA / NO APLICA",
                "provincia": "LABORATORIO PRIVADO / PROVEEDOR",
                "distrito": "LABORATORIO PRIVADO / PROVEEDOR",
                "latitud": None,
                "longitud": None
            })
            metricas["externo"] += 1

    # Actualización en bloque dentro de una sola transacción
    sql_update = text("""
        UPDATE datamart.dim_ubicacion
        SET departamento = :departamento,
            provincia = :provincia,
            distrito = :distrito,
            latitud = :latitud,
            longitud = :longitud
        WHERE id_ubicacion = :id_ubicacion;
    """)

    logging.info(f"Actualizando {len(actualizaciones)} registros en datamart.dim_ubicacion...")
    with engine.begin() as conn:
        conn.execute(sql_update, actualizaciones)

    logging.info(f"Enriquecimiento finalizado. Métricas: {metricas}")


if __name__ == "__main__":
    enriquecer_dim_ubicacion()