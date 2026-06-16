CREATE MATERIALIZED VIEW mart_eficiencia_modelo_ia AS
SELECT 
    ia.modelo_usado,
    COUNT(h.id_interaccion) AS total_generaciones,
    SUM(h.costo_token_ia) AS costo_total_tokens,
    AVG(h.calificacion) AS promedio_satisfaccion,
    -- KPI de eficiencia: Costo por punto de satisfacción
    SUM(h.costo_token_ia) / NULLIF(AVG(h.calificacion), 0) AS costo_eficiencia_score
FROM Hechos_Interacciones h
INNER JOIN dim_contexto_ia ia ON h.id_contexto = ia.id_contexto
GROUP BY ia.modelo_usado;

COMMENT ON MATERIALIZED VIEW mart_eficiencia_modelo_ia IS 
'Analítica de rentabilidad: Relación entre costo de tokens y satisfacción del usuario por modelo de IA.';




CREATE MATERIALIZED VIEW mart_engagement_social AS
SELECT 
    u.id_usuario,
    u.pais,
    COUNT(h.id_interaccion) AS total_actividad,
    COUNT(DISTINCT h.id_cancion) AS canciones_unicas_creadas,
    -- Categorización simple para segmentación
    CASE 
        WHEN COUNT(h.id_interaccion) > 50 THEN 'Power User'
        WHEN COUNT(h.id_interaccion) BETWEEN 10 AND 50 THEN 'Casual'
        ELSE 'Newbie'
    END AS segmento_usuario
FROM Hechos_Interacciones h
INNER JOIN dim_usuario u ON h.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.pais;

COMMENT ON MATERIALIZED VIEW mart_engagement_social IS 
'Segmentación de usuarios según volumen de interacción y canciones creadas.';


CREATE MATERIALIZED VIEW mart_tendencias_virales AS
SELECT 
    c.id_cancion,
    c.genero_musical,
    d.fecha AS fecha_creacion,
    COUNT(h.id_interaccion) AS total_escuchas,
    -- Crecimiento: Comparativa simple de actividad reciente
    SUM(CASE WHEN h.fecha_interaccion >= CURRENT_DATE - 7 THEN 1 ELSE 0 END) AS escuchas_ultimos_7_dias
FROM Hechos_Interacciones h
INNER JOIN dim_cancion c ON h.id_cancion = c.id_cancion
INNER JOIN dim_tiempo d ON h.id_tiempo = d.id_tiempo
GROUP BY c.id_cancion, c.genero_musical, d.fecha;

COMMENT ON MATERIALIZED VIEW mart_tendencias_virales IS 
'Análisis de tendencias: Identificación de canciones con alto crecimiento en los últimos 7 días.';