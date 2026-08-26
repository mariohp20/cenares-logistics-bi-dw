-- CONSULTAS ANALÍTICAS Y MÉTRICAS DE NEGOCIO (DATAMART CENARES)

-- 1. KPI DE CUMPLIMIENTO Y LEAD TIME PROMEDIO POR DEPARTAMENTO
-- Mide el tiempo promedio entre la emisión de la PECOSA y la salida efectiva del almacén
SELECT 
    u.departamento,
    COUNT(f.id_hecho) AS total_despachos,
    ROUND(SUM(f.monto_total), 2) AS monto_total_distribuido,
    ROUND(AVG(t_salida.fecha - t_emision.fecha), 2) AS lead_time_promedio_dias,
    SUM(CASE WHEN f.anulado THEN 1 ELSE 0 END) AS total_pedidos_anulados
FROM datamart.fact_distribucion f
JOIN datamart.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
JOIN datamart.dim_tiempo t_emision ON f.id_fecha_emision_pecosa = t_emision.id_tiempo
JOIN datamart.dim_tiempo t_salida ON f.id_fecha_salida_almacen = t_salida.id_tiempo
WHERE f.anulado = FALSE
GROUP BY u.departamento
ORDER BY monto_total_distribuido DESC;


-- 2. TOP 10 PRODUCTOS Y MEDICAMENTOS MÁS DISTRIBUIDOS POR ESTRATEGIA
SELECT 
    e.estrategia,
    p.codigo_sismed,
    p.descripcion AS producto,
    SUM(f.cantidad_despachada) AS unidades_totales,
    ROUND(SUM(f.monto_total), 2) AS inversion_total
FROM datamart.fact_distribucion f
JOIN datamart.dim_producto p ON f.id_producto = p.id_producto
JOIN datamart.dim_estrategia e ON f.id_estrategia = e.id_estrategia
GROUP BY e.estrategia, p.codigo_sismed, p.descripcion
ORDER BY unidades_totales DESC
LIMIT 10;


-- 3. AUDITORÍA DE RIESGO OPERATIVO Y CADUCIDAD DE LOTES
-- Identifica despachos de alto riesgo predictivo o con vida útil crítica
SELECT 
    f.nro_pecosa,
    f.nro_lote,
    p.descripcion AS producto,
    u.punto_destino,
    f.dias_vida_util_lote_emision,
    f.riesgo_sal,
    CASE 
        WHEN f.riesgo_sal >= 0.70 THEN 'ALTO RIESGO'
        WHEN f.riesgo_sal >= 0.40 THEN 'RIESGO MEDIO'
        ELSE 'BAJO RIESGO'
    END AS categoria_riesgo_sla
FROM datamart.fact_distribucion f
JOIN datamart.dim_producto p ON f.id_producto = p.id_producto
JOIN datamart.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
WHERE f.riesgo_sal IS NOT NULL
ORDER BY f.riesgo_sal DESC
LIMIT 20;


-- 4. SIMULACIÓN / MONITOREO DE DESPACHOS PENDIENTES DE CONCILIACIÓN
SELECT 
    f.id_hecho,
    f.nro_pecosa,
    f.nro_cd,
    f.responsable_coordinacion,
    t_emision.fecha AS fecha_emision,
    f.monto_total
FROM datamart.fact_distribucion f
JOIN datamart.dim_tiempo t_emision ON f.id_fecha_emision_pecosa = t_emision.id_tiempo
WHERE f.id_fecha_conciliacion = -1
  AND f.anulado = FALSE
ORDER BY t_emision.fecha ASC;