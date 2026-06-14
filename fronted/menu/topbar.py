import flet as ft

"""
Componente compartido: barra superior
"""

def top_bar(page: ft.Page):

    return ft.Container(
        padding=ft.padding.only(left=20, right=20, top=15, bottom=10),
        bgcolor=ft.Colors.with_opacity(0.85, "#0F0A1A"),
        border=ft.border.only(
            bottom=ft.BorderSide(
                1,
                ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
            )
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    "SealMusic",
                    size=20,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.WHITE,
                ),
                ft.TextButton(
                    "Iniciar sesión",
                    on_click=lambda e: page.go("/login"),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        ),
    )