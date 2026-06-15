
-- Dimensión Geográfica (Jerárquica)
CREATE TABLE dim_ubicacion (
    id_ubicacion SERIAL,
    continente VARCHAR(50) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    estado VARCHAR(150) NOT NULL,
    
    CONSTRAINT pk_dim_ubicacion PRIMARY KEY (id_ubicacion)
);

-- Dimensión Temporal
CREATE TABLE dim_fecha_hora (
    id_fecha_hora SERIAL,
    fecha DATE NOT NULL,
    dia INT NOT NULL,
    mes INT NOT NULL,
    trimestre INT NOT NULL,
    anio INT NOT NULL,
    dia_semana VARCHAR(20) NOT NULL,
    
    CONSTRAINT pk_dim_fecha_hora PRIMARY KEY (id_fecha_hora)
);

-- Dimensión de Usuarios (Oyentes y Creadores)
CREATE TABLE dim_usuario (
    id_usuario VARCHAR(255), -- Conecta directamente con tu cognito_id analítico
    nombre VARCHAR(150) NOT NULL,
    edad INT NOT NULL,
    rango_edad VARCHAR(50) NOT NULL,
    tipo_membresia VARCHAR(50) NOT NULL,
    
    CONSTRAINT pk_dim_usuario PRIMARY KEY (id_usuario)
);

-- Dimensión Tecnológica
CREATE TABLE dim_dispositivo (
    id_dispositivo SERIAL,
    tipo_dispositivo VARCHAR(100) NOT NULL,
    sistema_operativo VARCHAR(100) NOT NULL,
    idioma_dispositivo VARCHAR(50) NOT NULL,
    
    CONSTRAINT pk_dim_dispositivo PRIMARY KEY (id_dispositivo)
);


-- Dimensión de Obras Musicales
CREATE TABLE dim_cancion (
    id_cancion SERIAL, 
    id_autor VARCHAR(255) NOT NULL, 
    duracion INT NOT NULL,
    idioma VARCHAR(10) NOT NULL,
    genero VARCHAR(100) NOT NULL,
    tema VARCHAR(100) NOT NULL,
    
    CONSTRAINT pk_dim_cancion PRIMARY KEY (id_cancion),
    CONSTRAINT fk_cancion_autor FOREIGN KEY (id_autor) 
        REFERENCES dim_usuario (id_usuario) ON DELETE RESTRICT
);


-- Centro A: Motor de Retención, Marketing e Interacciones
CREATE TABLE hechos_interacciones (
    id_interaccion SERIAL, -- Llave primaria propia de la transacción
    
    -- Claves Foráneas (Dimensionamiento)
    id_fecha_hora INT NOT NULL,
    id_usuario VARCHAR(255) NOT NULL, -- El oyente
    id_cancion INT NOT NULL,
    id_ubicacion INT NOT NULL,
    id_dispositivo INT NOT NULL,
    
    -- Métricas de Performance
    tiempo_reproduccion INT NOT NULL,
    -- Flags Binarios de Interacción (0 = No, 1 = Sí)
    dio_like SMALLINT NOT NULL DEFAULT 0,
    dio_dislike SMALLINT NOT NULL DEFAULT 0,
    descargada SMALLINT NOT NULL DEFAULT 0,
    
    -- Restricciones
    CONSTRAINT pk_hechos_interacciones PRIMARY KEY (id_interaccion),
    CONSTRAINT fk_interacciones_fecha FOREIGN KEY (id_fecha_hora) REFERENCES dim_fecha_hora(id_fecha_hora),
    CONSTRAINT fk_interacciones_usuario FOREIGN KEY (id_usuario) REFERENCES dim_usuario(id_usuario),
    CONSTRAINT fk_interacciones_cancion FOREIGN KEY (id_cancion) REFERENCES dim_cancion(id_cancion),
    CONSTRAINT fk_interacciones_ubicacion FOREIGN KEY (id_ubicacion) REFERENCES dim_ubicacion(id_ubicacion),
    CONSTRAINT fk_interacciones_dispositivo FOREIGN KEY (id_dispositivo) REFERENCES dim_dispositivo(id_dispositivo),
    
    -- Check constraints de seguridad para datos binarios
    CONSTRAINT chk_like CHECK (dio_like IN (0, 1)),
    CONSTRAINT chk_dislike CHECK (dio_dislike IN (0, 1)),
    CONSTRAINT chk_descargada CHECK (descargada IN (0, 1))
);

-- Centro B: Motor de Crecimiento, Altas y Retorno de Inversión (ROI)
CREATE TABLE hechos_adquisicion (
    id_adquisicion SERIAL,
    
    -- Claves Foráneas (Dimensionamiento)
    id_fecha_hora INT NOT NULL,
    id_usuario VARCHAR(255) NOT NULL, -- El nuevo usuario registrado
    id_ubicacion INT NOT NULL,
    id_dispositivo INT NOT NULL,
    
    -- Métricas Numéricas de Conteo Masivo
    usuario_registrado INT NOT NULL DEFAULT 1,
    
    -- Restricciones
    CONSTRAINT pk_hechos_adquisicion PRIMARY KEY (id_adquisicion),
    CONSTRAINT fk_adquisicion_fecha FOREIGN KEY (id_fecha_hora) REFERENCES dim_fecha_hora(id_fecha_hora),
    CONSTRAINT fk_adquisicion_usuario FOREIGN KEY (id_usuario) REFERENCES dim_usuario(id_usuario),
    CONSTRAINT fk_adquisicion_ubicacion FOREIGN KEY (id_ubicacion) REFERENCES dim_ubicacion(id_ubicacion),
    CONSTRAINT fk_adquisicion_dispositivo FOREIGN KEY (id_dispositivo) REFERENCES dim_dispositivo(id_dispositivo),
    
    CONSTRAINT chk_conteo_unitario CHECK (usuario_registrado = 1)
);


CREATE INDEX idx_hechos_inter_usuario ON hechos_interacciones(id_usuario);
CREATE INDEX idx_hechos_inter_cancion ON hechos_interacciones(id_cancion);
CREATE INDEX idx_hechos_inter_fecha ON hechos_interacciones(id_fecha_hora);

-- Índices para acelerar el análisis de adquisición de usuarios
CREATE INDEX idx_hechos_adquis_usuario ON hechos_adquisicion(id_usuario);
CREATE INDEX idx_hechos_adquis_ubicacion ON hechos_adquisicion(id_ubicacion);