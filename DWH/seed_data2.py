
import io
import time
import random
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text

# ──────────────────────────────────────────────────────────────────────────────
# CONEXIONES (AWS RDS)
# ──────────────────────────────────────────────────────────────────────────────
URI_USUARIOS      = "postgresql://postgres:*******@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/UsersETL"
URI_CANCIONES     = "postgresql://postgres:*******@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/CancionETL"
URI_INTERACCIONES = "postgresql://postgres:*******@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/Interacciones"

engine_usr = create_engine(URI_USUARIOS)
engine_can = create_engine(URI_CANCIONES)
engine_int = create_engine(URI_INTERACCIONES)

def generar_segundo_millon_interacciones(n_total=1_000_000, lote_size=200_000):
    print(f"\n[Fase 2] Iniciando generación de {n_total:,} nuevas interacciones...")
    t0 = time.time()

    # 1. Leer catálogos existentes para asegurar integridad referencial
    with engine_usr.connect() as conn:
        ids_usuarios = pd.read_sql(text("SELECT id_usuario FROM usuario;"), con=conn)["id_usuario"].values
    with engine_can.connect() as conn:
        ids_canciones = pd.read_sql(text("SELECT id_cancion FROM cancion;"), con=conn)["id_cancion"].values
    with engine_int.connect() as conn:
        ids_fechas = pd.read_sql(text("SELECT id_fecha FROM fecha;"), con=conn)["id_fecha"].values
        ids_dispositivos = pd.read_sql(text("SELECT id_dispositivo FROM dispositivo;"), con=conn)["id_dispositivo"].values

    # Encontrar el último ID de interacción en la BD para continuar desde ahí
    with engine_int.connect() as conn:
        res = conn.execute(text("SELECT COALESCE(MAX(id_interaccion), 0) FROM interacciones;")).fetchone()
        id_inicial = res[0] + 1
    print(f"    -> El último ID en la BD es {res[0]}. Iniciaremos en id_interaccion = {id_inicial}")

    # 2. Conexión nativa con psycopg2 para carga masiva ultra rápida (Mismo Servidor)
    conn = psycopg2.connect(URI_INTERACCIONES)
    conn.autocommit = True
    cur = conn.cursor()

    total_insertado = 0
    lote_n = 1
    id_actual = id_inicial

    while total_insertado < n_total:
        t_lote = time.time()
        filas = []

        # Generar registros en memoria cambiados estadísticamente (Simula un comportamiento de fin de semana/nocturno)
        for _ in range(lote_size):
            # Modificamos variables para que sean "datos diferentes" (Ej: Más likes y más tiempo de escucha)
            tiempo_reproduccion = random.randint(45, 400)  # Canciones escuchadas por más tiempo
            dio_like = random.random() < 0.65             # Mayor tasa de likes (65% vs histórico anterior)
            dio_dislike = random.random() < 0.05          # Menor tasa de dislikes
            descargada = random.random() < 0.40           # 40% de descargas

            f = (
                id_actual,
                int(random.choice(ids_fechas)),
                int(random.choice(ids_dispositivos)),
                str(random.choice(ids_usuarios)),
                str(random.choice(ids_canciones)),
                tiempo_reproduccion,
                'true' if dio_like else 'false',
                'true' if dio_dislike else 'false',
                'true' if descargada else 'false'
            )
            filas.append(f)
            id_actual += 1

        # Volcar a buffer usando StringIO para emular un comando COPY (Bulk insert)
        f_buffer = io.StringIO()
        for r in filas:
            f_buffer.write("\t".join(map(str, r)) + "\n")
        f_buffer.seek(0)

        # Inserción atómica en AWS RDS
        cur.copy_from(f_buffer, 'interacciones', sep='\t', 
                      columns=('id_interaccion', 'id_fecha', 'id_dispositivo', 'id_usuario', 'id_cancion', 
                               'tiempo_reproduccion', 'dio_like', 'dio_dislike', 'descargada'))
        
        total_insertado += lote_size
        print(f"    [Lote #{lote_n}] {lote_size:,} filas insertadas en {time.time()-t_lote:.1f}s | Acumulado: {total_insertado:,}")
        lote_n += 1

    cur.close()
    conn.close()
    print(f"\n[OK] ¡Segundo millón inyectado con éxito en {(time.time()-t0)/60:.1f} minutos!")

if __name__ == "__main__":
    print("=" * 60)
    print(" INYECTOR INKREMENTAL - FASE 2 (1,000,000 NUEVAS FILAS)")
    print("=" * 60)
    
    generar_segundo_millon_interacciones(n_total=1_000_000, lote_size=250_000)