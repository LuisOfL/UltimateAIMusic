import flet as ft
from views.menu.navbar import nav_bar

def add_view(page: ft.Page):

    header = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=40, bottom=8),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text("Crear", size=32, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                ft.Text(
                    "Elige cómo generar tu canción",
                    size=14,
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                ),
            ],
        ),
    )

    def option_card(icon, title, subtitle, route, gradient_colors, accent):
        return ft.Container(
            margin=ft.margin.symmetric(horizontal=20),
            on_click=lambda e: page.go(route),
            ink=True,
            border_radius=ft.border_radius.all(20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            shadow=ft.BoxShadow(
                blur_radius=16,
                color=ft.Colors.with_opacity(0.25, accent),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=58,
                        height=58,
                        border_radius=ft.border_radius.all(16),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=gradient_colors,
                        ),
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=28),
                    ),
                    ft.Container(width=16),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                            ft.Text(
                                subtitle,
                                size=12,
                                color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                                max_lines=2,
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE), size=20),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(16),
        )

    badge_new = ft.Container(
        margin=ft.margin.only(left=20, bottom=4),
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
        border_radius=ft.border_radius.all(20),
        bgcolor=ft.Colors.with_opacity(0.15, "#06B6D4"),
        content=ft.Text("3 métodos disponibles", size=11, color="#06B6D4", weight=ft.FontWeight.W_600),
    )

    content = ft.Column(
        controls=[
            header,
            ft.Container(height=12),
            badge_new,
            ft.Container(height=8),
            option_card(
                ft.Icons.PICTURE_AS_PDF_ROUNDED,
                "PDF + Canción base",
                "Sube un PDF y una pista MP3 para generar tu canción educativa",
                "/option_one",
                ["#7C3AED", "#06B6D4"],
                "#7C3AED",
            ),
            ft.Container(height=12),
            option_card(
                ft.Icons.TEXT_SNIPPET_ROUNDED,
                "Texto libre",
                "Escribe o pega el contenido y deja que la IA compose la canción",
                "/option_two",
                ["#DB2777", "#F59E0B"],
                "#DB2777",
            ),
            ft.Container(height=12),
            option_card(
                ft.Icons.MIC_ROUNDED,
                "Grabación de voz",
                "Graba tu explicación y transfórmala en una melodía educativa",
                "/option_three",
                ["#059669", "#06B6D4"],
                "#059669",
            ),
            ft.Container(height=20),
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
        route="/add",
        controls=[main, nav_bar(page, active="add")],
        bgcolor="#0F0A1A",
        padding=0,
    )