import streamlit as st
import requests

st.title("PDF → AI Song")

pdf = st.file_uploader(
    "Sube PDF",
    type=["pdf"]
)

song = st.file_uploader(
    "Sube canción",
    type=["mp3", "wav"]
)

if st.button("Generar canción"):

    if pdf and song:

        files = {
            "pdf": (
                pdf.name,
                pdf,
                "application/pdf"
            ),
            "song": (
                song.name,
                song,
                "audio/mpeg"
            )
        }

        with st.spinner("Generando canción IA..."):

            response = requests.post(
                "http://localhost:8000/generate-song",
                files=files
            )

        if response.status_code == 200:

            data = response.json()

            audio_url = data["audio_url"]

            st.success("Canción generada")

            # =========================
            # REPRODUCTOR
            # =========================

            st.audio(audio_url)

            # =========================
            # LINK DESCARGA
            # =========================

            st.markdown(
                f"[Descargar canción]({audio_url})"
            )

            # =========================
            # MOSTRAR URL
            # =========================

            st.code(audio_url)

        else:

            st.error("Error backend")

            st.text(response.text)

    else:

        st.warning("Sube ambos archivos")