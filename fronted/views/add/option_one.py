import flet as ft
import httpx
import os

BACKEND_URL = "http://127.0.0.1:8000/pipeline"


def option_one_view(page: ft.Page):

    estado = {"pdf_path": None, "mp3_path": None}
    is_playing = {"value": False}
    # Reproductor se crea solo cuando llega la URL real (evita error de src vacío)
    audio_ref = {"player": None}

    texto_pdf = ft.Text("Sin archivo PDF", size=13, color=ft.Colors.GREY_500, italic=True)
    texto_mp3 = ft.Text("Sin archivo MP3", size=13, color=ft.Colors.GREY_500, italic=True)

    audio_status = ft.Text("", size=13, color=ft.Colors.GREEN_400, visible=False, weight=ft.FontWeight.W_600)

    progress_bar = ft.ProgressBar(value=0, color=ft.Colors.TEAL_400, bgcolor=ft.Colors.GREY_800, visible=False, expand=True)

    tiempo_txt = ft.Text("0:00 / 0:00", size=11, color=ft.Colors.GREY_400, visible=False)

    duracion_total = {"ms": 0}
    posicion_actual = {"ms": 0}

    def format_tiempo(ms):
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    def actualizar_tiempo():
        tiempo_txt.value = f"{format_tiempo(posicion_actual['ms'])} / {format_tiempo(duracion_total['ms'])}"

    def on_duration_changed(e):
        duracion_total["ms"] = int(e.data) if e.data else 0
        actualizar_tiempo()

    def on_position_changed(e):
        posicion_actual["ms"] = int(e.data) if e.data else 0
        if duracion_total["ms"] > 0:
            progress_bar.value = posicion_actual["ms"] / duracion_total["ms"]
        actualizar_tiempo()
        page.update()

    def on_state_changed(e):
        if e.data == "completed":
            is_playing["value"] = False
            btn_play.text = "▶  Reproducir"
            btn_play.icon = ft.Icons.PLAY_CIRCLE_ROUNDED
            progress_bar.value = 0
            posicion_actual["ms"] = 0
            actualizar_tiempo()
            page.update()

    btn_play = ft.ElevatedButton(
        "▶  Reproducir",
        icon=ft.Icons.PLAY_CIRCLE_ROUNDED,
        style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=20, vertical=10)),
        visible=False,
    )

    def toggle_play(e):
        p = audio_ref["player"]
        if p is None:
            return
        if not is_playing["value"]:
            p.play()
            is_playing["value"] = True
            btn_play.text = "⏸  Pausar"
            btn_play.icon = ft.Icons.PAUSE_CIRCLE_ROUNDED
        else:
            p.pause()
            is_playing["value"] = False
            btn_play.text = "▶  Reproducir"
            btn_play.icon = ft.Icons.PLAY_CIRCLE_ROUNDED
        page.update()

    btn_play.on_click = toggle_play

    btn_stop = ft.IconButton(icon=ft.Icons.STOP_CIRCLE_ROUNDED, icon_color=ft.Colors.RED_400, tooltip="Detener", visible=False)

    def stop_audio(e):
        p = audio_ref["player"]
        if p is None:
            return
        p.pause()
        p.seek(0)
        is_playing["value"] = False
        btn_play.text = "▶  Reproducir"
        btn_play.icon = ft.Icons.PLAY_CIRCLE_ROUNDED
        page.update()

    btn_stop.on_click = stop_audio

    btn_download = ft.ElevatedButton(
        "⬇  Descargar MP3",
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=20, vertical=10)),
        visible=False,
    )

    def descargar(e):
        p = audio_ref["player"]
        if p and p.src:
            page.launch_url(p.src)

    btn_download.on_click = descargar

    loading_row = ft.Row(
        controls=[ft.ProgressRing(width=20, height=20, stroke_width=2), ft.Text("Procesando… esto puede tardar unos minutos.", size=13)],
        visible=False,
    )

    error_txt = ft.Text("", color=ft.Colors.RED_400, size=13, visible=False)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    modo = {"tipo": 1}

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            f = e.files[0]
            if modo["tipo"] == 1:
                estado["pdf_path"] = f.path
                texto_pdf.value = f"📄 {f.name}"
                texto_pdf.color = ft.Colors.BLUE_300
                texto_pdf.italic = False
            else:
                estado["mp3_path"] = f.path
                texto_mp3.value = f"🎵 {f.name}"
                texto_mp3.color = ft.Colors.PURPLE_300
                texto_mp3.italic = False
            page.update()

    file_picker.on_result = on_file_result

    dropdown = ft.Dropdown(
        label="Idioma de la canción generada",
        value="es",
        options=[
            ft.dropdown.Option("es", "Español"),
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("zh", "中文 (Chino)"),
            ft.dropdown.Option("hi", "हिन्दी (Hindi)"),
        ],
        width=280,
        border_color=ft.Colors.BLUE_GREY_400,
    )

    btn_pdf = ft.ElevatedButton(
        "Cargar PDF", icon=ft.Icons.PICTURE_AS_PDF,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: (modo.update({"tipo": 1}), file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])),
    )

    btn_mp3 = ft.ElevatedButton(
        "Cargar MP3", icon=ft.Icons.MUSIC_NOTE,
        style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: (modo.update({"tipo": 2}), file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3"])),
    )

    btn_procesar = ft.ElevatedButton(
        "Procesar archivos", icon=ft.Icons.PLAY_ARROW_ROUNDED,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=24, vertical=12)),
    )

    async def procesar_async(e):
        for campo, msg in [
            ("pdf_path", "⚠️ Selecciona un archivo PDF primero."),
            ("mp3_path", "⚠️ Selecciona un archivo MP3 primero."),
        ]:
            if not estado[campo]:
                error_txt.value = msg
                error_txt.visible = True
                page.update()
                return
        for campo, msg in [
            ("pdf_path", "⚠️ No se encontró el PDF en disco."),
            ("mp3_path", "⚠️ No se encontró el MP3 en disco."),
        ]:
            if not os.path.exists(estado[campo]):
                error_txt.value = msg
                error_txt.visible = True
                page.update()
                return

        error_txt.visible = False
        audio_status.visible = False
        btn_play.visible = False
        btn_stop.visible = False
        btn_download.visible = False
        progress_bar.visible = False
        tiempo_txt.visible = False
        loading_row.visible = True
        btn_procesar.disabled = True

        # Eliminar reproductor anterior del overlay si existe
        if audio_ref["player"] is not None:
            try:
                page.overlay.remove(audio_ref["player"])
            except Exception:
                pass
            audio_ref["player"] = None

        is_playing["value"] = False
        btn_play.text = "▶  Reproducir"
        btn_play.icon = ft.Icons.PLAY_CIRCLE_ROUNDED
        progress_bar.value = 0
        duracion_total["ms"] = 0
        posicion_actual["ms"] = 0
        page.update()

        try:
            idioma = dropdown.value or "es"
            with open(estado["pdf_path"], "rb") as pdf_file, open(estado["mp3_path"], "rb") as mp3_file:
                async with httpx.AsyncClient(timeout=600) as client:
                    response = await client.post(
                        BACKEND_URL,
                        data={"idioma": idioma},
                        files={
                            "pdf": (os.path.basename(estado["pdf_path"]), pdf_file, "application/pdf"),
                            "song": (os.path.basename(estado["mp3_path"]), mp3_file, "audio/mpeg"),
                        },
                    )

            if response.status_code == 200:
                data = response.json()
                url = data.get("output_url", str(data))

                # Crear ft.Audio con URL real (nunca con src vacío)
                new_player = ft.Audio(
                    src=url,
                    autoplay=False,
                    on_duration_changed=on_duration_changed,
                    on_position_changed=on_position_changed,
                    on_state_changed=on_state_changed,
                )
                audio_ref["player"] = new_player
                page.overlay.append(new_player)

                audio_status.value = "✅ ¡Canción lista! Puedes reproducirla o descargarla."
                audio_status.visible = True
                btn_play.visible = True
                btn_stop.visible = True
                btn_download.visible = True
                progress_bar.visible = True
                tiempo_txt.visible = True
                error_txt.visible = False
            else:
                error_txt.value = f"❌ Error del servidor ({response.status_code}):\n{response.text[:300]}"
                error_txt.visible = True

        except httpx.ConnectError:
            error_txt.value = f"❌ No se pudo conectar al backend en:\n{BACKEND_URL}\nVerifica que FastAPI esté corriendo."
            error_txt.visible = True
        except Exception as ex:
            error_txt.value = f"❌ Error inesperado: {ex}"
            error_txt.visible = True
        finally:
            loading_row.visible = False
            btn_procesar.disabled = False
            page.update()

    btn_procesar.on_click = lambda e: page.run_task(procesar_async, e)

    low_menu = ft.Row(
        controls=[
            ft.ElevatedButton("Inicio", on_click=lambda e: page.go("/")),
            ft.ElevatedButton("Agregar", on_click=lambda e: page.go("/add")),
            ft.ElevatedButton("Config", on_click=lambda e: page.go("/config")),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    high_menu = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Generador de canciones educativas", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Text("1. Selecciona el idioma", weight=ft.FontWeight.W_600),
                dropdown,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Text("2. Sube el contenido del PDF", weight=ft.FontWeight.W_600),
                ft.Row([btn_pdf, texto_pdf], spacing=12, wrap=True),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Text("3. Sube la canción base (MP3)", weight=ft.FontWeight.W_600),
                ft.Row([btn_mp3, texto_mp3], spacing=12, wrap=True),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                btn_procesar,
                loading_row,
                error_txt,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                audio_status,
                ft.Row([btn_play, btn_stop, btn_download], spacing=12, wrap=True),
                ft.Row([progress_bar, tiempo_txt], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.padding.all(24),
        expand=True,
    )

    return ft.View(route="/option_one", controls=[high_menu, low_menu])