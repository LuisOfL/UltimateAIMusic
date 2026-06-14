import flet as ft
from views.menu.navbar import nav_bar

def config_view(page: ft.Page):

    header = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=40, bottom=8),
        content=ft.Text("Ajustes", size=32, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
    )

    def section_label(text):
        return ft.Container(
            padding=ft.padding.only(left=24, top=12, bottom=4),
            content=ft.Text(
                text.upper(),
                size=11,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE),
                letter_spacing=1.2,
            ),
        )

    def settings_tile(icon, title, subtitle=None, trailing=None, on_click=None):
        return ft.Container(
            margin=ft.margin.symmetric(horizontal=20, vertical=2),
            padding=ft.padding.all(14),
            border_radius=ft.border_radius.all(14),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            on_click=on_click,
            ink=on_click is not None,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=ft.border_radius.all(10),
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                        content=ft.Icon(icon, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE), size=18),
                    ),
                    ft.Container(width=12),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(title, size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                            *([ ft.Text(subtitle, size=12, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)) ] if subtitle else []),
                        ],
                    ),
                    trailing or ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), size=18),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    toggle_dark = ft.Switch(value=True, active_color="#7C3AED", scale=0.8)
    toggle_notif = ft.Switch(value=False, active_color="#7C3AED", scale=0.8)

    # Tarjeta de perfil
    profile_card = ft.Container(
        margin=ft.margin.symmetric(horizontal=20),
        padding=ft.padding.all(18),
        border_radius=ft.border_radius.all(20),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1E1040", "#0E3040"],
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        content=ft.Row(
            controls=[
                ft.Container(
                    width=54,
                    height=54,
                    border_radius=ft.border_radius.all(17),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=["#7C3AED", "#06B6D4"],
                    ),
                    content=ft.Icon(ft.Icons.PERSON_ROUNDED, color=ft.Colors.WHITE, size=28),
                ),
                ft.Container(width=14),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Usuario", size=17, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text("Plan gratuito", size=12, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                    ],
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=5),
                    border_radius=ft.border_radius.all(20),
                    bgcolor=ft.Colors.with_opacity(0.15, "#7C3AED"),
                    content=ft.Text("FREE", size=11, color="#A78BFA", weight=ft.FontWeight.W_700),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    content = ft.Column(
        controls=[
            header,
            ft.Container(height=12),
            profile_card,
            section_label("Apariencia"),
            settings_tile(ft.Icons.DARK_MODE_ROUNDED, "Modo oscuro", trailing=toggle_dark),
            settings_tile(ft.Icons.LANGUAGE_ROUNDED, "Idioma de la app", "Español"),
            section_label("Notificaciones"),
            settings_tile(ft.Icons.NOTIFICATIONS_ROUNDED, "Notificaciones", trailing=toggle_notif),
            section_label("App"),
            settings_tile(ft.Icons.INFO_OUTLINE_ROUNDED, "Versión", "1.0.0", trailing=ft.Text("1.0.0", size=12, color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE))),
            settings_tile(ft.Icons.HELP_OUTLINE_ROUNDED, "Ayuda y soporte"),
            settings_tile(ft.Icons.PRIVACY_TIP_OUTLINED, "Privacidad"),
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
        route="/config",
        controls=[main, nav_bar(page, active="config")],
        bgcolor="#0F0A1A",
        padding=0,
    )