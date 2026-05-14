import flet as ft
import threading
import requests


def option_one_view(page: ft.Page):

    # =========================
    # VARIABLES
    # =========================

    pdf_path = {"value": None}
    song_path = {"value": None}

    texto_pdf = ft.Text("Ningún PDF seleccionado")
    texto_song = ft.Text("Ninguna canción seleccionada")

    audio_resultado = ft.Audio()
    page.overlay.append(audio_resultado)

    # =========================
    # IDIOMA SELECTOR
    # =========================

    idioma = ft.Dropdown(
        label="Idioma de salida",
        value="es",
        options=[
            ft.dropdown.Option("es"),
            ft.dropdown.Option("en"),
            ft.dropdown.Option("fr"),
            ft.dropdown.Option("de")
        ]
    )

    # =========================
    # MENÚ
    # =========================

    btn_play = ft.ElevatedButton(
        "Inicio",
        on_click=lambda e: page.go("/")
    )

    btn_create = ft.ElevatedButton(
        "Crear",
        on_click=lambda e: page.go("/add")
    )

    btn_config = ft.ElevatedButton(
        "Config",
        on_click=lambda e: page.go("/config")
    )

    # =========================
    # PDF PICKER
    # =========================

    def seleccionar_pdf(e: ft.FilePickerResultEvent):
        if e.files:
            archivo = e.files[0]
            pdf_path["value"] = archivo.path
            texto_pdf.value = f"PDF:\n{archivo.name}"
            page.update()

    pdf_picker = ft.FilePicker(on_result=seleccionar_pdf)

    # =========================
    # SONG PICKER
    # =========================

    def seleccionar_song(e: ft.FilePickerResultEvent):
        if e.files:
            archivo = e.files[0]
            song_path["value"] = archivo.path
            texto_song.value = f"Canción:\n{archivo.name}"
            page.update()

    song_picker = ft.FilePicker(on_result=seleccionar_song)

    page.overlay.append(pdf_picker)
    page.overlay.append(song_picker)

    # =========================
    # BOTONES UPLOAD
    # =========================

    btn_pdf = ft.ElevatedButton(
        "Subir PDF",
        on_click=lambda _: pdf_picker.pick_files(
            allowed_extensions=["pdf"]
        )
    )

    btn_song = ft.ElevatedButton(
        "Subir canción",
        on_click=lambda _: song_picker.pick_files(
            allowed_extensions=["mp3", "wav"]
        )
    )

    # =========================
    # PIPELINE BUTTON
    # =========================

    def crear_cancion(e):

        if not pdf_path["value"]:
            texto_pdf.value = "Selecciona un PDF"
            page.update()
            return

        if not song_path["value"]:
            texto_song.value = "Selecciona una canción"
            page.update()
            return

        texto_pdf.value = "Enviando PDF..."
        texto_song.value = "Enviando canción..."
        page.update()

        def task():

            try:
                with open(pdf_path["value"], "rb") as pdf_file, \
                     open(song_path["value"], "rb") as song_file:

                    files = {
                        "pdf": pdf_file,
                        "song": song_file
                    }

                    data = {
                        "idioma": idioma.value
                    }

                    response = requests.post(
                        "http://127.0.0.1:8000/pipeline",
                        files=files,
                        data=data,
                        timeout=600 
                    )

                result = response.json()
                output_url = result["output_url"]

                def update_ui():
                    texto_song.value = "¡Canción lista!"
                    audio_resultado.src = output_url
                    audio_resultado.autoplay = True
                    page.update()

                page.call_from_thread(update_ui)

            except Exception as ex:

                def error_ui():
                    texto_song.value = f"Error: {str(ex)}"
                    page.update()

                page.call_from_thread(error_ui)

        threading.Thread(target=task).start()

    btn_create_song = ft.ElevatedButton(
        "Crear canción",
        on_click=crear_cancion
    )

    # =========================
    # LAYOUT
    # =========================

    low_menu = ft.Row(
        controls=[btn_play, btn_create, btn_config],
        alignment=ft.MainAxisAlignment.CENTER
    )

    high_menu = ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[

                ft.Text("Crear una nueva canción", size=24),

                ft.Text("Sube un PDF", size=20),
                btn_pdf,
                texto_pdf,

                ft.Text("Escoge melodía de fondo", size=20),
                btn_song,
                texto_song,

                ft.Text("Escoge idioma", size=20),
                idioma,

                btn_create_song,
                audio_resultado
            ]
        )
    )

    return ft.View(
        route="/option_one",
        controls=[
            high_menu,
            low_menu
        ]
    )