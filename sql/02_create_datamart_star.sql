-- ESQUEMA DATAMART CENARES (MODELO ESTRELLA OFICIAL)

CREATE SCHEMA IF NOT EXISTS datamart;

-- 1. DIMENSIÓN TIEMPO
CREATE TABLE IF NOT EXISTS datamart.dim_tiempo (
    id_tiempo       INTEGER PRIMARY KEY, -- Formato YYYYMMDD (Ej: 20241230)
    fecha           DATE NOT NULL,
    anio            INTEGER NOT NULL,
    mes_num         INTEGER NOT NULL,
    mes_nombre      VARCHAR(20) NOT NULL,
    trimestre       INTEGER NOT NULL,
    dia_semana      VARCHAR(20) NOT NULL
);

-- 2. DIMENSIÓN UBICACIÓN
CREATE TABLE IF NOT EXISTS datamart.dim_ubicacion (
    id_ubicacion    SERIAL PRIMARY KEY,
    codigo_destino  VARCHAR(50),
    disa_diresa     VARCHAR(255),
    punto_destino   VARCHAR(255),
    departamento    VARCHAR(100),
    provincia       VARCHAR(100),
    distrito        VARCHAR(100),
    latitud         NUMERIC(12, 8),
    longitud        NUMERIC(12, 8)
);

-- 3. DIMENSIÓN PRODUCTO
CREATE TABLE IF NOT EXISTS datamart.dim_producto (
    id_producto     SERIAL PRIMARY KEY,
    codigo_siga     VARCHAR(50),
    codigo_sismed   VARCHAR(50),
    descripcion     VARCHAR(255)
);

-- 4. DIMENSIÓN ESTRATEGIA
CREATE TABLE IF NOT EXISTS datamart.dim_estrategia (
    id_estrategia   SERIAL PRIMARY KEY,
    estrategia      VARCHAR(150),
    meta            VARCHAR(50)
);

-- 5. TABLA DE HECHOS: DISTRIBUCIÓN
CREATE TABLE IF NOT EXISTS datamart.fact_distribucion (
    id_hecho                        SERIAL PRIMARY KEY,
    id_producto                     INTEGER REFERENCES datamart.dim_producto(id_producto),
    id_ubicacion                    INTEGER REFERENCES datamart.dim_ubicacion(id_ubicacion),
    id_estrategia                   INTEGER REFERENCES datamart.dim_estrategia(id_estrategia),
    id_fecha_pedido                 INTEGER REFERENCES datamart.dim_tiempo(id_tiempo),
    id_fecha_emision_pecosa         INTEGER REFERENCES datamart.dim_tiempo(id_tiempo),
    id_fecha_cargo_pecosa           INTEGER REFERENCES datamart.dim_tiempo(id_tiempo),
    id_fecha_salida_almacen         INTEGER REFERENCES datamart.dim_tiempo(id_tiempo),
    id_fecha_vencimiento            INTEGER REFERENCES datamart.dim_tiempo(id_tiempo),
    id_fecha_conciliacion           INTEGER,
    id_fecha_anulacion              INTEGER,
    nro_pecosa                      VARCHAR(100),
    nro_cd                          VARCHAR(100),
    nro_cargo_pecosa                VARCHAR(100),
    nro_lote                        VARCHAR(100),
    responsable_coordinacion        VARCHAR(255),
    nombre_recepcionista_sistema    VARCHAR(255),
    anulado                         BOOLEAN DEFAULT FALSE,
    cantidad_despachada             INTEGER,
    precio_unitario                 NUMERIC(12, 6),
    monto_total                     NUMERIC(14, 2),
    dias_vida_util_lote_emision     INTEGER,
    riesgo_sal                      NUMERIC(5, 2) -- Salida del modelo predictivo (Score 0.00 a 1.00 o %)
);

-- Índices de aceleración analítica
CREATE INDEX IF NOT EXISTS idx_fact_dist_prod ON datamart.fact_distribucion(id_producto);
CREATE INDEX IF NOT EXISTS idx_fact_dist_ubic ON datamart.fact_distribucion(id_ubicacion);
CREATE INDEX IF NOT EXISTS idx_fact_dist_fecha_emision ON datamart.fact_distribucion(id_fecha_emision_pecosa);