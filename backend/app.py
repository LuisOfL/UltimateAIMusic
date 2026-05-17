from utils import extraer_texto_pdf_s3
from utils import separar_y_subir_audio
from utils import transcribir_audio_s3
from utils import llamar_qwen
from utils import generar_y_mezclar_tts_s3
from utils import extraer_nombre
from utils import subir_archivos
from utils import genera_url


def pipeline(bucket_name, idioma, pdf_local, song_local):
    # 1. Subir originales a S3 (esto te devuelve las rutas de S3)
    rutas_s3 = subir_archivos(pdf_local, song_local)
    pdf_s3_path = rutas_s3[0]
    
    # Extraemos el nombre para organizar las carpetas en S3
    song_name = extraer_nombre(song_local)
    
    # 2. Extraer texto del PDF (Usando la ruta de S3)
    texto = extraer_texto_pdf_s3(bucket_name, pdf_s3_path)
    
    # 3. SEPARACIÓN: ¡OJO! Aquí usamos 'song_local' (el archivo temporal en tu PC)
    # No uses 'music_path' porque esa es la ruta de S3 y Demucs no la lee.
    separar_y_subir_audio(song_local, bucket_name)
    
    # 4. Transcripción (Ahora sí, de lo que subió separar_y_subir_audio)
    res = transcribir_audio_s3(bucket_name, f"results/{song_name}/vocals.mp3")
    
    # 5. Generar letra con IA
    resultado = llamar_qwen(texto, res['texto_completo'], len(res['segmentos']), idioma)
    
    # 6. Mezclar y generar resultado final
    ruta_final = generar_y_mezclar_tts_s3(
        resultado=resultado,
        bucket=bucket_name,
        voice_key=f"results/{song_name}/vocals.mp3",
        instrumental_key=f"results/{song_name}/no_vocals.mp3",
        output_key=f"outputs/{song_name}.mp3",
        segmentos_whisper=res['segmentos'],
        language=idioma
    )
    url = genera_url(bucket_name,f"outputs/{song_name}.mp3")
    return url
