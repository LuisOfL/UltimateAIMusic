from datetime import datetime
import numpy as np
import pandas as pd
import pycountry
import pycountry_convert
from rapidfuzz import fuzz, process
from sqlalchemy import create_engine, text
import unicodedata


ORIGEN_URI  = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/Users"
DESTINO_URI = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/UsersETL"

engine_origen  = create_engine(ORIGEN_URI)
engine_destino = create_engine(DESTINO_URI)


print("[Fase E] Extrayendo datos desde la base de datos origen...")
query = text(
    'SELECT cognito_id, email, username, birthdate, country, state, created_at '
    'FROM "usuarios";'
)
with engine_origen.connect() as conn:
    resultado = conn.execute(query)
    df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())


print("[Fase T] Limpiando campos y formateando fechas...")
df["cognito_id"] = df["cognito_id"].str.lower().str.strip()
df["email"]      = df["email"].str.lower().str.strip()
df["username"]   = df["username"].str.lower().str.strip()
df["birthdate"]  = df["birthdate"].str.lower().str.strip()
df["country"]    = df["country"].str.lower().str.strip()
df["state"]      = df["state"].str.lower().str.strip()

df["birthdate"]  = pd.to_datetime(df["birthdate"])


df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["created_at"] = df["created_at"].fillna(pd.Timestamp.now())

# Edad
hoy = pd.Timestamp.now()
df["edad"] = (
    hoy.year - df["birthdate"].dt.year
    - (
        (hoy.month < df["birthdate"].dt.month)
        | ((hoy.month == df["birthdate"].dt.month) & (hoy.day < df["birthdate"].dt.day))
    )
)

df["rango_edad"] = pd.cut(
    df["edad"],
    bins=[0, 12, 17, 24, 34, 44, 54, 64, 120],
    labels=["Niño","Adolescente","Joven","Adulto Joven","Adulto","Adulto Maduro","Adulto Mayor","Tercera Edad"],
    include_lowest=True,
)

df["membresia"] = np.random.choice(["normal", "premium"], size=len(df))


def normalizar(texto):
    texto = str(texto).strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

paises     = [c.name for c in pycountry.countries]
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
    estados_por_iso.setdefault(sub.country_code, []).append(sub.name)

estados_norm = {
    iso: {normalizar(e): e for e in estados}
    for iso, estados in estados_por_iso.items()
}

def corregir_estado(row):
    pais_obj = pycountry.countries.get(name=row["country"])
    if not pais_obj:
        return row["state"]
    catalogo = estados_norm.get(pais_obj.alpha_2)
    if not catalogo:
        return row["state"]
    match = process.extractOne(normalizar(row["state"]), catalogo.keys(), scorer=fuzz.WRatio)
    if match and match[1] >= 10:
        return catalogo[match[0]]
    return row["state"]

df["state"] = df.apply(corregir_estado, axis=1)

continent_map = {
    "AF":"África","AS":"Asia","EU":"Europa",
    "NA":"América del Norte","SA":"América del Sur",
    "OC":"Oceanía","AN":"Antártida",
}

def obtener_continente(pais):
    if pd.isna(pais) or str(pais).strip() == "":
        return "Desconocido"
    try:
        obj = pycountry.countries.search_fuzzy(str(pais).strip())[0]
        code = pycountry_convert.country_alpha2_to_continent_code(obj.alpha_2)
        return continent_map.get(code, "Desconocido")
    except Exception:
        return "Desconocido"

df["continent"] = df["country"].apply(obtener_continente)


def cargar_datos_to_rds(df_origen):
    print("[Fase L] Iniciando carga masiva en AWS RDS (UsersETL)...")


    df_ubi = (
        df_origen[["continent","country","state"]]
        .drop_duplicates()
        .rename(columns={"continent":"continente","country":"pais","state":"estado"})
    )
    df_ubi["continente"] = df_ubi["continente"].astype(str).str.strip()
    df_ubi["pais"]       = df_ubi["pais"].astype(str).str.strip()
    df_ubi["estado"]     = df_ubi["estado"].astype(str).str.strip()

    print(f"-> Insertando {len(df_ubi)} ubicaciones...")
    df_ubi.to_sql("ubicacion", con=engine_destino, if_exists="append",
                  index=False, method="multi", chunksize=500)


    print("-> Sincronizando llaves primarias...")
    with engine_destino.connect() as conn:
        df_ubi_db = pd.read_sql(
            text('SELECT id_ubicacion, continente, pais, estado FROM ubicacion;'), con=conn
        )


    df_map = df_origen.rename(columns={"continent":"continente","country":"pais","state":"estado"})
    df_merged = pd.merge(df_map, df_ubi_db, on=["continente","pais","estado"])

    df_usuario = pd.DataFrame({
        "id_usuario"    : df_merged["cognito_id"].astype(str).str.strip(),
        "nombre"        : df_merged["username"].astype(str).str.strip(),
        "edad"          : df_merged["edad"].astype("Int64"),
        "rango_edad"    : df_merged["rango_edad"].astype(str).str.strip(),
        "tipo_membresia": df_merged["membresia"].astype(str).str.strip(),
        "created_at"    : pd.to_datetime(df_merged["created_at"]),   # ← incluido
        "id_ubicacion"  : df_merged["id_ubicacion"].astype(int),
    })

    print(f"-> Insertando {len(df_usuario)} usuarios...")
    df_usuario.to_sql("usuario", con=engine_destino, if_exists="append",
                      index=False, method="multi", chunksize=1000)

    print("[ETL FIN] ¡Proceso completado exitosamente!")


cargar_datos_to_rds(df)