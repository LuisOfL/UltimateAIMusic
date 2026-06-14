import flet as ft
from views.menu.navbar import nav_bar

def add_view(page: ft.Page):
    # Verificamos si el usuario está logueado leyendo el almacenamiento local
    is_logged_in = page.client_storage.get("cognito_id") is not None

    header = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=40, bottom=8),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text("Crear", size=32, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                ft.Text(
                    "Elige cómo generar tu canción" if is_logged_in else "Inicia sesión para desbloquear las herramientas",
                    size=14,
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE) if is_logged_in else "#F87171",
                ),
            ],
        ),
    )

    # Estructura de la tarjeta que soporta el estado visual "Desactivado"
    def option_card(icon, title, subtitle, route, gradient_colors, accent):
        
        # DEFINICIÓN DE ESTILOS DINÁMICOS (Si está logueado vs si está bloqueado)
        if is_logged_in:
            card_bgcolor = ft.Colors.with_opacity(0.06, ft.Colors.WHITE)
            card_opacity = 1.0
            icon_gradient = ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=gradient_colors,
            )
            card_shadow = ft.BoxShadow(
                blur_radius=16,
                color=ft.Colors.with_opacity(0.25, accent),
                offset=ft.Offset(0, 8),
            )
            # Comportamiento normal: navega al endpoint correspondiente
            on_click_action = lambda e: page.go(route)
            trailing_icon = ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), size=14)
        else:
            # Estado Desactivado (Bonito y traslúcido)
            card_bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
            card_opacity = 0.4  # Aplica el efecto de "apagado" general
            icon_gradient = ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#374151", "#1F2937"], # Colores grisáceos oscuros
            )
            card_shadow = None # Sin resplandor de color activo
            # Acción preventiva: Avisa que requiere login
            on_click_action = lambda e: page.open(
                ft.SnackBar(
                    content=ft.Text("🔒 Esta función requiere iniciar sesión. Ve a 'Inicio' o al menú superior."),
                    bgcolor="#7C3AED"
                )
            )
            # Candado indicativo de bloqueo
            trailing_icon = ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE), size=16)

        return ft.Container(
            margin=ft.margin.symmetric(horizontal=20),
            on_click=on_click_action,
            ink=is_logged_in, # El efecto ripple solo funciona si está desbloqueado
            opacity=card_opacity,
            border_radius=ft.border_radius.all(20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE) if is_logged_in else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            bgcolor=card_bgcolor,
            shadow=card_shadow,
            padding=ft.padding.all(20),
            content=ft.Row(
                spacing=16,
                controls=[
                    ft.Container(
                        width=52,
                        height=52,
                        border_radius=ft.border_radius.all(16),
                        gradient=icon_gradient,
                        content=ft.Icon(icon, color=ft.Colors.WHITE if is_logged_in else ft.Colors.with_opacity(0.4, ft.Colors.WHITE), size=24),
                    ),
                    # AQUÍ SE CORRIGIÓ: Usamos Container con expand=True en lugar de ft.Expanded()
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                                ft.Text(subtitle, size=12, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                            ],
                        )
                    ),
                    trailing_icon,
                ],
            ),
        )

    badge_new = ft.Container(
        margin=ft.margin.only(left=24),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=ft.border_radius.all(8),
        bgcolor=ft.Colors.with_opacity(0.1, "#06B6D4") if is_logged_in else ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        content=ft.Text(
            "MÉTODOS IA" if is_logged_in else "BLOQUEADO", 
            size=10, 
            color="#06B6D4" if is_logged_in else ft.Colors.with_opacity(0.4, ft.Colors.WHITE), 
            weight=ft.FontWeight.W_800
        ),
    )

    body = ft.Column(
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
        content=body,
        expand=True,
        bgcolor="#0F0A1A",
    )

    return ft.View(
        route="/add",
        controls=[main, nav_bar(page, active="add")],
        bgcolor="#0F0A1A",
        padding=0,
    )