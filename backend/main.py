import os
import uuid
import shutil

from fastapi import FastAPI, UploadFile, File, Form

from app import pipeline

app = FastAPI()


@app.post("/pipeline")
async def run_pipeline(
    pdf: UploadFile = File(...),
    song: UploadFile = File(...),
    idioma: str = Form("es")
):

    # =========================
    # GUARDAR ARCHIVOS TEMPORALES
    # =========================

    temp_pdf = f"temp_{uuid.uuid4()}_{pdf.filename}"
    temp_song = f"temp_{uuid.uuid4()}_{song.filename}"

    with open(temp_pdf, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    with open(temp_song, "wb") as buffer:
        shutil.copyfileobj(song.file, buffer)

    # =========================
    # EJECUTAR PIPELINE
    # =========================

    url_publica = pipeline(
        bucket_name="music-project-ia",
        idioma=idioma,
        pdf_local=temp_pdf,
        song_local=temp_song
    )

    # =========================
    # LIMPIAR TEMPORALES
    # =========================

    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)

    if os.path.exists(temp_song):
        os.remove(temp_song)

    # =========================
    # RETORNAR URL
    # =========================

    return {
        "output_url": url_publica
    }