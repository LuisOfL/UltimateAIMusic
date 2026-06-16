CREATE TABLE ubicacion (
    id_ubicacion SERIAL PRIMARY KEY,    
    continente VARCHAR(50) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    estado VARCHAR(100) NOT NULL
);


CREATE TABLE usuario (
    id_usuario VARCHAR(100) PRIMARY KEY, 
    nombre VARCHAR(150) NOT NULL,        
    edad INT NOT NULL,                   
    rango_edad VARCHAR(30) NOT NULL,    
    tipo_membresia VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL, 
    id_ubicacion INT NOT NULL,          

    CONSTRAINT fk_usuario_ubicacion 
        FOREIGN KEY (id_ubicacion) 
        REFERENCES ubicacion(id_ubicacion)
        ON DELETE CASCADE
);

CREATE INDEX idx_usuario_nombre
ON usuario(nombre);