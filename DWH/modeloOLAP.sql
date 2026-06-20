CREATE TABLE dim_ubicacion (
    id_ubicacion SERIAL,
    continente   VARCHAR(50)  NOT NULL,
    pais         VARCHAR(100) NOT NULL,
    estado       VARCHAR(150) NOT NULL,

    CONSTRAINT pk_dim_ubicacion  PRIMARY KEY (id_ubicacion),
    CONSTRAINT uq_dim_ubicacion  UNIQUE (continente, pais, estado)   -- ← NUEVO
);


CREATE TABLE dim_fecha_hora (
    id_fecha_hora SERIAL,
    fecha         DATE        NOT NULL,
    dia           INT         NOT NULL,
    mes           INT         NOT NULL,
    trimestre     INT         NOT NULL,
    anio          INT         NOT NULL,
    dia_semana    VARCHAR(20) NOT NULL,

    CONSTRAINT pk_dim_fecha_hora  PRIMARY KEY (id_fecha_hora),
    CONSTRAINT uq_dim_fecha_hora  UNIQUE (fecha)                     -- ← NUEVO
);


CREATE TABLE dim_usuario (
    id_usuario     VARCHAR(255),
    nombre         VARCHAR(150) NOT NULL,
    edad           INT          NOT NULL,
    rango_edad     VARCHAR(50)  NOT NULL,
    tipo_membresia VARCHAR(50)  NOT NULL,

    CONSTRAINT pk_dim_usuario PRIMARY KEY (id_usuario)
    -- La PK ya es UNIQUE; ON CONFLICT (id_usuario) DO NOTHING funciona sin cambios
);


CREATE TABLE dim_dispositivo (
    id_dispositivo    SERIAL,
    tipo_dispositivo  VARCHAR(100) NOT NULL,
    sistema_operativo VARCHAR(100) NOT NULL,
    idioma_dispositivo VARCHAR(50) NOT NULL,

    CONSTRAINT pk_dim_dispositivo  PRIMARY KEY (id_dispositivo),
    CONSTRAINT uq_dim_dispositivo  UNIQUE (tipo_dispositivo, sistema_operativo, idioma_dispositivo)  -- ← NUEVO
);


CREATE TABLE dim_cancion (
    id_cancion SERIAL,
    id_autor   VARCHAR(255) NOT NULL,
    duracion   INT          NOT NULL,
    idioma     VARCHAR(10)  NOT NULL,
    genero     VARCHAR(100) NOT NULL,
    tema       VARCHAR(100) NOT NULL,

    CONSTRAINT pk_dim_cancion    PRIMARY KEY (id_cancion),
    CONSTRAINT uq_dim_cancion    UNIQUE (id_autor, duracion, idioma, genero, tema),  -- ← NUEVO
    CONSTRAINT fk_cancion_autor  FOREIGN KEY (id_autor)
        REFERENCES dim_usuario (id_usuario) ON DELETE RESTRICT
);


CREATE TABLE dim_escenario (
    id_escenario     SERIAL PRIMARY KEY,
    nombre_escenario VARCHAR(100) NOT NULL,
    descripcion      TEXT,
    fecha_creacion   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);




CREATE TABLE hechos_interacciones (
    id_interaccion      SERIAL,

    id_fecha_hora       INT          NOT NULL,
    id_usuario          VARCHAR(255) NOT NULL,
    id_cancion          INT          NOT NULL,
    id_ubicacion        INT          NOT NULL,
    id_dispositivo      INT          NOT NULL,
    tiempo_reproduccion INT          NOT NULL,
    dio_like            SMALLINT     NOT NULL DEFAULT 0,
    dio_dislike         SMALLINT     NOT NULL DEFAULT 0,
    descargada          SMALLINT     NOT NULL DEFAULT 0,

    CONSTRAINT pk_hechos_interacciones       PRIMARY KEY (id_interaccion),
    CONSTRAINT fk_interacciones_fecha        FOREIGN KEY (id_fecha_hora)  REFERENCES dim_fecha_hora  (id_fecha_hora),
    CONSTRAINT fk_interacciones_usuario      FOREIGN KEY (id_usuario)     REFERENCES dim_usuario     (id_usuario),
    CONSTRAINT fk_interacciones_cancion      FOREIGN KEY (id_cancion)     REFERENCES dim_cancion     (id_cancion),
    CONSTRAINT fk_interacciones_ubicacion    FOREIGN KEY (id_ubicacion)   REFERENCES dim_ubicacion   (id_ubicacion),
    CONSTRAINT fk_interacciones_dispositivo  FOREIGN KEY (id_dispositivo) REFERENCES dim_dispositivo (id_dispositivo),

    CONSTRAINT chk_like       CHECK (dio_like    IN (0, 1)),
    CONSTRAINT chk_dislike    CHECK (dio_dislike IN (0, 1)),
    CONSTRAINT chk_descargada CHECK (descargada  IN (0, 1))
);


CREATE TABLE hechos_adquisicion (
    id_adquisicion SERIAL,

    id_fecha_hora  INT          NOT NULL,
    id_usuario     VARCHAR(255) NOT NULL,
    id_ubicacion   INT          NOT NULL,
    id_dispositivo INT          NOT NULL,

    usuario_registrado INT NOT NULL DEFAULT 1,

    CONSTRAINT pk_hechos_adquisicion         PRIMARY KEY (id_adquisicion),
    CONSTRAINT fk_adquisicion_fecha          FOREIGN KEY (id_fecha_hora)  REFERENCES dim_fecha_hora  (id_fecha_hora),
    CONSTRAINT fk_adquisicion_usuario        FOREIGN KEY (id_usuario)     REFERENCES dim_usuario     (id_usuario),
    CONSTRAINT fk_adquisicion_ubicacion      FOREIGN KEY (id_ubicacion)   REFERENCES dim_ubicacion   (id_ubicacion),
    CONSTRAINT fk_adquisicion_dispositivo    FOREIGN KEY (id_dispositivo) REFERENCES dim_dispositivo (id_dispositivo),

    CONSTRAINT chk_conteo_unitario CHECK (usuario_registrado = 1)
);


CREATE TABLE hechos_simulaciones (
    id_simulacion        SERIAL PRIMARY KEY,

    id_escenario         INT          NOT NULL,
    id_ubicacion         INT          NOT NULL,
    id_fecha_hora        INT          NOT NULL,
    id_usuario           VARCHAR(255) NOT NULL,
    id_dispositivo       INT          NOT NULL,
    kpi_proyectado_valor NUMERIC(15, 2) NOT NULL,
    metodo_proyeccion    VARCHAR(50),

    CONSTRAINT fk_sim_escenario  FOREIGN KEY (id_escenario)   REFERENCES dim_escenario   (id_escenario),
    CONSTRAINT fk_sim_ubicacion  FOREIGN KEY (id_ubicacion)   REFERENCES dim_ubicacion   (id_ubicacion),
    CONSTRAINT fk_sim_fecha      FOREIGN KEY (id_fecha_hora)  REFERENCES dim_fecha_hora  (id_fecha_hora),
    CONSTRAINT fk_sim_usuario    FOREIGN KEY (id_usuario)     REFERENCES dim_usuario     (id_usuario),
    CONSTRAINT fk_sim_dispositivo FOREIGN KEY (id_dispositivo) REFERENCES dim_dispositivo (id_dispositivo)
);


CREATE TABLE hechos_data_quality (
    id_log           SERIAL PRIMARY KEY,
    id_fecha_hora    INT          NOT NULL,
    entidad_afectada VARCHAR(100) NOT NULL,
    tipo_error       VARCHAR(100) NOT NULL,
    detalle_error    TEXT,
    severidad        INT CHECK (severidad BETWEEN 1 AND 5),

    CONSTRAINT fk_dq_fecha FOREIGN KEY (id_fecha_hora) REFERENCES dim_fecha_hora (id_fecha_hora)
);



CREATE INDEX idx_dq_fecha ON hechos_data_quality (id_fecha_hora);

CREATE INDEX idx_hechos_inter_usuario  ON hechos_interacciones (id_usuario);
CREATE INDEX idx_hechos_inter_cancion  ON hechos_interacciones (id_cancion);
CREATE INDEX idx_hechos_inter_fecha    ON hechos_interacciones (id_fecha_hora);

CREATE INDEX idx_hechos_adquis_usuario   ON hechos_adquisicion (id_usuario);
CREATE INDEX idx_hechos_adquis_ubicacion ON hechos_adquisicion (id_ubicacion);


