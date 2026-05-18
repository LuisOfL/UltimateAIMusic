import flet as ft

"""
Componente compartido: barra de navegación inferior
"""

def nav_bar(page: ft.Page, active: str = "home"):

    def nav_btn(icon_active, icon_default, label, route, key):
        is_active = active == key
        return ft.Container(
            on_click=lambda e: page.go(route),
            ink=True,
            border_radius=ft.border_radius.all(14),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.Colors.with_opacity(0.15, "#7C3AED") if is_active else ft.Colors.TRANSPARENT,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    ft.Icon(
                        icon_active if is_active else icon_default,
                        color="#06B6D4" if is_active else ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                        size=22,
                    ),
                    ft.Text(
                        label,
                        size=10,
                        color="#06B6D4" if is_active else ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
            ),
        )

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.Colors.with_opacity(0.85, "#0F0A1A"),
        border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE))),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=[
                nav_btn(ft.Icons.HOME_ROUNDED, ft.Icons.HOME_OUTLINED, "Inicio", "/", "home"),
                nav_btn(ft.Icons.ADD_CIRCLE_ROUNDED, ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, "Crear", "/add", "add"),
                nav_btn(ft.Icons.SETTINGS_ROUNDED, ft.Icons.SETTINGS_OUTLINED, "Ajustes", "/config", "config"),
            ],
        ),
    )