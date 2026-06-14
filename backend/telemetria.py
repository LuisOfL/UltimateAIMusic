import psycopg2
from pydantic import BaseModel
from datetime import datetime
from fastapi import HTTPException

# Parámetros oficiales de conexión a tu base de datos en AWS RDS
DB_PARAMS = {
    "host": "seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com",
    "database": "Interacciones",  # <── ASEGÚRATE QUE EN DBEAVER ESTÉS VIENDO ESTA BD Y NO LA LLAMADA 'postgres'
    "user": "postgres",
    "password": "Nomelase123+",
    "port": "5432"
}

class ContextoDispositivo(BaseModel):
    dispositivo: str
    sistema_operativo: str
    idioma: str
    tipo_conexion: str

class PayloadTelemetria(BaseModel):
    id_usuario: str
    id_cancion: str
    tipo_evento: str                   
    contexto_dispositivo: ContextoDispositivo
    segundos_escuchados: float = 0.0

def procesar_e_insertar_metrica(data: PayloadTelemetria):
    conn = None
    try:
        # Conectamos a la base de datos
        conn = psycopg2.connect(**DB_PARAMS)
        
        # ── CAMBIO CRÍTICO 1: Forzar escritura inmediata ──
        conn.autocommit = True 
        
        cursor = conn.cursor()
        ahora = datetime.utcnow()
        
        # 1. Dimensión Temporal (fecha)
        id_fecha = int(ahora.strftime("%Y%m%d%H%M%S"))
        cursor.execute("""
            INSERT INTO fecha (id_fecha, fecha, hora, dia, mes, anio)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_fecha) DO NOTHING;
        """, (id_fecha, ahora.date(), ahora.time(), ahora.day, ahora.month, ahora.year))

        # 2. Dimensión Física (dispositivo)
        id_dispositivo = int(datetime.utcnow().timestamp() * 1000) & 0x7FFFFFFF
        cursor.execute("""
            INSERT INTO dispositivo (id_dispositivo, tipo_dispositivo, sistema_operativo, idioma_dispositivo, tipo_conexion)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id_dispositivo) DO NOTHING;
        """, (
            id_dispositivo,
            data.contexto_dispositivo.dispositivo,
            data.contexto_dispositivo.sistema_operativo,
            data.contexto_dispositivo.idioma,
            data.contexto_dispositivo.tipo_conexion
        ))

        # 3. Mapeo de Flags Analíticos
        tiempo_reproduccion = int(data.segundos_escuchados)
        dio_like = True if data.tipo_evento == "like" else False
        dio_dislike = True if data.tipo_evento == "dislike" else False
        descargada = True if data.tipo_evento == "descarga" else False

        # 4. Inserción en Tabla de Hechos (interacciones)
        cursor.execute("""
            INSERT INTO interacciones (
                id_fecha, id_dispositivo, id_usuario, id_cancion, tipo_evento,
                tiempo_reproduccion, dio_like, descargada, dio_dislike
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            id_fecha,
            id_dispositivo,
            data.id_usuario,
            data.id_cancion,
            data.tipo_evento,
            tiempo_reproduccion,
            dio_like,
            descargada,
            dio_dislike
        ))

        # ── CAMBIO CRÍTICO 2: Asegurar el cierre y confirmación de la transacción ──
        cursor.close()
        
        print(f"✅ ¡Datos guardados físicamente en RDS para la canción: {data.id_cancion}!")
        return {"status": "success", "message": "Telemetría guardada y confirmada en AWS RDS"}

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ [ERROR REAL EN AWS RDS]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo de persistencia en RDS: {str(e)}")
    finally:
        if conn:
            conn.close()