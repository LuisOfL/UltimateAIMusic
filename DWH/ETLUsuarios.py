from datetime import datetime
import os
import numpy as np
import pandas as pd
import pycountry
import pycountry_convert
from rapidfuzz import fuzz, process
from sqlalchemy import create_engine, text
import unicodedata

# =========================================================================
# 1. CONEXIONES A LAS BASES DE DATOS DE AWS RDS
# =========================================================================
ORIGEN_URI = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/Users"
DESTINO_URI = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/UsersETL"

engine_origen = create_engine(ORIGEN_URI)
engine_destino = create_engine(DESTINO_URI)


# =========================================================================
# 2. EXTRACCIÓN DE DATOS (E)
# =========================================================================
print("[Fase E] Extrayendo datos desde la base de datos origen...")
query = text(
    'SELECT cognito_id, email, username, birthdate, country, state, created_at FROM "usuarios";'
)

with engine_origen.connect() as conn:
    resultado = conn.execute(query)
    df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())


# =========================================================================
# 3. TRANSFORMACIÓN Y LIMPIEZA DE CAMPOS (T)
# =========================================================================
print("[Fase T] Limpiando campos de texto y formateando fechas...")
df["cognito_id"] = df["cognito_id"].str.lower().str.strip()
df["email"] = df["email"].str.lower().str.strip()
df["username"] = df["username"].str.lower().str.strip()
df["birthdate"] = df["birthdate"].str.lower().str.strip()
df["country"] = df["country"].str.lower().str.strip()
df["state"] = df["state"].str.lower().str.strip()

df["birthdate"] = pd.to_datetime(df["birthdate"])

# Cálculo de edad basado en el año actual (2026)
hoy = pd.Timestamp.now()
df["edad"] = (
    hoy.year
    - df["birthdate"].dt.year
    - (
        (hoy.month < df["birthdate"].dt.month)
        | ((hoy.month == df["birthdate"].dt.month) & (hoy.day < df["birthdate"].dt.day))
    )
)

df["rango_edad"] = pd.cut(
    df["edad"],
    bins=[0, 12, 17, 24, 34, 44, 54, 64, 120],
    labels=[
        "Niño",
        "Adolescente",
        "Joven",
        "Adulto Joven",
        "Adulto",
        "Adulto Maduro",
        "Adulto Mayor",
        "Tercera Edad",
    ],
    include_lowest=True,
)

df["membresia"] = np.random.choice(["normal", "premium"], size=len(df))


# =========================================================================
# 4. ENRIQUECIMIENTO GEOGRÁFICO (Fuzzy Matching)
# =========================================================================
def normalizar(texto):
    texto = str(texto).strip().lower()
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


paises = [c.name for c in pycountry.countries]
paises_norm = {normalizar(p): p for p in paises}


def corregir_pais(pais):
    pais_norm = normalizar(pais)
    match = process.extractOne(pais_norm, paises_norm.keys(), scorer=fuzz.WRatio)
    if match and match[1] >= 80:
        return paises_norm[match[0]]
    return pais


df["country"] = df["country"].apply(corregir_pais)

estados_por_iso = {}
for sub in pycountry.subdivisions:
    iso = sub.country_code
    estados_por_iso.setdefault(iso, []).append(sub.name)

estados_norm = {
    iso: {normalizar(e): e for e in estados} for iso, estados in estados_por_iso.items()
}


def corregir_estado(row):
    pais = row["country"]
    estado = row["state"]
    pais_obj = pycountry.countries.get(name=pais)

    if not pais_obj:
        return estado

    iso = pais_obj.alpha_2
    catalogo = estados_norm.get(iso)

    if not catalogo:
        return estado

    estado_norm = normalizar(estado)
    match = process.extractOne(estado_norm, catalogo.keys(), scorer=fuzz.WRatio)

    if match and match[1] >= 10:
        return catalogo[match[0]]

    return estado


df["state"] = df.apply(corregir_estado, axis=1)

continent_map = {
    "AF": "África",
    "AS": "Asia",
    "EU": "Europa",
    "NA": "América del Norte",
    "SA": "América del Sur",
    "OC": "Oceanía",
    "AN": "Antártida",
}


def obtener_continente(pais):
    if pd.isna(pais) or str(pais).strip() == "":
        return "Desconocido"
    try:
        country_matches = pycountry.countries.search_fuzzy(str(pais).strip())
        if not country_matches:
            return "Desconocido"
        country_obj = country_matches[0]
        continent_code = pycountry_convert.country_alpha2_to_continent_code(
            country_obj.alpha_2
        )
        return continent_map.get(continent_code, "Desconocido")
    except Exception:
        return "Desconocido"


df["continent"] = df["country"].apply(obtener_continente)


# =========================================================================
# 5. CARGA CONTROLADA A LA BASE DE DATOS DESTINO (L)
# =========================================================================
def cargar_datos_to_rds(df_origen):
    print("[Fase L] Iniciando proceso de carga masiva en AWS RDS...")

    # --- 5.1 TABLA: UBICACION ---
    df_ubicaciones_nuevas = df_origen[
        ["continent", "country", "state"]
    ].drop_duplicates()
    df_ubicaciones_nuevas = df_ubicaciones_nuevas.rename(
        columns={"continent": "continente", "country": "pais", "state": "estado"}
    )

    df_ubicaciones_nuevas["continente"] = (
        df_ubicaciones_nuevas["continente"].astype(str).str.strip()
    )
    df_ubicaciones_nuevas["pais"] = (
        df_ubicaciones_nuevas["pais"].astype(str).str.strip()
    )
    df_ubicaciones_nuevas["estado"] = (
        df_ubicaciones_nuevas["estado"].astype(str).str.strip()
    )

    print("-> Insertando dimensiones en la tabla 'ubicacion'...")
    df_ubicaciones_nuevas.to_sql(
        name="ubicacion",
        con=engine_destino,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    # --- 5.2 SINCRONIZACIÓN SEGURA DE IDS (CORREGIDO) ---
    print("-> Sincronizando llaves primarias autoincrementales...")
    query_select = text(
        'SELECT id_ubicacion, continente, pais, estado FROM "ubicacion";'
    )

    # Abrimos la conexión de forma explícita con un contexto válido para Pandas y SQLAlchemy 2.0
    with engine_destino.connect() as conn:
        df_ubicaciones_db = pd.read_sql(query_select, con=conn)

    # --- 5.3 TABLA: USUARIO ---
    df_mapeado = df_origen.rename(
        columns={"continent": "continente", "country": "pais", "state": "estado"}
    )
    df_usuarios_preparados = pd.merge(
        df_mapeado, df_ubicaciones_db, on=["continente", "pais", "estado"]
    )

    df_usuario_final = pd.DataFrame()
    df_usuario_final["id_usuario"] = (
        df_usuarios_preparados["cognito_id"].astype(str).str.strip()
    )
    df_usuario_final["nombre"] = (
        df_usuarios_preparados["username"].astype(str).str.strip()
    )
    df_usuario_final["edad"] = df_usuarios_preparados["edad"].astype("Int64")
    df_usuario_final["rango_edad"] = (
        df_usuarios_preparados["rango_edad"].astype(str).str.strip()
    )
    df_usuario_final["tipo_membresia"] = (
        df_usuarios_preparados["membresia"].astype(str).str.strip()
    )

    if "id_ubicacion" in df_usuarios_preparados.columns:
        df_usuario_final["id_ubicacion"] = df_usuarios_preparados[
            "id_ubicacion"
        ].astype(int)

    print(f"-> Insertando {len(df_usuario_final)} usuarios en la tabla destino...")
    df_usuario_final.to_sql(
        name="usuario",
        con=engine_destino,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print("[ETL FIN] ¡Proceso completado exitosamente sin errores!")


# =========================================================================
# 6. DISPARADOR DE LA OPERACIÓN
# =========================================================================
# Pasamos el dataframe limpio para ejecutar el pipeline final
cargar_datos_to_rds(df)