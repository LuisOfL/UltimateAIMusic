import flet as ft

"""
Pantalla de carga animada con logo y barra de progreso estilizada
"""

def splash_view():

    # Notas musicales decorativas
    notas = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Text("♪", size=22, color=ft.Colors.with_opacity(0.3, ft.Colors.PURPLE_200)),
            ft.Text("♫", size=30, color=ft.Colors.with_opacity(0.5, ft.Colors.CYAN_300)),
            ft.Text("♩", size=18, color=ft.Colors.with_opacity(0.3, ft.Colors.PURPLE_200)),
        ]
    )

    logo_icon = ft.Container(
        width=90,
        height=90,
        border_radius=ft.border_radius.all(28),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#7C3AED", "#06B6D4"],
        ),
        content=ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=46, color=ft.Colors.WHITE),
        shadow=ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.5, "#7C3AED"),
            offset=ft.Offset(0, 8),
        ),
    )

    titulo = ft.Text(
        "EduSong",
        size=38,
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    subtitulo = ft.Text(
        "Aprendizaje a través de la música",
        size=14,
        color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
        text_align=ft.TextAlign.CENTER,
    )

    barra = ft.ProgressBar(
        width=180,
        color="#06B6D4",
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        border_radius=ft.border_radius.all(4),
    )

    version = ft.Text(
        "v1.0",
        size=11,
        color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
    )

    main = ft.Container(
        expand=True,
        width=float("inf"),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#0F0A1A", "#0A0F1A", "#0F0A1A"],
        ),
        alignment=ft.alignment.center,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                notas,
                ft.Container(height=8),
                logo_icon,
                ft.Container(height=4),
                titulo,
                subtitulo,
                ft.Container(height=20),
                barra,
                ft.Container(height=40),
                version,
            ],
        ),
    )

    return ft.View(
        route="/splash_screen",
        controls=[main],
        bgcolor="#0F0A1A",
        padding=0,
    )