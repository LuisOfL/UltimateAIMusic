import os
import uuid
import shutil

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles

from app import pipeline

app = FastAPI()

# =========================
# SERVIR ARCHIVOS OUTPUT
# =========================

os.makedirs("outputs", exist_ok=True)

app.mount(
    "/outputs",
    StaticFiles(directory="outputs"),
    name="outputs"
)

# =========================
# PIPELINE ENDPOINT
# =========================

@app.post("/pipeline")
async def run_pipeline(
    pdf: UploadFile = File(...),
    song: UploadFile = File(...),
    idioma: str = Form("es")
):
    # Limpiamos el nombre para evitar espacios o caracteres raros
    clean_pdf_name = pdf.filename.replace(" ", "_")
    clean_song_name = song.filename.replace(" ", "_")
    
    # El nombre base será usado por demucs, así que lo mantenemos identificable
    temp_pdf = f"temp_{uuid.uuid4().hex[:8]}_{clean_pdf_name}"
    temp_song = f"temp_{uuid.uuid4().hex[:8]}_{clean_song_name}"

    try:
        with open(temp_pdf, "wb") as buffer:
            shutil.copyfileobj(pdf.file, buffer)
        with open(temp_song, "wb") as buffer:
            shutil.copyfileobj(song.file, buffer)

        output_path = pipeline(
            bucket_name="music-project-ia",
            idioma=idioma,
            pdf_local=temp_pdf,
            song_local=temp_song
        )

        filename = os.path.basename(output_path)
        return {"output_url": f"http://127.0.0.1:8000/outputs/{filename}"}

    finally:
        # Limpieza de archivos temporales locales para no saturar el servidor
        if os.path.exists(temp_pdf): os.remove(temp_pdf)
        if os.path.exists(temp_song): os.remove(temp_song)