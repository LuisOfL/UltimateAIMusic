import flet as ft

"""
Esta es la pantalla de carga que se pone cuando inicia la app
"""
def splash_view():
        
    main = ft.Container(
        expand=True,
        width=float("inf"),
        alignment=ft.alignment.center,  # 👈 centra todo
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Mi App", size=30, weight="bold"),
                ft.ProgressRing()
            ]
        )
    )

    return ft.View(
        route="/splash_screen",
        controls=[main]
    )