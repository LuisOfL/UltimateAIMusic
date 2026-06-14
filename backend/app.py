import boto3
import io
from utils import extraer_texto_pdf_s3
from utils import separar_y_subir_audio
from utils import transcribir_audio_s3
from utils import llamar_qwen
from utils import generar_y_mezclar_tts_s3
from utils import extraer_nombre
from utils import subir_archivos
from utils import genera_url

# Importamos la nueva función 
from utils import agregar_registro_csv_s3

def pipeline(bucket_name, idioma, pdf_local, song_local, cognito_id):
    # 1. Subir originales a S3
    rutas_s3 = subir_archivos(pdf_local, song_local)
    pdf_s3_path = rutas_s3[0]
    
    # Extraemos el nombre para organizar las carpetas en S3
    song_name = extraer_nombre(song_local)
    
    # 2. Extraer texto del PDF
    texto = extraer_texto_pdf_s3(bucket_name, pdf_s3_path)
    
    # 3. Separación de audio
    separar_y_subir_audio(song_local, bucket_name)
    
    # 4. Transcripción
    datos_transcripcion = transcribir_audio_s3(bucket_name, f"results/{song_name}/vocals.mp3")
    
    # 5. Generar letra con IA
    resultado = llamar_qwen(texto, datos_transcripcion['texto_completo'], len(datos_transcripcion['segmentos']), idioma)
    
    # =========================================================================
    # NUEVO PASO: Subir la letra (.txt) a S3 en memoria sin guardarla en disco
    # =========================================================================
    s3_client = boto3.client('s3')
    letra_txt_key = f"letras/{song_name}_letra.txt"
    
    # Convertimos el string 'resultado' a bytes codificados en utf-8
    letra_bytes = resultado.encode('utf-8')
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=letra_txt_key,
        Body=letra_bytes,
        ContentType="text/plain; charset=utf-8"
    )
    # =========================================================================
    
    # 6. Mezclar y generar resultado final (.mp3)
    output_key_final = f"outputs/{song_name}.mp3"
    
    ruta_final = generar_y_mezclar_tts_s3(
        resultado=resultado, # Se le sigue pasando el string para generar la voz
        bucket=bucket_name,
        voice_key=f"results/{song_name}/vocals.mp3",
        instrumental_key=f"results/{song_name}/no_vocals.mp3",
        output_key=output_key_final,
        segmentos_whisper=datos_transcripcion['segmentos'],
        language=idioma
    )
    
    # 7. Generar URL
    url = genera_url(bucket_name, output_key_final)

    # 8. Guardar el registro en el CSV en S3
    # ¡OJO! Ahora pasamos 'letra_txt_key' en lugar del texto completo ('resultado')
    registro_a_subir = [output_key_final, letra_txt_key, cognito_id]
    
    # Definimos dónde se guardará el CSV dentro del bucket
    ruta_csv_s3 = "DataLakeCanciones/option_one.csv" 
    
    agregar_registro_csv_s3(bucket_name, ruta_csv_s3, registro_a_subir)

    return url