import flet as ft


def option_two_view(page: ft.Page):

    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=16, bottom=4),
        content=ft.Row(
            controls=[
                ft.Container(
                    on_click=lambda e: page.go("/add"),
                    ink=True,
                    border_radius=ft.border_radius.all(10),
                    padding=ft.padding.all(8),
                    bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
                    content=ft.Icon(ft.Icons.ARROW_BACK_IOS_ROUNDED, color=ft.Colors.WHITE, size=18),
                ),
                ft.Container(width=12),
                ft.Column(
                    spacing=1,
                    controls=[
                        ft.Text("Texto libre", size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text("Escribe el contenido educativo", size=12, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                    ],
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    text_area = ft.TextField(
        multiline=True,
        min_lines=6,
        max_lines=10,
        hint_text="Escribe o pega aquí el texto educativo que quieres convertir en canción...",
        hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        border_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        focused_border_color="#7C3AED",
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border_radius=ft.border_radius.all(14),
        text_size=14,
    )

    char_count = ft.Text("0 caracteres", size=11, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE))

    def on_text_change(e):
        char_count.value = f"{len(text_area.value or '')} caracteres"
        page.update()

    text_area.on_change = on_text_change

    estilo_dropdown = ft.Dropdown(
        label="Estilo musical",
        value="pop",
        options=[
            ft.dropdown.Option("pop", "🎵 Pop educativo"),
            ft.dropdown.Option("rap", "🎤 Rap / Hip-hop"),
            ft.dropdown.Option("clasica", "🎼 Clásica"),
            ft.dropdown.Option("folk", "🪕 Folk / Acústico"),
        ],
        border_color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        focused_border_color="#DB2777",
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border_radius=ft.border_radius.all(12),
    )

    info_card = ft.Container(
        padding=ft.padding.all(14),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.with_opacity(0.08, "#DB2777"),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#DB2777")),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color="#F472B6", size=16),
                ft.Container(width=8),
                ft.Text(
                    "Esta función estará disponible próximamente.",
                    size=12,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                    expand=True,
                ),
            ]
        ),
    )

    btn_generar = ft.Container(
        border_radius=ft.border_radius.all(14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#DB2777", "#F59E0B"],
        ),
        padding=ft.padding.symmetric(vertical=14),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.WHITE, size=20),
                ft.Text("Generar canción", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700, size=14),
            ],
        ),
        opacity=0.5,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.3, "#DB2777"),
            offset=ft.Offset(0, 6),
        ),
    )

    body = ft.Column(
        controls=[
            header,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20),
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Container(height=4),
                        ft.Text("Contenido", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        text_area,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[char_count],
                        ),
                        ft.Text("Estilo", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        estilo_dropdown,
                        info_card,
                        btn_generar,
                        ft.Container(height=12),
                    ],
                ),
            ),
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
        route="/option_two",
        controls=[main],
        bgcolor="#0F0A1A",
        padding=0,
    )