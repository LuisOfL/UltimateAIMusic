import flet as ft
from views.menu.splashscreen import splash_view
from views.menu.home import home_view
from views.options.add import add_view
from views.options.config import config_view
from views.add.option_one import option_one_view
from views.add.option_two import option_two_view
from views.add.option_three import option_three_view
from views.login.login import login_view
from views.login.profile import profile_view
import time


def main(page: ft.Page):
    page.title = "EduSong"
    page.bgcolor = "#0F0A1A"

    def route_change(e):
        # 1. Limpiamos por completo la caché de vistas previas
        page.views.clear()

        # 2. Re-evaluamos las vistas dinámicamente en cada salto
        if page.route == "/splash_screen":
            page.views.append(splash_view())
            page.update()
            time.sleep(2)
            page.go("/")

        elif page.route == "/":
            page.views.append(home_view(page))

        elif page.route == "/add":
            page.views.append(add_view(page))

        elif page.route == "/profile":
            page.views.append(profile_view(page))

        elif page.route == "/login":
            page.views.append(login_view(page))

        elif page.route == "/config":
            page.views.append(config_view(page))
        
        elif page.route == "/option_one":
            page.views.append(option_one_view(page))

        elif page.route == "/option_two":
            page.views.append(option_two_view(page))

        elif page.route == "/option_three":
            page.views.append(option_three_view(page))

        else:
            page.views.append(
                ft.View(
                    route="/404",
                    controls=[ft.Text("404 - No encontrado", color=ft.Colors.WHITE)]
                )
            )
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go("/splash_screen")

ft.app(target=main)