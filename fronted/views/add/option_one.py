import flet as ft
import httpx
import os

# ─────────────────────────────────────────────
# Configura aquí la URL de tu backend FastAPI
# ─────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000/pipeline"


def option_one_view(page: ft.Page):

    # ── Estado ──────────────────────────────────
    estado = {
        "pdf_path": None,
        "mp3_path": None,
    }

    # ── Textos de estado ────────────────────────
    texto_pdf = ft.Text(
        "Sin archivo PDF",
        size=13,
        color=ft.Colors.GREY_500,
        italic=True,
    )
    texto_mp3 = ft.Text(
        "Sin archivo MP3",
        size=13,
        color=ft.Colors.GREY_500,
        italic=True,
    )

    # ── Resultado ────────────────────────────────
    resultado_txt = ft.TextField(
        label="URL del resultado",
        read_only=True,
        multiline=True,
        min_lines=3,
        max_lines=6,
        expand=True,
        visible=False,
        border_color=ft.Colors.GREEN_400,
        focused_border_color=ft.Colors.GREEN_600,
        label_style=ft.TextStyle(color=ft.Colors.GREEN_400),
    )

    # ── Indicador de carga ───────────────────────
    loading_row = ft.Row(
        controls=[
            ft.ProgressRing(width=20, height=20, stroke_width=2),
            ft.Text("Procesando… esto puede tardar unos minutos.", size=13),
        ],
        visible=False,
    )

    # ── Mensaje de error ─────────────────────────
    error_txt = ft.Text(
        "",
        color=ft.Colors.RED_400,
        size=13,
        visible=False,
    )

    # ── FilePicker ───────────────────────────────
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    modo = {"tipo": 1}

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            path = file.path

            if modo["tipo"] == 1:
                estado["pdf_path"] = path
                texto_pdf.value = f"📄 {file.name}"
                texto_pdf.color = ft.Colors.BLUE_300
                texto_pdf.italic = False
            else:
                estado["mp3_path"] = path
                texto_mp3.value = f"🎵 {file.name}"
                texto_mp3.color = ft.Colors.PURPLE_300
                texto_mp3.italic = False

            page.update()

    file_picker.on_result = on_file_result

    # ── Dropdown de idioma ───────────────────────
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

    # ── Botones de carga ─────────────────────────
    btn_pdf = ft.ElevatedButton(
        "Cargar PDF",
        icon=ft.Icons.PICTURE_AS_PDF,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=lambda e: (
            modo.update({"tipo": 1}),
            file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["pdf"],
            ),
        ),
    )

    btn_mp3 = ft.ElevatedButton(
        "Cargar MP3",
        icon=ft.Icons.MUSIC_NOTE,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=lambda e: (
            modo.update({"tipo": 2}),
            file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["mp3"],
            ),
        ),
    )

    # ── Botón procesar ───────────────────────────
    btn_procesar = ft.ElevatedButton(
        "Procesar archivos",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
        ),
    )

    async def procesar_async(e):
        if not estado["pdf_path"]:
            error_txt.value = "⚠️ Selecciona un archivo PDF primero."
            error_txt.visible = True
            resultado_txt.visible = False
            page.update()
            return

        if not estado["mp3_path"]:
            error_txt.value = "⚠️ Selecciona un archivo MP3 primero."
            error_txt.visible = True
            resultado_txt.visible = False
            page.update()
            return

        if not os.path.exists(estado["pdf_path"]):
            error_txt.value = "⚠️ No se encontró el PDF en disco."
            error_txt.visible = True
            page.update()
            return

        if not os.path.exists(estado["mp3_path"]):
            error_txt.value = "⚠️ No se encontró el MP3 en disco."
            error_txt.visible = True
            page.update()
            return

        error_txt.visible = False
        resultado_txt.visible = False
        loading_row.visible = True
        btn_procesar.disabled = True
        page.update()

        try:
            idioma = dropdown.value or "es"

            with open(estado["pdf_path"], "rb") as pdf_file, \
                 open(estado["mp3_path"], "rb") as mp3_file:

                async with httpx.AsyncClient(timeout=600) as client:
                    response = await client.post(
                        BACKEND_URL,
                        data={"idioma": idioma},
                        files={
                            "pdf": (
                                os.path.basename(estado["pdf_path"]),
                                pdf_file,
                                "application/pdf",
                            ),
                            "song": (
                                os.path.basename(estado["mp3_path"]),
                                mp3_file,
                                "audio/mpeg",
                            ),
                        },
                    )

            if response.status_code == 200:
                data = response.json()
                url = data.get("output_url", str(data))
                resultado_txt.value = url
                resultado_txt.visible = True
                error_txt.visible = False
            else:
                error_txt.value = (
                    f"❌ Error del servidor ({response.status_code}):\n"
                    f"{response.text[:300]}"
                )
                error_txt.visible = True

        except httpx.ConnectError:
            error_txt.value = (
                f"❌ No se pudo conectar al backend en:\n{BACKEND_URL}\n"
                "Verifica que FastAPI esté corriendo."
            )
            error_txt.visible = True
        except Exception as ex:
            error_txt.value = f"❌ Error inesperado: {ex}"
            error_txt.visible = True
        finally:
            loading_row.visible = False
            btn_procesar.disabled = False
            page.update()

    btn_procesar.on_click = lambda e: page.run_task(procesar_async, e)

    # ── Botón copiar URL ──────────────────────────
    def copiar_url(e):
        if resultado_txt.value:
            page.set_clipboard(resultado_txt.value)
            page.open(
                ft.SnackBar(content=ft.Text("✅ URL copiada al portapapeles"))
            )

    btn_copiar = ft.IconButton(
        icon=ft.Icons.COPY,
        tooltip="Copiar URL",
        on_click=copiar_url,
    )

    # ── Menú inferior ─────────────────────────────
    low_menu = ft.Row(
        controls=[
            ft.ElevatedButton("Inicio", on_click=lambda e: page.go("/")),
            ft.ElevatedButton("Agregar", on_click=lambda e: page.go("/add")),
            ft.ElevatedButton("Config", on_click=lambda e: page.go("/config")),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ── Layout principal ─────────────────────────
    high_menu = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Generador de canciones educativas",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
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
                ft.Row(
                    [
                        ft.Text("Resultado:", weight=ft.FontWeight.W_600),
                        btn_copiar,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                resultado_txt,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.padding.all(24),
        expand=True,
    )

    return ft.View(
        route="/option_one",
        controls=[high_menu, low_menu],
    )