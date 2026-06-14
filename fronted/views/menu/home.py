import flet as ft
import boto3
import re as _re
import requests
import threading
from views.menu.navbar import nav_bar
from views.menu.topbar import top_bar

# ── CONFIGURACIÓN AWS S3 ────────────────────────────────────────────────────
BUCKET_NAME = "music-project-ia"
PREFIX = "outputs/"
S3_BASE_URL = f"https://{BUCKET_NAME}.s3.amazonaws.com/"
FASTAPI_TELEMETRIA_URL = "http://127.0.0.1:8000/api/v1/telemetria"

# Paletas de colores para las tarjetas (estilo Pinterest variado)
CARD_PALETTES = [
    ["#4C1D95", "#7C3AED"],   # Violeta profundo
    ["#1E3A8A", "#3B82F6"],   # Azul marino
    ["#134E4A", "#0D9488"],   # Verde esmeralda
    ["#7C2D12", "#EA580C"],   # Naranja quemado
    ["#1E1B4B", "#4F46E5"],   # Índigo oscuro
    ["#831843", "#EC4899"],   # Rosa fucsia
    ["#164E63", "#06B6D4"],   # Cian profundo
    ["#3B0764", "#A855F7"],   # Púrpura eléctrico
]

CARD_HEIGHTS = [110, 140, 120, 160, 125, 145, 115, 135]

MUSIC_ICONS = [
    ft.Icons.MUSIC_NOTE_ROUNDED,
    ft.Icons.HEADPHONES_ROUNDED,
    ft.Icons.PIANO_ROUNDED,
    ft.Icons.QUEUE_MUSIC_ROUNDED,
    ft.Icons.LIBRARY_MUSIC_ROUNDED,
    ft.Icons.ALBUM_ROUNDED,
    ft.Icons.AUDIOTRACK_ROUNDED,
    ft.Icons.GRAPHIC_EQ_ROUNDED,
]


def limpiar_nombre(key: str) -> str:
    """Convierte un key de S3 en nombre legible, eliminando UUIDs y prefijos."""
    nombre = key.replace(PREFIX, "").replace(".mp3", "").replace(".wav", "")
    nombre = _re.sub(
        r'[0-9a-f]{8}[-_]?[0-9a-f]{4}[-_]?[0-9a-f]{4}[-_]?[0-9a-f]{4}[-_]?[0-9a-f]{12}',
        '', nombre, flags=_re.IGNORECASE
    )
    nombre = _re.sub(r'\b[0-9a-f]{8,}\b', '', nombre, flags=_re.IGNORECASE)
    nombre = nombre.replace("_", " ").replace("-", " ")
    nombre = _re.sub(r'\s+', ' ', nombre).strip()
    return nombre.title() if nombre else "Canción"


# ── FIX #3: cognito_id se recibe como parámetro en lugar de buscarse en el scope ──
def home_view(page: ft.Page, cognito_id: str = "Unknown-User"):
    # ── ESTADOS ──────────────────────────────────────────────────────────────
    is_playing = {"value": False}
    duracion_total = {"ms": 0}
    posicion_actual = {"ms": 0}
    is_updating_slider = {"value": False}
    cancion_actual_src = {"url": ""}
    likes_count = {"value": 0}
    dislikes_count = {"value": 0}
    liked = {"value": False}
    disliked = {"value": False}

    # Acumuladores analíticos de reproducción en la sesión actual
    tiempo_escuchado_acumulado = {"ms": 0, "ultimo_registro": 0}

    # ── AUDIO PLAYER ─────────────────────────────────────────────────────────
    audio_player = ft.Audio(
        src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        autoplay=False,
        volume=1,
        balance=0,
    )
    page.overlay.append(audio_player)

    # ── CONTENEDORES DE VISTAS ────────────────────────────────────────────────
    contenedor_feed = ft.Container(expand=True, visible=True)
    contenedor_reproductor = ft.Container(expand=True, visible=False)

    # ── CONTROLES DEL REPRODUCTOR ─────────────────────────────────────────────
    txt_titulo_detalle = ft.Text(
        "",
        size=20,
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    txt_autor_detalle = ft.Text(
        "Autor: Inteligencia Artificial (SealMusic)",
        size=13,
        color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE),
    )

    btn_play_icon = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color="#0F0A1A", size=34)

    slider_progreso = ft.Slider(
        min=0,
        max=100,
        value=0,
        active_color="#A78BFA",
        inactive_color=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
        thumb_color="#7C3AED",
        expand=True,
    )

    txt_tiempo_actual = ft.Text("0:00", size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE))
    txt_tiempo_total = ft.Text("0:00", size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE))

    txt_likes = ft.Text("0", size=13, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE))
    txt_dislikes = ft.Text("0", size=13, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE))
    btn_like = ft.IconButton(
        icon=ft.Icons.THUMB_UP_OUTLINED,
        icon_color="#34D399",
        icon_size=22,
        tooltip="Me gusta",
    )
    btn_dislike = ft.IconButton(
        icon=ft.Icons.THUMB_DOWN_OUTLINED,
        icon_color="#F87171",
        icon_size=22,
        tooltip="No me gusta",
    )

    caratula_gradient = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=["#7C3AED", "#06B6D4"],
    )
    caratula_icon = ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=72, color=ft.Colors.WHITE)
    caratula_container = ft.Container(
        width=220,
        height=220,
        border_radius=ft.border_radius.all(28),
        gradient=caratula_gradient,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            blur_radius=40,
            color=ft.Colors.with_opacity(0.35, "#7C3AED"),
            offset=ft.Offset(0, 12),
        ),
        content=caratula_icon,
    )

    grid_pinterest = ft.ResponsiveRow(spacing=12, run_spacing=12)

    loading_indicator = ft.Container(
        alignment=ft.alignment.center,
        padding=ft.padding.all(50),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                ft.ProgressRing(color="#7C3AED", width=38, height=38, stroke_width=3),
                ft.Text(
                    "Conectando con AWS S3...",
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    size=13,
                ),
            ],
        ),
    )

    # ── FUNCIÓN DE EMISIÓN DE TELEMETRÍA (BACKGROUND THREADING) ────────────────
    def disparar_analitica_async(tipo_evento, segundos_reproduccion=0.0):
        """
        Despacha en un hilo secundario las métricas hacia la API.
        FIX #3: cognito_id viene del parámetro de home_view, siempre disponible.
        FIX #2: el nombre de la canción se lee de txt_titulo_detalle, que sí existe.
        FIX #1: se elimina el segundo hilo duplicado (post_worker) que causaba
                doble registro y NameError de payload fuera de scope.
        """
        # FIX #3: cognito_id es ahora un parámetro real de home_view
        user_id = str(cognito_id) if cognito_id else "Unknown-User"

        # FIX #2: leer el nombre del control que sí existe en este scope
        nombre_cancion = txt_titulo_detalle.value or "Unknown-Track"

        # FIX #1: un único hilo con el payload construido dentro de su propio scope
        def tarea_envio(u_id, c_name):
            try:
                payload = {
                    "id_usuario": u_id,
                    "id_cancion": c_name,
                    "tipo_evento": tipo_evento,
                    "contexto_dispositivo": {
                        "dispositivo": "Desktop-App",
                        "sistema_operativo": str(page.platform) if page.platform else "Unknown",
                        "idioma": "es-MX",
                        "tipo_conexion": "WiFi-Ethernet"
                    },
                    "segundos_escuchados": float(segundos_reproduccion)
                }

                response = requests.post(
                    FASTAPI_TELEMETRIA_URL,
                    json=payload,
                    timeout=5
                )

                if response.status_code == 200:
                    print(f"[Analítica] Evento '{tipo_evento}' de '{c_name}' registrado en RDS.")
                else:
                    print(f"[Analítica Error] Servidor respondió {response.status_code}: {response.text}")

            except Exception as ex:
                print(f"[Analítica Falló] Error en envío de red: {str(ex)}")

        # FIX #1: solo un hilo, no dos
        threading.Thread(target=tarea_envio, args=(user_id, nombre_cancion), daemon=True).start()

    # ── EVENTOS DE AUDIO CONTROLADOS ──────────────────────────────────────────
    def format_tiempo(ms: int) -> str:
        s = max(0, ms // 1000)
        return f"{s // 60}:{s % 60:02d}"

    def on_duration_changed(e):
        duracion_total["ms"] = int(e.data) if e.data else 0
        slider_progreso.max = max(1, duracion_total["ms"])
        txt_tiempo_total.value = format_tiempo(duracion_total["ms"])
        page.update()

    def on_position_changed(e):
        posicion_actual["ms"] = int(e.data) if e.data else 0
        if not is_updating_slider["value"] and duracion_total["ms"] > 0:
            slider_progreso.value = posicion_actual["ms"]
        txt_tiempo_actual.value = format_tiempo(posicion_actual["ms"])

        # Calcular delta de tiempo reproducido si el reproductor está activo
        if is_playing["value"]:
            delta = posicion_actual["ms"] - tiempo_escuchado_acumulado["ultimo_registro"]
            if 0 < delta < 2000:  # Filtrar saltos bruscos manuales en la barra
                tiempo_escuchado_acumulado["ms"] += delta
        tiempo_escuchado_acumulado["ultimo_registro"] = posicion_actual["ms"]
        page.update()

    def on_state_changed(e):
        if e.data == "completed":
            is_playing["value"] = False
            btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
            slider_progreso.value = 0
            posicion_actual["ms"] = 0
            txt_tiempo_actual.value = "0:00"

            # Al completarse, emitimos la reproducción completa
            disparar_analitica_async("reproduccion", segundos_reproduccion=tiempo_escuchado_acumulado["ms"] / 1000)
            tiempo_escuchado_acumulado["ms"] = 0
            page.update()

    audio_player.on_duration_changed = on_duration_changed
    audio_player.on_position_changed = on_position_changed
    audio_player.on_state_changed = on_state_changed

    def toggle_play(e):
        if not is_playing["value"]:
            audio_player.play()
            is_playing["value"] = True
            btn_play_icon.name = ft.Icons.PAUSE_ROUNDED
        else:
            audio_player.pause()
            is_playing["value"] = False
            btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED

            # Emitir métrica parcial al pausar
            if tiempo_escuchado_acumulado["ms"] > 500:
                disparar_analitica_async("reproduccion", segundos_reproduccion=tiempo_escuchado_acumulado["ms"] / 1000)
                tiempo_escuchado_acumulado["ms"] = 0
        page.update()

    def slider_changed(e):
        is_updating_slider["value"] = True
        audio_player.seek(int(slider_progreso.value))
        tiempo_escuchado_acumulado["ultimo_registro"] = int(slider_progreso.value)
        is_updating_slider["value"] = False

    slider_progreso.on_change_end = slider_changed

    # ── CAPTURA DE FEEDBACK (LIKE / DISLIKE) ──────────────────────────────────
    def dar_like(e):
        if not liked["value"]:
            likes_count["value"] += 1
            liked["value"] = True
            btn_like.icon = ft.Icons.THUMB_UP_ROUNDED
            disparar_analitica_async("like")
            if disliked["value"]:
                dislikes_count["value"] = max(0, dislikes_count["value"] - 1)
                disliked["value"] = False
                btn_dislike.icon = ft.Icons.THUMB_DOWN_OUTLINED
        else:
            likes_count["value"] = max(0, likes_count["value"] - 1)
            liked["value"] = False
            btn_like.icon = ft.Icons.THUMB_UP_OUTLINED
        txt_likes.value = str(likes_count["value"])
        txt_dislikes.value = str(dislikes_count["value"])
        page.update()

    def dar_dislike(e):
        if not disliked["value"]:
            dislikes_count["value"] += 1
            disliked["value"] = True
            btn_dislike.icon = ft.Icons.THUMB_DOWN_ROUNDED
            disparar_analitica_async("dislike")
            if liked["value"]:
                likes_count["value"] = max(0, likes_count["value"] - 1)
                liked["value"] = False
                btn_like.icon = ft.Icons.THUMB_UP_OUTLINED
        else:
            dislikes_count["value"] = max(0, dislikes_count["value"] - 1)
            disliked["value"] = False
            btn_dislike.icon = ft.Icons.THUMB_DOWN_OUTLINED
        txt_likes.value = str(likes_count["value"])
        txt_dislikes.value = str(dislikes_count["value"])
        page.update()

    btn_like.on_click = dar_like
    btn_dislike.on_click = dar_dislike

    # ── GESTIÓN DE NAVEGACIÓN Y CIERRES DE PISTA ──────────────────────────────
    def abrir_detalle_cancion(file_key, palette_idx=0, icon_idx=0):
        audio_player.pause()
        is_playing["value"] = False
        btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED
        slider_progreso.value = 0
        duracion_total["ms"] = 0
        posicion_actual["ms"] = 0
        tiempo_escuchado_acumulado["ms"] = 0
        tiempo_escuchado_acumulado["ultimo_registro"] = 0
        txt_tiempo_actual.value = "0:00"
        txt_tiempo_total.value = "0:00"

        txt_titulo_detalle.value = limpiar_nombre(file_key)
        url = f"{S3_BASE_URL}{file_key}"
        cancion_actual_src["url"] = url
        audio_player.src = url

        paleta = CARD_PALETTES[palette_idx % len(CARD_PALETTES)]
        caratula_gradient.colors = paleta
        caratula_icon.name = MUSIC_ICONS[icon_idx % len(MUSIC_ICONS)]

        likes_count["value"] = 0
        dislikes_count["value"] = 0
        liked["value"] = False
        disliked["value"] = False
        txt_likes.value = "0"
        txt_dislikes.value = "0"
        btn_like.icon = ft.Icons.THUMB_UP_OUTLINED
        btn_dislike.icon = ft.Icons.THUMB_DOWN_OUTLINED

        contenedor_feed.visible = False
        contenedor_reproductor.visible = True
        page.update()

    def regresar_al_feed(e):
        audio_player.pause()
        is_playing["value"] = False
        btn_play_icon.name = ft.Icons.PLAY_ARROW_ROUNDED

        # Despachar métrica acumulada antes de salir del reproductor
        if tiempo_escuchado_acumulado["ms"] > 500:
            disparar_analitica_async("reproduccion", segundos_reproduccion=tiempo_escuchado_acumulado["ms"] / 1000)

        tiempo_escuchado_acumulado["ms"] = 0
        contenedor_reproductor.visible = False
        contenedor_feed.visible = True
        page.update()

    def descargar_cancion(e):
        if cancion_actual_src["url"]:
            page.launch_url(cancion_actual_src["url"])
            disparar_analitica_async("descarga")

    # ── CARGA DESDE S3 ────────────────────────────────────────────────────────
    def _mostrar_vacio():
        grid_pinterest.controls.append(
            ft.Container(
                col=12,
                alignment=ft.alignment.center,
                padding=ft.padding.all(50),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Icon(ft.Icons.MUSIC_OFF_ROUNDED, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE), size=40),
                        ft.Text(
                            "No hay canciones en el bucket",
                            color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                            size=14,
                        ),
                    ],
                ),
            )
        )

    def _crear_tarjeta(key: str, idx: int):
        nombre = limpiar_nombre(key)
        paleta = CARD_PALETTES[idx % len(CARD_PALETTES)]
        altura_imagen = CARD_HEIGHTS[idx % len(CARD_HEIGHTS)]
        icono = MUSIC_ICONS[idx % len(MUSIC_ICONS)]

        tarjeta = ft.Container(
            col={"xs": 6, "sm": 6, "md": 4, "lg": 3},
            border_radius=ft.border_radius.all(18),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            on_click=lambda e, k=key, p=idx, ic=idx: abrir_detalle_cancion(k, p, ic),
            ink=True,
            ink_color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=altura_imagen,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=paleta,
                        ),
                        alignment=ft.alignment.center,
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    width=altura_imagen * 0.9,
                                    height=altura_imagen * 0.9,
                                    border_radius=ft.border_radius.all(999),
                                    bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(
                                    width=altura_imagen,
                                    height=altura_imagen,
                                    alignment=ft.alignment.center,
                                    content=ft.Icon(icono, size=40, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                                ),
                                ft.Container(
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.all(8),
                                    content=ft.Container(
                                        width=30,
                                        height=30,
                                        border_radius=ft.border_radius.all(15),
                                        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                                        alignment=ft.alignment.center,
                                        content=ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=18, color=ft.Colors.WHITE),
                                    ),
                                ),
                            ]
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=10),
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(
                                    nombre,
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.WHITE,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.Icon(ft.Icons.SMART_TOY_ROUNDED, size=10, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                                        ft.Text(
                                            "SealMusic AI",
                                            size=10,
                                            color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )
        grid_pinterest.controls.append(tarjeta)

    async def cargar_canciones_s3():
        try:
            s3 = boto3.client("s3")
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
            grid_pinterest.controls.clear()

            if "Contents" in response:
                archivos = [
                    obj["Key"]
                    for obj in response["Contents"]
                    if obj["Key"] != PREFIX and obj["Key"].lower().endswith((".mp3", ".wav"))
                ]
                if not archivos:
                    _mostrar_vacio()
                else:
                    for i, key in enumerate(archivos):
                        _crear_tarjeta(key, i)
            else:
                _mostrar_vacio()

        except Exception as ex:
            grid_pinterest.controls.clear()
            grid_pinterest.controls.append(
                ft.Container(
                    col=12,
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(30),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color="#F87171", size=36),
                            ft.Text(
                                "Error conectando con AWS S3",
                                color="#F87171",
                                size=14,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                str(ex),
                                color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                                size=11,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            )
        finally:
            loading_indicator.visible = False
            page.update()

    page.run_task(cargar_canciones_s3)

    # ── ESTRUCTURA GENERAL DE LOS CONTENEDORES ────────────────────────────────
    contenedor_feed.content = ft.Column(
        spacing=0,
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Explorar", size=24, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                                ft.Text("Canciones generadas con IA", size=12, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                            ],
                        ),
                        ft.Container(
                            width=36, height=36,
                            border_radius=ft.border_radius.all(12),
                            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.Icons.TUNE_ROUNDED, size=18, color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                        ),
                    ],
                ),
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=4),
                content=ft.Column(
                    spacing=0,
                    controls=[loading_indicator, grid_pinterest],
                ),
            ),
            ft.Container(height=24),
        ],
    )

    contenedor_reproductor.content = ft.Column(
        spacing=0,
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                            icon_color=ft.Colors.WHITE,
                            icon_size=28,
                            on_click=regresar_al_feed,
                            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                        ),
                        ft.Text("Reproduciendo ahora", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ft.Container(width=42),
                    ],
                ),
            ),
            ft.Container(
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=10),
                content=caratula_container,
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=28, vertical=12),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        txt_titulo_detalle,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.SMART_TOY_ROUNDED, size=13, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                                txt_autor_detalle,
                            ],
                        ),
                    ],
                ),
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20, vertical=4),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        slider_progreso,
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=6),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[txt_tiempo_actual, txt_tiempo_total],
                            ),
                        ),
                    ],
                ),
            ),
            ft.Container(
                padding=ft.padding.symmetric(vertical=16),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[btn_dislike, txt_dislikes]),
                        ft.IconButton(
                            icon=ft.Icons.REPLAY_10_ROUNDED,
                            icon_color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                            icon_size=28,
                            on_click=lambda e: audio_player.seek(max(0, posicion_actual["ms"] - 10000)),
                        ),
                        ft.Container(
                            width=68, height=68,
                            border_radius=ft.border_radius.all(34),
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=["#A78BFA", "#7C3AED"],
                            ),
                            alignment=ft.alignment.center,
                            on_click=toggle_play,
                            shadow=ft.BoxShadow(
                                blur_radius=20,
                                color=ft.Colors.with_opacity(0.4, "#7C3AED"),
                                offset=ft.Offset(0, 6),
                            ),
                            content=btn_play_icon,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.FORWARD_10_ROUNDED,
                            icon_color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                            icon_size=28,
                            on_click=lambda e: audio_player.seek(
                                min(duracion_total["ms"], posicion_actual["ms"] + 10000)
                            ),
                        ),
                        ft.Row(spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[btn_like, txt_likes]),
                    ],
                ),
            ),
            ft.Container(
                margin=ft.margin.symmetric(horizontal=24),
                height=1,
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=24, vertical=18),
                content=ft.ElevatedButton(
                    content=ft.Row(
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=18, color=ft.Colors.WHITE),
                            ft.Text("Descargar MP3", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ],
                    ),
                    on_click=descargar_cancion,
                    style=ft.ButtonStyle(
                        bgcolor={
                            ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            ft.ControlState.HOVERED: ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
                        },
                        shape=ft.RoundedRectangleBorder(radius=14),
                        padding=ft.padding.symmetric(horizontal=24, vertical=14),
                        overlay_color=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    ),
                    expand=True,
                ),
            ),
            ft.Container(height=12),
        ],
    )

    body = ft.Column(
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            top_bar(page),
            contenedor_feed,
            contenedor_reproductor,
        ],
    )

    main_scaffold = ft.Container(
        content=body,
        expand=True,
        bgcolor="#0F0A1A",
    )

    return ft.View(
        route="/",
        controls=[main_scaffold, nav_bar(page, active="home")],
        bgcolor="#0F0A1A",
        padding=0,
    )