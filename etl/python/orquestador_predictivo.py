import logging
import os
import urllib.parse
from pathlib import Path
import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# 1. Configuración de entorno y rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cenares_dw")

MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "modelo_riesgo_cenares_final.pkl"
ENCODER_PATH = MODELS_DIR / "diccionarios_encoding_cenares.pkl"

if not MODEL_PATH.exists() or not ENCODER_PATH.exists():
    raise FileNotFoundError("No se encontraron los artefactos .pkl en 'models/'.")

pass_encoded = urllib.parse.quote_plus(DB_PASS)
conn_str = f"postgresql://{DB_USER}:{pass_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(conn_str)


# 2. Inferencia y actualización sobre datamart.fact_distribucion
def ejecutar_inferencia_riesgo():
    logging.info("Cargando modelo y codificadores categóricos...")
    modelo = joblib.load(MODEL_PATH)
    diccionarios = joblib.load(ENCODER_PATH)

    # Consulta directa a fact_distribucion
    query_pendientes = """
    SELECT
        f.id_hecho,
        f.cantidad_despachada,
        f.dias_vida_util_lote_emision,
        f.monto_total,
        u.departamento,
        u.provincia,
        e.estrategia
    FROM datamart.fact_distribucion f
    JOIN datamart.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
    JOIN datamart.dim_estrategia e ON f.id_estrategia = e.id_estrategia
    WHERE f.riesgo_sal IS NULL;
    """

    with engine.connect() as conn:
        df_pendientes = pd.read_sql(query_pendientes, conn)

    if df_pendientes.empty:
        logging.info("No existen registros pendientes de cálculo de riesgo_sal.")
        return

    logging.info(f"Evaluando {len(df_pendientes)} despachos pendientes...")

    # Preparación de features
    X_predict = pd.DataFrame()
    for col in ['departamento', 'provincia', 'estrategia']:
        if col in diccionarios:
            X_predict[f'tasa_riesgo_{col}'] = df_pendientes[col].map(diccionarios[col]).fillna(0.5)

    X_predict['cantidad_despachada'] = pd.to_numeric(df_pendientes['cantidad_despachada'], errors='coerce').fillna(0)
    X_predict['monto_total'] = pd.to_numeric(df_pendientes['monto_total'], errors='coerce').fillna(0)

    # Inferencia (probabilidad o score)
    try:
        predicciones = modelo.predict_proba(X_predict.values)[:, 1]
    except AttributeError:
        predicciones = modelo.predict(X_predict.values)

    actualizaciones = [
        {"id_hecho": int(id_h), "riesgo_sal": float(round(p, 2))}
        for id_h, p in zip(df_pendientes['id_hecho'], predicciones)
    ]

    sql_update = text("""
        UPDATE datamart.fact_distribucion
        SET riesgo_sal = :riesgo_sal
        WHERE id_hecho = :id_hecho;
    """)

    logging.info("Actualizando datamart.fact_distribucion con riesgo_sal...")
    with engine.begin() as conn:
        conn.execute(sql_update, actualizaciones)

    logging.info("Proceso predictivo completado.")


if __name__ == "__main__":
    ejecutar_inferencia_riesgo()