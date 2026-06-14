CREATE TABLE ubicacion (
    id_ubicacion SERIAL PRIMARY KEY,    -- ID autoincremental manejado por PostgreSQL
    continente VARCHAR(50) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    estado VARCHAR(100) NOT NULL
);

-- 2. Crear la tabla de hechos/usuarios vinculada a la ubicación
CREATE TABLE usuario (
    id_usuario VARCHAR(100) PRIMARY KEY, 
    nombre VARCHAR(150) NOT NULL,        
    edad INT NOT NULL,                   
    rango_edad VARCHAR(30) NOT NULL,    
    tipo_membresia VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL, 
    id_ubicacion INT NOT NULL,          
    
    -- Establecemos la relación de Integridad Referencial
    CONSTRAINT fk_usuario_ubicacion 
        FOREIGN KEY (id_ubicacion) 
        REFERENCES ubicacion(id_ubicacion)
        ON DELETE CASCADE
);