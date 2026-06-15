from concurrent.futures import ThreadPoolExecutor
import io
import os
import boto3
import joblib
import pandas as pd
from langdetect import detect, LangDetectException
from sqlalchemy import create_engine


S3_BUCKET_NAME = "music-project-ia"
AWS_REGION = "us-east-2"
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Destino: AWS RDS PostgreSQL Data Warehouse
DESTINO_URI = "postgresql://postgres:Nomelase123+@seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com:5432/CancionETL"

print("[INFO] Conectando al Data Warehouse de Destino en AWS RDS...")
engine_destino = create_engine(DESTINO_URI)


print("[INFO] Buscando y cargando modelos de Inteligencia Artificial locales...")
DIR_DEL_SCRIPT = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
CARPETA_MODELS = os.path.join(DIR_DEL_SCRIPT, "models")

vectorizer_path = os.path.join(CARPETA_MODELS, "tfidf_vectorizer.joblib")
topic_path = os.path.join(CARPETA_MODELS, "svm_topic_classifier.joblib")


AFFINITY_LEXICON = {
    "feliz": 1, "alegría": 2, "amor": 2, "fiesta": 1, "bailar": 1, "ganar": 1, "gol": 2,
    "triste": -1, "llorar": -2, "dolor": -1, "soledad": -2, "ira": -1, "perder": -1
}

try:
    vectorizer = joblib.load(vectorizer_path)
    topic_classifier = joblib.load(topic_path)
    print(f"[ÉXITO] Modelos cargados correctamente desde: {CARPETA_MODELS}")
except Exception as e:
    print(f"[ERROR CRÍTICO] Falló la carga de modelos. Ejecuta 'entrenar_modelos_locales.py'. Detalle: {e}")
    raise


def analyze_sentiment_as_genre(text: str) -> str:
    """
    Determina la polaridad emocional del texto y la mapea como el género analítico.
    """
    tokens = text.lower().split()
    score = sum(AFFINITY_LEXICON.get(token, 0) for token in tokens)
    
    if score > 1:
        return "Positivo / Energético"
    elif score < -1:
        return "Negativo / Melancólico"
    else:
        return "Neutro / Académico"

def procesar_cancion_individual(row_data):
    """
    Descarga un único archivo desde S3 y extrae sus features analíticas en RAM.
    """
    idx_simulado, cognito_id, ruta_letra = row_data
    
    if pd.isna(ruta_letra) or str(ruta_letra).strip() == "":
        return None
        
    clean_key = str(ruta_letra).strip().lstrip("/")
    
    try:
        # Descarga rápida directa a memoria RAM
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=clean_key)
        raw_text = response['Body'].read().decode('utf-8')
        
        if not raw_text.strip():
            return None
            
        # Minería de Datos: Detección de Idioma
        try:
            idioma = detect(raw_text)
        except LangDetectException:
            idioma = "unknown"
            
        # Análisis Léxico de Sentimientos (Mapeado a Género Analítico)
        genero_sentimiento = analyze_sentiment_as_genre(raw_text)
        
        # Inferencia del Clasificador ML (Predicción de Tema)
        text_vectorized = vectorizer.transform([raw_text])
        tema_predicho = topic_classifier.predict(text_vectorized)[0]
        
        # Mapeo limpio estructurado (Sin 'id_cancion' para respetar el SERIAL de la BD)
        return {
            "duracion": int(180 + (idx_simulado * 10)),
            "idioma": str(idioma).strip(),
            "tema": str(tema_predicho).strip(),
            "genero": str(genero_sentimiento).strip(),
            "id_autor": str(cognito_id).strip()
        }
        
    except Exception as e:
        print(f"[WARNING] Error procesando archivo S3 ({clean_key}): {e}")
        return None

def pipeline_nlp_masivo(df_origen):
    """
    Orquesta la segmentación y ejecución paralela mediante subprocesos hilos.
    """
    registros = [
        (i, row['cognito_id'], row['ruta_letra']) 
        for i, row in df_origen.iterrows()
    ]
    
    total_canciones = len(registros)
    print(f"\n[Fase T] Iniciando minería paralela para {total_canciones} canciones...")
    
    resultados_finales = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        for resultado in executor.map(procesar_cancion_individual, registros):
            if resultado:
                resultados_finales.append(resultado)
                
    return pd.DataFrame(resultados_finales)

# =========================================================================
# 4. CARGA CONTROLADA A LA BASE DE DATOS DESTINO (LOAD)
# =========================================================================
def cargar_canciones_to_rds(df_resultado):
    """
    Deposita el DataFrame estructurado en la tabla 'cancion' de RDS PostgreSQL.
    """
    if df_resultado.empty:
        print("[AVISO] El DataFrame está vacío. No hay datos que registrar.")
        return

    print("\n[Fase L] Iniciando proceso de carga masiva en AWS RDS...")
    
    # Filtramos y ordenamos las columnas exactas requeridas por la base de datos
    df_cancion_final = df_resultado[['duracion', 'idioma', 'tema', 'genero', 'id_autor']]
    
    try:
        print(f"-> Insertando {len(df_cancion_final)} registros analíticos en la tabla 'cancion'...")
        
        # Inserción en bloques a alta velocidad libre de comentarios de línea propensos a errores
        df_cancion_final.to_sql(
            name="cancion",
            con=engine_destino,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000
        )
        
        print("[ETL FIN] ¡Proceso de canciones completado exitosamente sin errores!")
        
    except Exception as e:
        print(f"[ERROR CRÍTICO] Falló la inserción masiva en el Data Warehouse: {e}")


if __name__ == "__main__":
    # Fase E: Extracción
    URL_CSV = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/DataLakeCanciones/option_one.csv"
    print(f"[Fase E] Extrayendo catálogo masivo desde: {URL_CSV}")
    df_inicial = pd.read_csv(URL_CSV)
    
    # Fase T: Transformación
    df_canciones_features = pipeline_nlp_masivo(df_inicial)
    
    # Fase L: Carga
    cargar_canciones_to_rds(df_canciones_features)