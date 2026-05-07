import flet as ft

def home_view(page:ft.Page):
    
    btn_play = ft.ElevatedButton("Click", on_click=lambda e: page.go("/"))
    btn_create = ft.ElevatedButton("Click", on_click=lambda e: page.go("/add"))
    btn_config = ft.ElevatedButton("Click", on_click=lambda e: page.go("/config"))

    low_menu = ft.Row(
                    controls=[btn_play, btn_create, btn_config],
                    expand=10,
                    alignment=ft.MainAxisAlignment.CENTER
                    )
    high_menu = ft.Container(
                    content=ft.Text("Esta es la vista principal"),
                    alignment=ft.alignment.center,
                    expand=90,
                    width=float("inf")
                     )

    return ft.View(
        route="/",
        controls=[ high_menu,
                   low_menu
                ]
    )
