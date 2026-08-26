-- 1. CREACIÓN DE ESQUEMAS
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS datamart;

-- 2. TABLA STAGING: DESPACHOS Y COMPROBANTES CENARES
DROP TABLE IF EXISTS staging.stg_cenares;
CREATE TABLE staging.stg_cenares (
    disa_diresa                                     VARCHAR(255),
    codigo_destino                                  VARCHAR(50),
    punto_destino                                   VARCHAR(255),
    estrategias                                     VARCHAR(255),
    responsable                                     VARCHAR(255),
    anio_cd                                         VARCHAR(50),
    n_cd                                            VARCHAR(100),
    referencia_siga                                 TEXT,
    fec_creacion_cd                                 VARCHAR(50),
    referencia_cd                                   VARCHAR(255),
    fec_pedido                                      VARCHAR(50),
    anio_pecosa                                     VARCHAR(50),
    mes_pecosa                                      VARCHAR(50),
    fec_emision_pecosa                              VARCHAR(50),
    n_pecosa                                        VARCHAR(100),
    n_cargo_pecosa                                  VARCHAR(100),
    fecha_cargo_pecosa                              VARCHAR(50),
    fec_salida_de_pecosa_y_producto_del_almacen     VARCHAR(50),
    nombre_del_recepcionista                        VARCHAR(255),
    fec_de_conciliacion                             VARCHAR(50),
    fec_anulacion_de_pecosa                         VARCHAR(50),
    anulados                                        BOOLEAN,
    codigo_siga                                     VARCHAR(50),
    codigo_sismed                                   VARCHAR(50),
    producto                                        VARCHAR(255),
    lotes                                           VARCHAR(100),
    fec_vencimiento                                 VARCHAR(50),
    cantidades                                      INTEGER,
    precio_unitario                                 NUMERIC(14, 6),
    total                                           NUMERIC(16, 2)
);

-- Índices de staging para acelerar transformaciones en Kettle/Pentaho
CREATE INDEX IF NOT EXISTS idx_stg_cenares_pecosa ON staging.stg_cenares(n_pecosa);
CREATE INDEX IF NOT EXISTS idx_stg_cenares_codigo_dest ON staging.stg_cenares(codigo_destino);
CREATE INDEX IF NOT EXISTS idx_stg_cenares_siga ON staging.stg_cenares(codigo_siga);

-- 3. TABLA STAGING: MAESTRO RENIPRESS (ESTABLECIMIENTOS DE SALUD)
DROP TABLE IF EXISTS staging.stg_renipress;
CREATE TABLE staging.stg_renipress (
    cod_ue          VARCHAR(50),
    departamento    VARCHAR(100),
    provincia       VARCHAR(100),
    distrito        VARCHAR(100),
    latitud         VARCHAR(50),
    longitud        VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_stg_renipress_cod_ue ON staging.stg_renipress(cod_ue);