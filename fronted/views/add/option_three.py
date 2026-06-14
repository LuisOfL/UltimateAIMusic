import flet as ft


def option_three_view(page: ft.Page):

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
                        ft.Text("Grabación de voz", size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text("Graba y transforma en canción", size=12, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                    ],
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # Visualizador de onda decorativo
    wave_viz = ft.Container(
        height=80,
        border_radius=ft.border_radius.all(16),
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            controls=[
                ft.Container(
                    width=3,
                    height=h,
                    border_radius=ft.border_radius.all(2),
                    bgcolor=ft.Colors.with_opacity(0.2 + (i % 5) * 0.07, "#059669"),
                )
                for i, h in enumerate([10, 18, 30, 22, 40, 28, 50, 34, 42, 20, 36, 26, 48, 32, 24, 38, 16, 44, 28, 20])
            ],
        ),
    )

    recording_label = ft.Text(
        "Listo para grabar",
        size=13,
        color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
        text_align=ft.TextAlign.CENTER,
    )

    timer_text = ft.Text(
        "00:00",
        size=42,
        weight=ft.FontWeight.W_300,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    btn_record = ft.Container(
        width=80,
        height=80,
        border_radius=ft.border_radius.all(40),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#059669", "#0891B2"],
        ),
        shadow=ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.5, "#059669"),
            offset=ft.Offset(0, 8),
        ),
        content=ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.WHITE, size=36),
        alignment=ft.alignment.center,
        ink=True,
    )

    info_card = ft.Container(
        padding=ft.padding.all(14),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.with_opacity(0.08, "#059669"),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#059669")),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color="#34D399", size=16),
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

    tips = ft.Container(
        padding=ft.padding.all(16),
        border_radius=ft.border_radius.all(16),
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Consejos para mejores resultados", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                *[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color="#34D399", size=15),
                            ft.Text(tip, size=12, color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE), expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                    for tip in [
                        "Habla con claridad y a velocidad moderada",
                        "Usa un ambiente silencioso",
                        "Explica el tema como si fuera a un estudiante",
                    ]
                ],
            ],
        ),
    )

    body = ft.Column(
        controls=[
            header,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=20),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Container(height=8),
                        wave_viz,
                        timer_text,
                        recording_label,
                        btn_record,
                        ft.Container(height=4),
                        info_card,
                        tips,
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
        route="/option_three",
        controls=[main],
        bgcolor="#0F0A1A",
        padding=0,
    )