import flet as ft

""" 
Este archivo es el que se usa para añadir canciones
DE MOMENTO NO HAY BACK
"""
def add_view(page:ft.Page):

    #Botones del menu inferior
    btn_play = ft.ElevatedButton("Click", on_click=lambda e: page.go("/"))
    btn_create = ft.ElevatedButton("Click", on_click=lambda e: page.go("/add"))
    btn_config = ft.ElevatedButton("Click", on_click=lambda e: page.go("/config"))

    #Botones principales:
    btn1 = ft.ElevatedButton("Botón 1", on_click=lambda e: page.go("/option_one"))
    btn2 = ft.ElevatedButton("Botón 2", on_click=lambda e: page.go("/option_two"))
    btn3 = ft.ElevatedButton("Botón 3", on_click=lambda e: page.go("/option_three"))

    low_menu = ft.Row(
                    controls=[btn_play, btn_create, btn_config],
                    expand=10,
                    alignment=ft.MainAxisAlignment.CENTER
                    )
    high_menu = ft.Container(
                    alignment=ft.alignment.center,
                    expand=90,
                    width=float("inf"),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Text("Crear una nueva canción", size=24),
                            btn1,
                            btn2,
                            btn3
                        ]
                    )
                )

    return ft.View(
        route="/add",
        controls=[ high_menu,
                   low_menu
                ]
    )
