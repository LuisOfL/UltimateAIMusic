"""
Ejecutar UNA SOLA VEZ para crear las tablas en AWS RDS PostgreSQL.
Comando: python crear_tablas_rds.py
"""
import psycopg2

DB_PARAMS = {
    "host": "seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com",
    "database": "Interacciones",
    "user": "postgres",
    "password": "Nomelase123+",
    "port": "5432"
}

SQL = """
DROP TABLE IF EXISTS interacciones;
DROP TABLE IF EXISTS fecha;
DROP TABLE IF EXISTS dispositivo;

CREATE TABLE fecha (
    id_fecha BIGINT PRIMARY KEY,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    dia INT NOT NULL,
    mes INT NOT NULL,
    anio INT NOT NULL
);

CREATE TABLE dispositivo (
    id_dispositivo BIGINT PRIMARY KEY,
    tipo_dispositivo VARCHAR(100),
    sistema_operativo VARCHAR(100),
    idioma_dispositivo VARCHAR(50),
    tipo_conexion VARCHAR(50)
);

CREATE TABLE interacciones (
    id_interaccion SERIAL PRIMARY KEY,
    id_fecha BIGINT,
    id_dispositivo BIGINT,
    id_usuario VARCHAR(255) NOT NULL,
    id_cancion VARCHAR(255) NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL,
    tiempo_reproduccion INT DEFAULT 0,
    dio_like BOOLEAN DEFAULT FALSE,
    descargada BOOLEAN DEFAULT FALSE,
    dio_dislike BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_interacciones_fecha FOREIGN KEY (id_fecha) REFERENCES fecha(id_fecha) ON DELETE CASCADE,
    CONSTRAINT fk_interacciones_dispositivo FOREIGN KEY (id_dispositivo) REFERENCES dispositivo(id_dispositivo) ON DELETE CASCADE
);
"""

def crear_tablas():
    conn = None
    try:
        print("Conectando a RDS...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        print("Ejecutando DDL...")
        cursor.execute(SQL)
        conn.commit()
        cursor.close()

        print(" Tablas creadas exitosamente:")
        print("   - fecha")
        print("   - dispositivo")
        print("   - interacciones")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f" Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    crear_tablas()