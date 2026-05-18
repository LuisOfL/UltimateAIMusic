from fastapi import FastAPI, UploadFile, File
import tempfile
import shutil
import os
import subprocess
import uuid
import pdfplumber
import whisper
from pydub import AudioSegment
from TTS.api import TTS
import boto3
import botocore

app = FastAPI()

# =========================
# AWS CONFIG
# =========================

REGION = "us-east-1"
BUCKET_NAME = "music-project-ia"

s3 = boto3.client(
    "s3",
    region_name=REGION
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)

# =========================
# PDF EXTRACT
# =========================

def extraer_texto_pdf(pdf_path):

    texto = ""

    with pdfplumber.open(pdf_path) as pdf:

        for pagina in pdf.pages:

            contenido = pagina.extract_text()

            if contenido:
                texto += contenido + "\n"

    return texto

# =========================
# IA (BEDROCK / GEMMA)
# =========================

def generar_letra(pdf_texto, letra_original, num_lines):

    prompt = f"""
SISTEMA: Eres un extractor de datos técnicos.

[DATOS DEL PDF]
{pdf_texto}

[ESTRUCTURA RÍTMICA]
{letra_original}

REGLAS:
- NO copies palabras originales
- SOLO usa información del PDF
- EXACTAMENTE {num_lines} líneas
- No expliques nada

RESULTADO:
"""

    response = bedrock.converse(
        modelId="google.gemma-3-12b-it",
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        inferenceConfig={
            "maxTokens": 1200,
            "temperature": 0.7,
            "topP": 0.9
        }
    )

    return response["output"]["message"]["content"][0]["text"]

# =========================
# API
# =========================

@app.post("/generate-song")
async def generate_song(
    pdf: UploadFile = File(...),
    song: UploadFile = File(...)
):

    with tempfile.TemporaryDirectory() as temp_dir:

        # =========================
        # GUARDAR ARCHIVOS
        # =========================

        pdf_path = os.path.join(temp_dir, pdf.filename)
        song_path = os.path.join(temp_dir, song.filename)

        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        with open(song_path, "wb") as f:
            shutil.copyfileobj(song.file, f)

        # =========================
        # PDF TEXT
        # =========================

        texto_pdf = extraer_texto_pdf(pdf_path)

        # =========================
        # DEMUCS
        # =========================

        subprocess.run([
            "demucs",
            "--two-stems=vocals",
            song_path
        ], check=True)

        song_name = os.path.splitext(os.path.basename(song_path))[0]

        demucs_folder = os.path.join(
            "separated",
            "htdemucs",
            song_name
        )

        vocals_wav = os.path.join(demucs_folder, "vocals.wav")
        instrumental_wav = os.path.join(demucs_folder, "no_vocals.wav")

        vocals_mp3 = os.path.join(temp_dir, "vocals.mp3")
        instrumental_mp3 = os.path.join(temp_dir, "instrumental.mp3")

        # =========================
        # CONVERT WAV -> MP3
        # =========================

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i",
            vocals_wav,
            vocals_mp3
        ], check=True)

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i",
            instrumental_wav,
            instrumental_mp3
        ], check=True)

        # =========================
        # WHISPER
        # =========================

        model = whisper.load_model("base")

        result = model.transcribe(
            vocals_mp3,
            language="en"
        )

        letra_original = result["text"]
        segments = result["segments"]
        num_lines = len(segments)

        # =========================
        # GENERAR LETRA IA
        # =========================

        letra_generada = generar_letra(
            texto_pdf,
            letra_original,
            num_lines
        )

        generated_lines = [
            x.strip()
            for x in letra_generada.split("\n")
            if x.strip()
        ]

        # =========================
        # TTS (VOICE GENERATION)
        # =========================

        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

        for i, line in enumerate(generated_lines):

            out_path = os.path.join(temp_dir, f"line_{i}.wav")

            tts.tts_to_file(
                text=line,
                speaker_wav=vocals_mp3,
                language="en",
                file_path=out_path
            )

        # =========================
        # MIX FINAL AUDIO
        # =========================

        instrumental = AudioSegment.from_mp3(instrumental_mp3) - 8

        final = instrumental

        max_len = min(len(segments), len(generated_lines))

        for i in range(max_len):

            voice_path = os.path.join(temp_dir, f"line_{i}.wav")

            voice = AudioSegment.from_wav(voice_path) + 5

            start_ms = int(segments[i]["start"] * 1000)

            final = final.overlay(voice, position=start_ms)

        # =========================
        # EXPORT FINAL MP3
        # =========================

        output_path = os.path.join(temp_dir, "cancion_final.mp3")

        final.export(output_path, format="mp3")

        # =========================
        # SUBIR A S3
        # =========================

        file_key = f"songs/{uuid.uuid4()}.mp3"

        try:
            s3.upload_file(
                output_path,
                BUCKET_NAME,
                file_key,
                ExtraArgs={
                    "ContentType": "audio/mpeg"
                }
            )
        except botocore.exceptions.ClientError as e:
            print("ERROR S3:", e)
            raise

        # =========================
        # URL PRESIGNED
        # =========================

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": file_key
            },
            ExpiresIn=3600
        )

        # =========================
        # RESPONSE
        # =========================

        return {
            "success": True,
            "audio_url": url
        }