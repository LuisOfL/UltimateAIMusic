import flet as ft
from views.menu.navbar import nav_bar

def profile_view(page: ft.Page):
    # Recuperamos los datos que guardamos localmente al iniciar sesión
    username = page.client_storage.get("username") or "Usuario"
    email = page.client_storage.get("email") or "correo@ejemplo.com"
    country = page.client_storage.get("country") or "No especificado"

    header = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=40, bottom=8),
        content=ft.Text("Perfil", size=32, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
    )

    # Tarjeta de presentación superior
    profile_card = ft.Container(
        margin=ft.margin.symmetric(horizontal=20, vertical=10),
        padding=ft.padding.all(20),
        border_radius=ft.border_radius.all(20),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1E1B4B", "#0F172A"],
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        content=ft.Row(
            spacing=16,
            controls=[
                ft.Container(
                    width=64,
                    height=64,
                    border_radius=ft.border_radius.all(32),
                    gradient=ft.LinearGradient(
                        colors=["#7C3AED", "#06B6D4"]
                    ),
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        username[0].upper() if username else "U",
                        size=24,
                        weight=ft.FontWeight.W_700,
                        color=ft.Colors.WHITE,
                    )
                ),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(username, size=20, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                            ft.Text(email, size=13, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                        ]
                    )
                )
            ]
        )
    )

    def info_tile(icon, label, value):
        return ft.Container(
            margin=ft.margin.symmetric(horizontal=20, vertical=4),
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(14),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icon, color="#06B6D4", size=20),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(label, size=11, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                            ft.Text(value, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                        ]
                    )
                ]
            )
        )

    # Función para destruir la sesión activa
    def logout(e):
        page.client_storage.remove("cognito_id")
        page.client_storage.remove("username")
        page.client_storage.remove("email")
        page.client_storage.remove("country")
        
        page.open(
            ft.SnackBar(
                content=ft.Text("Sesión cerrada correctamente. Volviendo al inicio..."),
                bgcolor="#7C3AED"
            )
        )
        page.go("/") # Redirige al inicio y la barra superior se actualizará sola

    btn_logout = ft.Container(
        margin=ft.margin.symmetric(horizontal=20, vertical=20),
        content=ft.ElevatedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=18),
                    ft.Text("Cerrar Sesión", weight=ft.FontWeight.W_600)
                ]
            ),
            on_click=logout,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor="#DC2626",
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(vertical=14)
            )
        )
    )

    body = ft.Column(
        controls=[
            header,
            profile_card,
            ft.Container(height=10),
            ft.Container(
                padding=ft.padding.only(left=24, bottom=8),
                content=ft.Text("DETALLES DE LA CUENTA", size=11, weight=ft.FontWeight.W_700, color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE))
            ),
            info_tile(ft.Icons.PUBLIC_ROUNDED, "Región / País", country),
            info_tile(ft.Icons.VERIFIED_USER_ROUNDED, "Estado de cuenta", "Verificado vía Cognito"),
            btn_logout,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    main = ft.Container(
        content=body,
        expand=True,
        bgcolor="#0F0A1A",
    )

    return ft.View(
        route="/profile",
        controls=[main, nav_bar(page, active="home")], # Mantiene la barra de navegación activa
        bgcolor="#0F0A1A",
        padding=0,
    )