CREATE MATERIALIZED VIEW dm_rendimiento_contenido AS
SELECT 
    f.anio,
    f.trimestre,
    f.mes,
    u.continente,
    u.pais,
    c.genero,
    c.idioma,
    c.id_cancion,
    COUNT(i.id_interaccion) AS total_reproducciones,
    SUM(i.tiempo_reproduccion) AS tiempo_total_segundos,
    SUM(i.dio_like) AS total_likes,
    SUM(i.dio_dislike) AS total_dislikes,
    SUM(i.descargada) AS total_descargas
FROM hechos_interacciones i
JOIN dim_fecha_hora f ON i.id_fecha_hora = f.id_fecha_hora
JOIN dim_ubicacion u  ON i.id_ubicacion = u.id_ubicacion
JOIN dim_cancion c    ON i.id_cancion = c.id_cancion
GROUP BY 
    f.anio, f.trimestre, f.mes, 
    u.continente, u.pais, 
    c.genero, c.idioma, c.id_cancion
WITH DATA;

CREATE UNIQUE INDEX idx_dm_contenido ON dm_rendimiento_contenido (anio, mes, id_cancion, pais);






CREATE MATERIALIZED VIEW dm_adquisicion_usuarios AS
SELECT 
    f.anio,
    f.mes,
    f.dia_semana,
    ub.continente,
    ub.pais,
    d.tipo_dispositivo,
    d.sistema_operativo,
    usr.tipo_membresia,
    usr.rango_edad,
    SUM(a.usuario_registrado) AS nuevos_usuarios_registrados
FROM hechos_adquisicion a
JOIN dim_fecha_hora f    ON a.id_fecha_hora = f.id_fecha_hora
JOIN dim_ubicacion ub    ON a.id_ubicacion = ub.id_ubicacion
JOIN dim_dispositivo d   ON a.id_dispositivo = d.id_dispositivo
JOIN dim_usuario usr     ON a.id_usuario = usr.id_usuario
GROUP BY 
    f.anio, f.mes, f.dia_semana,
    ub.continente, ub.pais, 
    d.tipo_dispositivo, d.sistema_operativo,
    usr.tipo_membresia, usr.rango_edad
WITH DATA;


CREATE UNIQUE INDEX idx_dm_adquisicion ON dm_adquisicion_usuarios (anio, mes, pais, tipo_membresia, rango_edad, tipo_dispositivo);





CREATE MATERIALIZED VIEW dm_simulaciones_estrategicas AS
SELECT 
    e.nombre_escenario,
    f.anio,
    f.trimestre,
    u.continente,
    u.pais,
    s.metodo_proyeccion,
    usr.tipo_membresia,
    COUNT(DISTINCT s.id_usuario) AS usuarios_simulados_impactados,
    SUM(s.kpi_proyectado_valor) AS valor_kpi_total_proyectado,
    AVG(s.kpi_proyectado_valor) AS promedio_kpi_proyectado
FROM hechos_simulaciones s
JOIN dim_escenario e  ON s.id_escenario = e.id_escenario
JOIN dim_fecha_hora f ON s.id_fecha_hora = f.id_fecha_hora
JOIN dim_ubicacion u  ON s.id_ubicacion = u.id_ubicacion
JOIN dim_usuario usr  ON s.id_usuario = usr.id_usuario
GROUP BY 
    e.nombre_escenario, 
    f.anio, f.trimestre, 
    u.continente, u.pais, 
    s.metodo_proyeccion, 
    usr.tipo_membresia
WITH DATA;

CREATE UNIQUE INDEX idx_dm_simulaciones ON dm_simulaciones_estrategicas (nombre_escenario, anio, trimestre, pais, tipo_membresia, metodo_proyeccion);



