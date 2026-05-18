import flet as ft
import httpx
import os

BACKEND_URL = "http://127.0.0.1:8000/pipeline"


def option_one_view(page: ft.Page):

    estado = {"pdf_path": None, "mp3_path": None}
    is_playing = {"value": False}
    audio_ref = {"player": None}

    # ── Estado de archivos ──────────────────────────────────────────────
    texto_pdf = ft.Text("Ningún archivo seleccionado", size=12,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE), italic=True)
    texto_mp3 = ft.Text("Ningún archivo seleccionado", size=12,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE), italic=True)

    audio_status = ft.Container(
        visible=False,
        padding=ft.padding.all(12),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.with_opacity(0.12, "#059669"),
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, "#059669")),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#34D399", size=18),
                ft.Container(width=8),
                ft.Text("¡Canción lista! Puedes reproducirla o descargarla.", size=13,
                         color="#34D399", weight=ft.FontWeight.W_500),
            ]
        ),
    )

    progress_bar = ft.ProgressBar(
        value=0, color="#7C3AED",
        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
        border_radius=ft.border_radius.all(4),
        visible=False,
        expand=True,
    )
    tiempo_txt = ft.Text("0:00 / 0:00", size=11, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE), visible=False)

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
            btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
            progress_bar.value = 0
            posicion_actual["ms"] = 0
            actualizar_tiempo()
            page.update()

    btn_play_icon = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=ft.Colors.WHITE, size=22)

    btn_play = ft.Container(
        visible=False,
        on_click=None,
        ink=True,
        border_radius=ft.border_radius.all(14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#7C3AED", "#06B6D4"],
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        content=ft.Row(
            spacing=8,
            controls=[btn_play_icon, ft.Text("Reproducir", color=ft.Colors.WHITE, weight=ft.FontWeight.W_600, size=14)],
        ),
    )

    def toggle_play(e):
        p = audio_ref["player"]
        if p is None:
            return
        if not is_playing["value"]:
            p.play()
            is_playing["value"] = True
            btn_play_icon.name = ft.Icons.PAUSE_ROUNDED
        else:
            p.pause()
            is_playing["value"] = False
            btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
        page.update()

    btn_play.on_click = toggle_play

    btn_stop = ft.Container(
        visible=False,
        on_click=None,
        ink=True,
        border_radius=ft.border_radius.all(14),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        content=ft.Icon(ft.Icons.STOP_ROUNDED, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE), size=20),
    )

    def stop_audio(e):
        p = audio_ref["player"]
        if p is None:
            return
        p.pause()
        p.seek(0)
        is_playing["value"] = False
        btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
        page.update()

    btn_stop.on_click = stop_audio

    btn_download = ft.Container(
        visible=False,
        on_click=None,
        ink=True,
        border_radius=ft.border_radius.all(14),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        content=ft.Row(
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE), size=18),
                ft.Text("Descargar", color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE), size=13),
            ],
        ),
    )

    def descargar(e):
        p = audio_ref["player"]
        if p and p.src:
            page.launch_url(p.src)

    btn_download.on_click = descargar

    loading_row = ft.Container(
        visible=False,
        padding=ft.padding.all(16),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        content=ft.Row(
            controls=[
                ft.ProgressRing(width=18, height=18, stroke_width=2, color="#7C3AED"),
                ft.Container(width=12),
                ft.Text("Procesando… esto puede tardar unos minutos.", size=13,
                         color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
            ]
        ),
    )

    error_container = ft.Container(
        visible=False,
        padding=ft.padding.all(12),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.with_opacity(0.12, "#DC2626"),
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, "#DC2626")),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color="#F87171", size=18),
                ft.Container(width=8),
                ft.Text("", size=12, color="#F87171", expand=True),
            ]
        ),
    )

    def set_error(msg):
        error_container.content.controls[2].value = msg
        error_container.visible = True

    # ── File Picker ─────────────────────────────────────────────────────
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    modo = {"tipo": 1}

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            f = e.files[0]
            if modo["tipo"] == 1:
                estado["pdf_path"] = f.path
                texto_pdf.value = f"📄 {f.name}"
                texto_pdf.color = "#A78BFA"
                texto_pdf.italic = False
            else:
                estado["mp3_path"] = f.path
                texto_mp3.value = f"🎵 {f.name}"
                texto_mp3.color = "#06B6D4"
                texto_mp3.italic = False
            page.update()

    file_picker.on_result = on_file_result

    # ── Upload cards ────────────────────────────────────────────────────
    def upload_card(icon, label, color, pick_fn, texto_widget):
        return ft.Container(
            on_click=pick_fn,
            ink=True,
            expand=True,
            border_radius=ft.border_radius.all(16),
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            padding=ft.padding.all(16),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        border_radius=ft.border_radius.all(12),
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        content=ft.Icon(icon, color=color, size=22),
                    ),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    texto_widget,
                ],
            ),
        )

    def pick_pdf(e):
        modo.update({"tipo": 1})
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])

    def pick_mp3(e):
        modo.update({"tipo": 2})
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3"])

    dropdown = ft.Dropdown(
        label="Idioma de la canción",
        value="es",
        options=[
            ft.dropdown.Option("es", "🇪🇸 Español"),
            ft.dropdown.Option("en", "🇬🇧 English"),
            ft.dropdown.Option("zh", "🇨🇳 中文 (Chino)"),
            ft.dropdown.Option("hi", "🇮🇳 हिन्दी (Hindi)"),
        ],
        border_color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        focused_border_color="#7C3AED",
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border_radius=ft.border_radius.all(12),
    )

    btn_procesar = ft.Container(
        on_click=None,
        ink=True,
        border_radius=ft.border_radius.all(14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#059669", "#0891B2"],
        ),
        padding=ft.padding.symmetric(vertical=14),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.WHITE, size=20),
                ft.Text("Procesar y generar canción", color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700, size=14),
            ],
        ),
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.35, "#059669"),
            offset=ft.Offset(0, 6),
        ),
    )

    async def procesar_async(e):
        for campo, msg in [
            ("pdf_path", "Selecciona un archivo PDF primero."),
            ("mp3_path", "Selecciona un archivo MP3 primero."),
        ]:
            if not estado[campo]:
                set_error(f"⚠️ {msg}")
                page.update()
                return
        for campo, msg in [
            ("pdf_path", "No se encontró el PDF en disco."),
            ("mp3_path", "No se encontró el MP3 en disco."),
        ]:
            if not os.path.exists(estado[campo]):
                set_error(f"⚠️ {msg}")
                page.update()
                return

        error_container.visible = False
        audio_status.visible = False
        btn_play.visible = False
        btn_stop.visible = False
        btn_download.visible = False
        progress_bar.visible = False
        tiempo_txt.visible = False
        loading_row.visible = True
        btn_procesar.opacity = 0.5

        if audio_ref["player"] is not None:
            try:
                page.overlay.remove(audio_ref["player"])
            except Exception:
                pass
            audio_ref["player"] = None

        is_playing["value"] = False
        btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
        progress_bar.value = 0
        duracion_total["ms"] = 0
        posicion_actual["ms"] = 0
        page.update()

        try:
            idioma = dropdown.value or "es"
            with open(estado["pdf_path"], "rb") as pdf_f, open(estado["mp3_path"], "rb") as mp3_f:
                async with httpx.AsyncClient(timeout=600) as client:
                    response = await client.post(
                        BACKEND_URL,
                        data={"idioma": idioma},
                        files={
                            "pdf": (os.path.basename(estado["pdf_path"]), pdf_f, "application/pdf"),
                            "song": (os.path.basename(estado["mp3_path"]), mp3_f, "audio/mpeg"),
                        },
                    )

            if response.status_code == 200:
                data = response.json()
                url = data.get("output_url", str(data))
                new_player = ft.Audio(
                    src=url,
                    autoplay=False,
                    on_duration_changed=on_duration_changed,
                    on_position_changed=on_position_changed,
                    on_state_changed=on_state_changed,
                )
                audio_ref["player"] = new_player
                page.overlay.append(new_player)
                audio_status.visible = True
                btn_play.visible = True
                btn_stop.visible = True
                btn_download.visible = True
                progress_bar.visible = True
                tiempo_txt.visible = True
                error_container.visible = False
            else:
                set_error(f"Error del servidor ({response.status_code}): {response.text[:200]}")
        except httpx.ConnectError:
            set_error(f"No se pudo conectar al backend en {BACKEND_URL}")
        except Exception as ex:
            set_error(f"Error inesperado: {ex}")
        finally:
            loading_row.visible = False
            btn_procesar.opacity = 1.0
            page.update()

    btn_procesar.on_click = lambda e: page.run_task(procesar_async, e)

    # ── Header ──────────────────────────────────────────────────────────
    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=16, bottom=4),
        content=ft.Row(
            controls=[
                ft.Container(
                    on_click=lambda e: page.go("/add"),
                    ink=True,
                    border_radius=ft.border_radius.all(10),
                    padding=ft.padding.all(8),
                    bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
                    content=ft.Icon(ft.Icons.ARROW_BACK_IOS_ROUNDED, color=ft.Colors.WHITE, size=18),
                ),
                ft.Container(width=12),
                ft.Column(
                    spacing=1,
                    controls=[
                        ft.Text("PDF + Canción base", size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text("Genera tu canción educativa", size=12, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                    ],
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    def section(num, text):
        return ft.Container(
            padding=ft.padding.only(bottom=8, top=4),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=24,
                        height=24,
                        border_radius=ft.border_radius.all(8),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=["#7C3AED", "#06B6D4"],
                        ),
                        content=ft.Text(str(num), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700,
                                        text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(text, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    body = ft.Column(
        controls=[
            header,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20),
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Container(height=4),
                        section(1, "Idioma de la canción"),
                        dropdown,
                        section(2, "Archivos de entrada"),
                        ft.Row(
                            spacing=12,
                            controls=[
                                upload_card(ft.Icons.PICTURE_AS_PDF_ROUNDED, "PDF", "#A78BFA", pick_pdf, texto_pdf),
                                upload_card(ft.Icons.MUSIC_NOTE_ROUNDED, "MP3", "#06B6D4", pick_mp3, texto_mp3),
                            ],
                        ),
                        section(3, "Generar"),
                        btn_procesar,
                        loading_row,
                        error_container,
                        audio_status,
                        ft.Row(controls=[btn_play, btn_stop, btn_download], spacing=10, wrap=True),
                        ft.Row(controls=[progress_bar, tiempo_txt], spacing=10,
                               vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(height=12),
                    ],
                ),
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
    )

    main = ft.Container(
        content=body,
        expand=True,
        bgcolor="#0F0A1A",
    )

    return ft.View(
        route="/option_one",
        controls=[main],
        bgcolor="#0F0A1A",
        padding=0,
    )