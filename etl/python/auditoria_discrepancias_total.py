import logging
from pathlib import Path
import pandas as pd

# Configuración de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# 1. Configuración de rutas relativas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUTA_PROCESADO = BASE_DIR / "data" / "processed" / "CENARES_2024_FINAL.csv"
RUTA_REPORTE = BASE_DIR / "data" / "historic" / "DISCREPANCIAS_TOTAL_2024.csv"


# 2. Pipeline de auditoría de consistencia de precios y montos
def auditar_discrepancias(umbral_soles: float = 1.0):
    if not RUTA_PROCESADO.exists():
        logging.error(f"No se encontró el dataset procesado en: {RUTA_PROCESADO}")
        return

    logging.info("Iniciando auditoría de calidad de datos en CENARES_2024_FINAL.csv...")
    df = pd.read_csv(RUTA_PROCESADO, sep=';', dtype=str)

    # Conversión segura a tipos numéricos
    cantidades = pd.to_numeric(df.get('CANTIDADES', df.get('cantidades')), errors='coerce').fillna(0)
    precios = pd.to_numeric(df.get('PRECIO_UNITARIO', df.get('precio_unitario')), errors='coerce').fillna(0)
    totales = pd.to_numeric(df.get('TOTAL', df.get('total')), errors='coerce').fillna(0)

    total_calculado = (cantidades * precios).round(2)
    diferencia = (totales - total_calculado).round(2)

    df['TOTAL_CALCULADO'] = total_calculado
    df['DIFERENCIA'] = diferencia

    # Filtrar discrepancias por encima del umbral de tolerancia
    discrepancias = df[diferencia.abs() > umbral_soles].copy()

    total_filas = len(df)
    total_discrepancias = len(discrepancias)
    pct_discrepancias = (total_discrepancias / total_filas * 100) if total_filas > 0 else 0

    logging.info(f"Total registros analizados: {total_filas:,}")
    logging.info(f"Registros con diferencia > S/. {umbral_soles:.2f}: {total_discrepancias:,} ({pct_discrepancias:.2f}%)")

    if not discrepancias.empty:
        max_dif = diferencia.abs().max()
        avg_dif = discrepancias['DIFERENCIA'].abs().mean()
        logging.info(f"Diferencia máxima: S/. {max_dif:,.2f} | Diferencia promedio: S/. {avg_dif:,.2f}")

        # Exportar reporte a la carpeta de histórico
        RUTA_REPORTE.parent.mkdir(parents=True, exist_ok=True)
        discrepancias.to_csv(RUTA_REPORTE, sep=';', index=False, encoding='utf-8-sig')
        logging.info(f"Reporte de auditoría generado en: {RUTA_REPORTE}")
    else:
        logging.info("No se encontraron discrepancias financieras significativas.")


if __name__ == "__main__":
    auditar_discrepancias()