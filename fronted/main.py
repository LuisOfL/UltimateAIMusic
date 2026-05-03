import flet as ft
from home import home_view
from components.create import about_view

def main(page: ft.Page):

    def route_change(e):
        page.views.clear()

        if page.route == "/":
            page.views.append(home_view(page))

        elif page.route == "/about":
            page.views.append(about_view(page))

        else:
            page.views.append(
                ft.View(
                    route="/404",
                    controls=[ft.Text("404 - No encontrado")]
                )
            )

        page.update()

    def view_pop(e):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/")  # inicial

ft.app(target=main)