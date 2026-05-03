import flet as ft

def home_view(page: ft.Page):
    return ft.View(
        route="/",
        controls=[
            ft.Text("Home"),
            ft.ElevatedButton(
                "Ir a About",
                on_click=lambda e: page.go("/about")
            )
        ]
    )