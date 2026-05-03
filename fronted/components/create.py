import flet as ft

def about_view(page: ft.Page):
    return ft.View(
        route="/about",
        controls=[
            ft.Text("About"),
            ft.ElevatedButton(
                "Regresar",
                on_click=lambda e: page.go("/")
            )
        ]
    )