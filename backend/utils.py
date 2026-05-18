import boto3
import tempfile
import pdfplumber
import os
import subprocess
import whisper
import tempfile
from botocore.exceptions import ClientError
from TTS.api import TTS
from pydub import AudioSegment
from botocore.client import Config


def extraer_nombre(path):
    """Extrae el nombre base sin extensión de forma robusta."""
    return os.path.splitext(os.path.basename(path))[0]



def extraer_texto_pdf_s3(bucket, key):
    s3 = boto3.client("s3")
    with tempfile.TemporaryDirectory() as tmpdir:
        local_pdf = os.path.join(tmpdir, "file.pdf")
        s3.download_file(bucket, key, local_pdf)
        texto = ""
        with pdfplumber.open(local_pdf) as pdf:
            for pagina in pdf.pages:
                contenido = pagina.extract_text()
                if contenido:
                    texto += contenido + "\n"
        return texto
    


def separar_y_subir_audio(archivo, bucket, output_prefix="results"):
    s3 = boto3.client("s3")
    try:
        nombre = extraer_nombre(archivo)
        # Ejecutar Demucs - Usamos check=True para detenernos si hay error
        subprocess.run(["demucs", "--two-stems=vocals", archivo], check=True)

        # La carpeta de salida de Demucs por defecto es 'separated/htdemucs/nombre_del_archivo'
        output_folder = os.path.join("separated", "htdemucs", nombre)

        for root, dirs, files in os.walk(output_folder):
            for file in files:
                if file.endswith(".wav"):
                    wav_path = os.path.join(root, file)
                    mp3_path = wav_path.replace(".wav", ".mp3")

                    # Convertir WAV → MP3
                    subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path], check=True)

                    # Subir a S3 con el nombre limpio
                    s3_key = f"{output_prefix}/{nombre}/{file.replace('.wav', '.mp3')}"
                    s3.upload_file(mp3_path, bucket, s3_key)
    except Exception as e:
        print(f"Error en separar_y_subir_audio: {e}")
        raise e



def transcribir_audio_s3(bucket_name, s3_key, model_name="base", language="es"):
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    audio_bytes = obj["Body"].read()

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        local_file = f.name
        f.write(audio_bytes)

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(local_file, language=language)
        return {"texto_completo": result["text"], "segmentos": result["segments"]}
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)




def llamar_qwen(texto_pdf, letra_original, num_lines,idioma):
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    model_id = "google.gemma-3-12b-it"

    prompt = f"""
SISTEMA: Eres un extractor de datos técnicos. 
Tu objetivo es tomar la INFORMACIÓN del PDF y darle el ritmo de la ESTRUCTURA sugerida.

[DATOS TÉCNICOS DEL PDF]
{texto_pdf}

[ESTRUCTURA RÍTMICA A SEGUIR]
{letra_original}

[REGLAS CRÍTICAS]
- OBLIGATORIO: Solo usa conceptos encontrados en el 'DATOS TÉCNICOS DEL PDF'.
- Genera exactamente {num_lines} líneas.
- La letra debe estar en idioma {idioma}
- No saludes, no expliques, solo entrega la letra educativa.

RESULTADO (CANCIÓN TÉCNICA):
"""

    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]

    try:
        response = client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        return response['output']['message']['content'][0]['text']

    except ClientError as e:
        return f"Error de cliente: {e}"
    except Exception as e:
        return f"Error inesperado: {e}"
    

def generar_y_mezclar_tts_s3(
    resultado,
    bucket,
    voice_key,
    instrumental_key,
    output_key,
    segmentos_whisper,
    language="en",
    instrumental_gain=-8,
    voice_gain=5
):
    """
    1. Descarga voz de referencia desde S3
    2. Genera TTS temporal por línea
    3. Descarga instrumental
    4. Mezcla voces con instrumental
    5. Exporta mp3 final
    6. Sube resultado a S3
    """

    s3 = boto3.client("s3")

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    generated_lines = [
        x.strip()
        for x in resultado.split("\n")
        if x.strip()
    ]

    with tempfile.TemporaryDirectory() as tmpdir:

        # =========================
        # Descargar voz referencia
        # =========================

        local_voice = os.path.join(tmpdir, "voice.mp3")

        s3.download_file(
            bucket,
            voice_key,
            local_voice
        )

        # =========================
        # Descargar instrumental
        # =========================

        local_instrumental = os.path.join(
            tmpdir,
            "instrumental.mp3"
        )

        s3.download_file(
            bucket,
            instrumental_key,
            local_instrumental
        )

        instrumental = AudioSegment.from_mp3(
            local_instrumental
        )

        instrumental = instrumental + instrumental_gain

        final_audio = instrumental

        # =========================
        # Generar y mezclar voces
        # =========================

        max_len = min(
            len(generated_lines),
            len(segmentos_whisper)
        )

        for i in range(max_len):

            try:

                text = generated_lines[i]

                print(f"Generando línea {i}")

                wav_path = os.path.join(
                    tmpdir,
                    f"line_{i}.wav"
                )

                # =========================
                # Generar TTS
                # =========================

                tts.tts_to_file(
                    text=text,
                    speaker_wav=local_voice,
                    language=language,
                    file_path=wav_path
                )

                # =========================
                # Cargar voz generada
                # =========================

                voice = AudioSegment.from_wav(
                    wav_path
                )

                voice = voice + voice_gain

                # =========================
                # Posición del overlay
                # =========================

                start_ms = int(
                    segmentos_whisper[i]["start"] * 1000
                )

                print(
                    f"Overlay línea {i} en {start_ms} ms"
                )

                # =========================
                # Mezclar
                # =========================

                final_audio = final_audio.overlay(
                    voice,
                    position=start_ms
                )

            except Exception as e:

                print(f"Error línea {i}: {e}")

        # =========================
        # Exportar final
        # =========================

        final_local = os.path.join(
            tmpdir,
            "final.mp3"
        )

        final_audio.export(
            final_local,
            format="mp3"
        )

        # =========================
        # Subir a S3
        # =========================

        s3.upload_file(
            final_local,
            bucket,
            output_key
        )

        return f"s3://{bucket}/{output_key}"
    


def subir_archivos(path1, path2):
    pdf_name = os.path.basename(path1)
    song_name = os.path.basename(path2)
    
    s3 = boto3.client("s3")
    bucket = 'music-project-ia'
    
    s3_pdf_key = f'inputs/pdfs/{pdf_name}'
    s3_song_key = f'inputs/songs/{song_name}'
    
    s3.upload_file(path1, bucket, s3_pdf_key)
    s3.upload_file(path2, bucket, s3_song_key)
    
    return [s3_pdf_key, s3_song_key]



def genera_url(bucket,key):

    s3 = boto3.client(
        "s3",
        region_name="us-east-2",
        config=Config(signature_version="s3v4")
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key
        },
        ExpiresIn=3600  # 1 hora
    )
    return url