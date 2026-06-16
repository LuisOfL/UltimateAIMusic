

import io
import random
import time
import uuid
from datetime import date, timedelta

import numpy as np
import pandas as pd
import psycopg2
from faker import Faker
from sqlalchemy import create_engine, text

# ──────────────────────────────────────────────────────────────────────────────
# CONEXIONES
# ──────────────────────────────────────────────────────────────────────────────
URI_USUARIOS      = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/UsersETL"
URI_CANCIONES     = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/CancionETL"
URI_INTERACCIONES = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/Interacciones"

engine_usr = create_engine(URI_USUARIOS)
engine_can = create_engine(URI_CANCIONES)
engine_int = create_engine(URI_INTERACCIONES)

fake = Faker(['es_MX', 'es_ES', 'en_US', 'pt_BR'])
rng  = np.random.default_rng(42)

# ──────────────────────────────────────────────────────────────────────────────
# MOTOR DE INSERCIÓN RÁPIDA (COPY nativo)
# ──────────────────────────────────────────────────────────────────────────────
def bulk_insert(df: pd.DataFrame, tabla: str, uri: str, columns=None):
    cols = columns or list(df.columns)
    buf  = io.StringIO()
    df[cols].to_csv(buf, index=False, header=False, sep='\t', na_rep='\\N')
    buf.seek(0)
    conn   = psycopg2.connect(uri)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buf, tabla, sep='\t', columns=cols)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] {tabla}: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGOS COMPARTIDOS
# ──────────────────────────────────────────────────────────────────────────────
CONTINENTES = {
    "América del Norte": ["Mexico","United States","Canada"],
    "América del Sur"  : ["Brazil","Argentina","Colombia","Chile","Peru"],
    "Europa"           : ["Spain","Germany","France","Italy","United Kingdom"],
    "Asia"             : ["Japan","China","India","South Korea","Indonesia"],
    "África"           : ["Nigeria","South Africa","Kenya","Egypt","Ethiopia"],
    "Oceanía"          : ["Australia","New Zealand"],
}

ESTADOS_POR_PAIS = {
    "Mexico"        : ["Ciudad de México","Jalisco","Nuevo León","Puebla","Veracruz","Yucatán","Guanajuato","Chihuahua"],
    "United States" : ["California","Texas","New York","Florida","Illinois","Ohio","Georgia","Washington"],
    "Canada"        : ["Ontario","Quebec","British Columbia","Alberta","Manitoba"],
    "Brazil"        : ["São Paulo","Rio de Janeiro","Minas Gerais","Bahia","Paraná"],
    "Argentina"     : ["Buenos Aires","Córdoba","Santa Fe","Mendoza","Tucumán"],
    "Colombia"      : ["Bogotá","Antioquia","Valle del Cauca","Atlántico","Santander"],
    "Chile"         : ["Santiago","Valparaíso","Biobío","La Araucanía","Los Lagos"],
    "Peru"          : ["Lima","Arequipa","La Libertad","Cusco","Piura"],
    "Spain"         : ["Madrid","Cataluña","Andalucía","Valencia","Galicia"],
    "Germany"       : ["Bavaria","North Rhine-Westphalia","Baden-Württemberg","Hesse","Saxony"],
    "France"        : ["Île-de-France","Auvergne-Rhône-Alpes","Provence-Alpes-Côte d'Azur","Occitanie","Nouvelle-Aquitaine"],
    "Italy"         : ["Lombardy","Lazio","Campania","Sicily","Veneto"],
    "United Kingdom": ["England","Scotland","Wales","Northern Ireland"],
    "Japan"         : ["Tokyo","Osaka","Kanagawa","Aichi","Fukuoka"],
    "China"         : ["Guangdong","Shandong","Henan","Sichuan","Jiangsu"],
    "India"         : ["Maharashtra","Uttar Pradesh","Tamil Nadu","Karnataka","Gujarat"],
    "South Korea"   : ["Seoul","Gyeonggi","Busan","Incheon","Daegu"],
    "Indonesia"     : ["Java","Sumatra","Kalimantan","Sulawesi","Bali"],
    "Nigeria"       : ["Lagos","Kano","Oyo","Rivers","Kaduna"],
    "South Africa"  : ["Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape","Limpopo"],
    "Kenya"         : ["Nairobi","Mombasa","Kisumu","Nakuru","Eldoret"],
    "Egypt"         : ["Cairo","Alexandria","Giza","Shubra El-Kheima","Port Said"],
    "Ethiopia"      : ["Addis Ababa","Dire Dawa","Mekelle","Gondar","Hawassa"],
    "Australia"     : ["New South Wales","Victoria","Queensland","Western Australia","South Australia"],
    "New Zealand"   : ["Auckland","Wellington","Christchurch","Hamilton","Tauranga"],
}

GENEROS   = ["Pop","Rock","Reggaeton","Trap","Cumbia","Salsa","Jazz","Clásica","Electronic","Hip-Hop","R&B","Folk","Metal","Indie"]
TEMAS     = ["Amor","Desamor","Fiesta","Protesta","Nostalgia","Motivación","Naturaleza","Urbano","Fe","Amistad"]
IDIOMAS_C = ["es","en","pt","fr","de","ja","ko","it"]
MEMBRESIA = ["normal","premium"]
RANGOS    = ["Niño","Adolescente","Joven","Adulto Joven","Adulto","Adulto Maduro","Adulto Mayor","Tercera Edad"]
DISPOSITIVOS = [
    ("Smartphone","Android","es-MX"),("Smartphone","iOS","es-MX"),
    ("Smartphone","Android","en-US"),("Smartphone","iOS","en-US"),
    ("Tablet","Android","es-ES"),    ("Tablet","iOS","pt-BR"),
    ("Desktop","Windows","es-MX"),   ("Desktop","macOS","en-US"),
    ("Desktop","Linux","de-DE"),     ("SmartTV","Tizen","es-MX"),
    ("SmartTV","WebOS","en-US"),     ("SmartSpeaker","Amazon","en-US"),
    ("SmartSpeaker","Google","es-MX"),("Laptop","Windows","en-GB"),
    ("Laptop","macOS","fr-FR"),
]
CONEXIONES = ["WiFi","4G","5G","3G","Ethernet","LTE"]


def seed_usuarios(n_usuarios=100_000):
    print(f"\n[1/4] Generando {n_usuarios:,} usuarios + ubicaciones en UsersETL...")
    t0 = time.time()

    # Limpiar tablas en orden (FK: usuario → ubicacion)
    with engine_usr.begin() as conn:
        conn.execute(text("TRUNCATE TABLE usuario RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE ubicacion RESTART IDENTITY CASCADE;"))
    print("  Tablas limpiadas.")

    # --- Ubicaciones ---
    filas_ubi = []
    for continente, paises in CONTINENTES.items():
        for pais in paises:
            for estado in ESTADOS_POR_PAIS.get(pais, ["General"]):
                filas_ubi.append((continente, pais, estado))

    df_ubi = pd.DataFrame(filas_ubi, columns=["continente","pais","estado"]).drop_duplicates()
    df_ubi.to_sql("ubicacion", con=engine_usr, if_exists="append", index=False, method="multi")
    print(f"  ubicacion: {len(df_ubi)} filas insertadas.")

    # Leer IDs generados
    with engine_usr.connect() as conn:
        df_ubi_db = pd.read_sql(text("SELECT id_ubicacion, continente, pais, estado FROM ubicacion;"), con=conn)
    ids_ubi = df_ubi_db["id_ubicacion"].values

    # --- Usuarios ---
    BLOQUE = 10_000
    total_ins = 0
    buf_rows  = []

    for i in range(n_usuarios):
        id_ubi  = int(rng.choice(ids_ubi))
        edad    = int(rng.integers(13, 75))
        if   edad <= 12: rango = "Niño"
        elif edad <= 17: rango = "Adolescente"
        elif edad <= 24: rango = "Joven"
        elif edad <= 34: rango = "Adulto Joven"
        elif edad <= 44: rango = "Adulto"
        elif edad <= 54: rango = "Adulto Maduro"
        elif edad <= 64: rango = "Adulto Mayor"
        else:            rango = "Tercera Edad"

        created = fake.date_time_between(start_date="-5y", end_date="now")

        buf_rows.append((
            str(uuid.uuid4()),          
            fake.user_name()[:50],     
            edad,
            rango,
            random.choice(MEMBRESIA),   
            created.strftime("%Y-%m-%d %H:%M:%S"),  
            id_ubi,
        ))

        if len(buf_rows) >= BLOQUE:
            df_b = pd.DataFrame(buf_rows, columns=["id_usuario","nombre","edad","rango_edad","tipo_membresia","created_at","id_ubicacion"])
            bulk_insert(df_b, "usuario", URI_USUARIOS)
            total_ins += len(buf_rows)
            buf_rows   = []
            print(f"    {total_ins:,}/{n_usuarios:,} usuarios...", end="\r")

    if buf_rows:
        df_b = pd.DataFrame(buf_rows, columns=["id_usuario","nombre","edad","rango_edad","tipo_membresia","created_at","id_ubicacion"])
        bulk_insert(df_b, "usuario", URI_USUARIOS)
        total_ins += len(buf_rows)

    print(f"  usuario: {total_ins:,} filas insertadas en {time.time()-t0:.1f}s.")


def seed_canciones(n_canciones=50_000, ids_autores=None):
    print(f"\n[2/4] Generando {n_canciones:,} canciones en CancionETL...")
    t0 = time.time()

    with engine_can.begin() as conn:
        conn.execute(text("TRUNCATE TABLE cancion RESTART IDENTITY CASCADE;"))
    print("  Tabla limpiada.")

    BLOQUE = 5_000
    total  = 0
    buf    = []

    for _ in range(n_canciones):
        buf.append((
            int(rng.integers(60, 600)),         
            random.choice(IDIOMAS_C),
            random.choice(TEMAS),
            random.choice(GENEROS),
            str(rng.choice(ids_autores)),        
        ))
        if len(buf) >= BLOQUE:
            df_b = pd.DataFrame(buf, columns=["duracion","idioma","tema","genero","id_autor"])
            bulk_insert(df_b, "cancion", URI_CANCIONES)
            total += len(buf)
            buf    = []
            print(f"    {total:,}/{n_canciones:,} canciones...", end="\r")

    if buf:
        df_b = pd.DataFrame(buf, columns=["duracion","idioma","tema","genero","id_autor"])
        bulk_insert(df_b, "cancion", URI_CANCIONES)
        total += len(buf)

    print(f"  cancion: {total:,} filas insertadas en {time.time()-t0:.1f}s.")


def seed_fecha_dispositivo():
    print("\n[3/4] Generando fechas y dispositivos en Interacciones...")

    with engine_int.begin() as conn:
        conn.execute(text("TRUNCATE TABLE interacciones CASCADE;"))
        conn.execute(text("TRUNCATE TABLE fecha CASCADE;"))
        conn.execute(text("TRUNCATE TABLE dispositivo CASCADE;"))
    print("  Tablas limpiadas.")


    inicio = date(2022, 1, 1)
    fin    = date(2025, 6, 30)
    fechas = []
    d = inicio
    fid = 1
    while d <= fin:
        fechas.append((fid, d, "00:00:00", d.day, d.month, d.year))
        d  += timedelta(days=1)
        fid += 1

    df_f = pd.DataFrame(fechas, columns=["id_fecha","fecha","hora","dia","mes","anio"])
    bulk_insert(df_f, "fecha", URI_INTERACCIONES)
    print(f"  fecha: {len(df_f)} filas.")


    disp_rows = []
    for i, (tipo, so, idioma) in enumerate(DISPOSITIVOS, start=1):
        for conexion in CONEXIONES:
            disp_rows.append((i*10 + CONEXIONES.index(conexion), tipo, so, idioma, conexion))

    df_d = pd.DataFrame(disp_rows, columns=["id_dispositivo","tipo_dispositivo","sistema_operativo","idioma_dispositivo","tipo_conexion"])
    df_d = df_d.drop_duplicates(subset=["id_dispositivo"]).reset_index(drop=True)
    df_d["id_dispositivo"] = range(1, len(df_d)+1)
    bulk_insert(df_d, "dispositivo", URI_INTERACCIONES)
    print(f"  dispositivo: {len(df_d)} filas.")

    return df_f["id_fecha"].values, df_d["id_dispositivo"].values


def seed_interacciones(n_total=10_000_000, ids_usuarios=None, ids_canciones=None,
                       ids_fechas=None, ids_dispositivos=None):
    print(f"\n[4/4] Generando {n_total:,} interacciones...")
    t0     = time.time()
    BLOQUE = 500_000
    TIPOS  = ["play","pause","skip","complete","replay"]
    total  = 0

    while total < n_total:
        n = min(BLOQUE, n_total - total)

        df_b = pd.DataFrame({
            "id_fecha"           : rng.choice(ids_fechas,      size=n),
            "id_dispositivo"     : rng.choice(ids_dispositivos,size=n),
            "id_usuario"         : rng.choice(ids_usuarios,    size=n),
            "id_cancion"         : rng.choice(ids_canciones,   size=n).astype(str),
            "tipo_evento"        : rng.choice(TIPOS,            size=n),
            "tiempo_reproduccion": rng.integers(0, 600,         size=n),
            "dio_like"           : rng.integers(0, 2,           size=n).astype(bool),
            "descargada"         : rng.integers(0, 2,           size=n).astype(bool),
            "dio_dislike"        : rng.integers(0, 2,           size=n).astype(bool),
        })

        bulk_insert(df_b, "interacciones", URI_INTERACCIONES,
                    columns=["id_fecha","id_dispositivo","id_usuario","id_cancion",
                             "tipo_evento","tiempo_reproduccion","dio_like","descargada","dio_dislike"])

        total += n
        vel    = total / (time.time() - t0)
        print(f"    {total:,}/{n_total:,} ({vel:,.0f} filas/s)...", end="\r")

    print(f"\n  interacciones: {total:,} filas en {(time.time()-t0)/60:.1f} min.")

# ──────────────────────────────────────────────────────────────────────────────
# ORQUESTADOR
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    T0 = time.time()
    print("=" * 60)
    print(" SEED DATA — GENERACIÓN DE 10M DE INTERACCIONES")
    print("=" * 60)


    seed_usuarios(n_usuarios=100_000)


    with engine_usr.connect() as conn:
        ids_usuarios = pd.read_sql(text("SELECT id_usuario FROM usuario;"), con=conn)["id_usuario"].values


    seed_canciones(n_canciones=50_000, ids_autores=ids_usuarios)

    with engine_can.connect() as conn:
        ids_canciones = pd.read_sql(text("SELECT id_cancion FROM cancion;"), con=conn)["id_cancion"].values

 
    ids_fechas, ids_dispositivos = seed_fecha_dispositivo()

  
    seed_interacciones(
        n_total=6_000_000,
        ids_usuarios=ids_usuarios,
        ids_canciones=ids_canciones,
        ids_fechas=ids_fechas,
        ids_dispositivos=ids_dispositivos,
    )

    print(f"\n{'='*60}")
    print(f" SEED COMPLETADO EN {(time.time()-T0)/60:.1f} MINUTOS")
    print(f"{'='*60}")
    print("\nAhora ejecuta etl_constellation.py para poblar el cubo OLAP.")