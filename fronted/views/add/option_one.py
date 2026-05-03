import flet as ft

def option_one_view(page:ft.Page):

    #Botones del menu de navegacion 
    btn_play = ft.ElevatedButton("Click", on_click=lambda e: page.go("/"))
    btn_create = ft.ElevatedButton("Click", on_click=lambda e: page.go("/add"))
    btn_config = ft.ElevatedButton("Click", on_click=lambda e: page.go("/config"))

    #Botones principales:
    btn1 = ft.ElevatedButton("Subir pdf" )
    btn2 = ft.ElevatedButton("Subir cancion")
    btn3 = ft.ElevatedButton("Crear cancion")


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
                            ft.Text("Sube un archivo pdf (solo texto es reconocible)", size=20),
                            btn1,
                            ft.Text("Escojer melodia de fondo", size=20),
                            btn2,
                            btn3
                        ]
                    )
                )

    return ft.View(
        route="/option_one",
        controls=[ high_menu,
                   low_menu
                ]
    )
