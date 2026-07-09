import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from login import registrar_usuario, iniciar_sesion
from app import pipeline
from telemetria import PayloadTelemetria, procesar_e_insertar_metrica

app = FastAPI()


@app.post("/register")
async def register(user_data: dict):
    return registrar_usuario(
        email=user_data['email'],
        password=user_data['password'],
        username=user_data['username'],
        birthdate=user_data['birthdate'],
        country=user_data['country'],
        state=user_data['state']
    )

@app.post("/login")
async def login(user_data: dict):
    return iniciar_sesion(user_data['email'], user_data['password'])


@app.post("/pipeline")
async def run_pipeline(
    pdf: UploadFile = File(...),
    song: UploadFile = File(...),
    idioma: str = Form("es"),
    cognito_id: str = Form(...)  
):
    temp_pdf = f"temp_{uuid.uuid4()}_{pdf.filename}"
    temp_song = f"temp_{uuid.uuid4()}_{song.filename}"

    with open(temp_pdf, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    with open(temp_song, "wb") as buffer:
        shutil.copyfileobj(song.file, buffer)

    url_publica = pipeline(
        bucket_name="music-project-ia",
        idioma=idioma,
        pdf_local=temp_pdf,
        song_local=temp_song,
        cognito_id=cognito_id
    )

    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)

    if os.path.exists(temp_song):
        os.remove(temp_song)

    return {
        "output_url": url_publica
    }

@app.post("/api/v1/telemetria")
async def registrar_telemetria(data: PayloadTelemetria):
    return procesar_e_insertar_metrica(data)
