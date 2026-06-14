import flet as ft

"""
Componente compartido: barra superior dinámica basada en sesión
"""

def top_bar(page: ft.Page):
    # Verificamos si hay un usuario logueado en el almacenamiento local
    usuario_logeado = page.client_storage.get("cognito_id")

    if usuario_logeado:
        # Si está logueado, muestra un botón elegante hacia su perfil
        boton_sesion = ft.TextButton(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, color="#06B6D4", size=20),
                    ft.Text("Mi Perfil", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.W_600),
                ]
            ),
            on_click=lambda e: page.go("/profile"), # Redirige a la vista de perfil
        )
    else:
        # Si es un invitado, muestra el botón clásico de inicio de sesión
        boton_sesion = ft.TextButton(
            "Iniciar sesión",
            on_click=lambda e: page.go("/login"),
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
            ),
        )

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
                boton_sesion, # Renderizado dinámico según el estado de la sesión
            ],
        ),
    )