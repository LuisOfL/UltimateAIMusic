import flet as ft
from views.menu.navbar import nav_bar
from views.menu.topbar import top_bar


def home_view(page: ft.Page):

    header = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=40, bottom=16),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(
                    "Hola 👋",
                    size=14,
                    color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE),
                ),
                ft.Text(
                    "EduSong",
                    size=34,
                    weight=ft.FontWeight.W_800,
                    color=ft.Colors.WHITE,
                ),
            ],
        ),
    )

    # Tarjeta de bienvenida destacada
    hero_card = ft.Container(
        margin=ft.margin.symmetric(horizontal=20),
        padding=ft.padding.all(22),
        border_radius=ft.border_radius.all(20),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#4C1D95", "#0E7490"],
        ),
        shadow=ft.BoxShadow(
            blur_radius=24,
            color=ft.Colors.with_opacity(0.4, "#7C3AED"),
            offset=ft.Offset(0, 8),
        ),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=ft.border_radius.all(14),
                            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                            content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.WHITE, size=24),
                        ),
                        ft.Container(width=10),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Canciones Generadas", size=12, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
                                ft.Text("0 canciones", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                            ],
                        ),
                    ]
                ),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
                ft.Text(
                    "Convierte cualquier tema educativo en una canción memorable.",
                    size=13,
                    color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                ),
                ft.ElevatedButton(
                    "Crear canción →",
                    on_click=lambda e: page.go("/add"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.WHITE,
                        color="#4C1D95",
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        elevation=0,
                    ),
                ),
            ],
        ),
    )

    def stat_chip(icon, label, value, color):
        return ft.Container(
            expand=True,
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(16),
            bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(icon, color=color, size=22),
                    ft.Text(value, size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ft.Text(label, size=11, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                ],
            ),
        )

    stats_row = ft.Container(
        margin=ft.margin.symmetric(horizontal=20),
        content=ft.Row(
            spacing=12,
            controls=[
                stat_chip(ft.Icons.MUSIC_NOTE_ROUNDED, "Canciones", "0", "#06B6D4"),
                stat_chip(ft.Icons.PICTURE_AS_PDF_ROUNDED, "PDFs", "0", "#A78BFA"),
                stat_chip(ft.Icons.STAR_ROUNDED, "Favoritos", "0", "#F59E0B"),
            ],
        ),
    )

    section_title = ft.Container(
        padding=ft.padding.only(left=24, top=8),
        content=ft.Text(
            "Actividad reciente",
            size=16,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.WHITE,
        ),
    )

    empty_state = ft.Container(
        margin=ft.margin.symmetric(horizontal=20),
        padding=ft.padding.all(28),
        border_radius=ft.border_radius.all(16),
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.QUEUE_MUSIC_ROUNDED, size=42, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                ft.Text(
                    "Aún no hay canciones",
                    size=14,
                    color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Crea tu primera canción educativa",
                    size=12,
                    color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )

    content = ft.Column(
        controls=[
            header,
            hero_card,
            ft.Container(height=16),
            stats_row,
            ft.Container(height=16),
            section_title,
            ft.Container(height=8),
            empty_state,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
    )

    main = ft.Container(
        content=content,
        expand=True,
        bgcolor="#0F0A1A",
    )

    return ft.View(
        route="/",
        controls=[top_bar(page),main, nav_bar(page, active="home")],
        bgcolor="#0F0A1A",
        padding=0,
    )