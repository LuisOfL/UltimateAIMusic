import flet as ft
import datetime
import httpx

"""
Vista de inicio de sesión / registro.
Registro con confirmación automática (sin verificación por correo).

Endpoints:
  POST /login    {"email", "password"}
  POST /register {"email","password","username","birthdate","country","state"}
"""

API_BASE_URL = "http://127.0.0.1:8000"


def login_view(page: ft.Page):

    state = {"is_login": True, "loading": False}

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def show_snack(message, error=False):
        page.open(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor="#DC2626" if error else "#059669",
            )
        )

    def set_loading(is_loading: bool):
        state["loading"]        = is_loading
        submit_spinner.visible  = is_loading
        submit_btn_text.visible = not is_loading
        submit_btn.disabled     = is_loading
        submit_btn.opacity      = 0.6 if is_loading else 1
        page.update()

    def styled_field(label, icon, password=False, hint=None):
        return ft.TextField(
            label=label,
            hint_text=hint,
            password=password,
            can_reveal_password=password,
            prefix_icon=icon,
            label_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            focused_border_color="#7C3AED",
            border_radius=ft.border_radius.all(14),
            text_size=14,
        )

    # ------------------------------------------------------------------ #
    #  ENCABEZADO                                                          #
    # ------------------------------------------------------------------ #

    back_btn = ft.Container(
        on_click=lambda e: page.go("/"),
        ink=True,
        border_radius=ft.border_radius.all(10),
        padding=ft.padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
        content=ft.Icon(ft.Icons.ARROW_BACK_IOS_ROUNDED, color=ft.Colors.WHITE, size=18),
    )

    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=16, bottom=4),
        content=ft.Row(controls=[back_btn]),
    )

    logo_icon = ft.Container(
        width=72,
        height=72,
        border_radius=ft.border_radius.all(22),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#7C3AED", "#06B6D4"],
        ),
        content=ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=36, color=ft.Colors.WHITE),
        shadow=ft.BoxShadow(
            blur_radius=24,
            color=ft.Colors.with_opacity(0.4, "#7C3AED"),
            offset=ft.Offset(0, 6),
        ),
        alignment=ft.alignment.center,
    )

    title_text = ft.Text(
        "Bienvenido de nuevo",
        size=24,
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    subtitle_text = ft.Text(
        "Inicia sesión para continuar",
        size=13,
        color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
        text_align=ft.TextAlign.CENTER,
    )

    # ------------------------------------------------------------------ #
    #  TABS                                                                #
    # ------------------------------------------------------------------ #

    tab_login = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(vertical=10),
        border_radius=ft.border_radius.all(12),
        alignment=ft.alignment.center,
        content=ft.Text("Iniciar sesión", size=13, weight=ft.FontWeight.W_700),
    )

    tab_register = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(vertical=10),
        border_radius=ft.border_radius.all(12),
        alignment=ft.alignment.center,
        content=ft.Text("Registrarse", size=13, weight=ft.FontWeight.W_700),
    )

    tabs_switcher = ft.Container(
        margin=ft.margin.symmetric(horizontal=20),
        padding=ft.padding.all(4),
        border_radius=ft.border_radius.all(16),
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        content=ft.Row(controls=[tab_login, tab_register], spacing=4),
    )

    # ------------------------------------------------------------------ #
    #  FORMULARIO LOGIN                                                    #
    # ------------------------------------------------------------------ #

    login_email_field    = styled_field("Correo electrónico", ft.Icons.EMAIL_OUTLINED)
    login_password_field = styled_field("Contraseña", ft.Icons.LOCK_OUTLINE_ROUNDED, password=True)

    login_form = ft.Column(
        spacing=14,
        controls=[
            login_email_field,
            login_password_field,
            ft.Container(
                alignment=ft.alignment.center_right,
                content=ft.TextButton(
                    "¿Olvidaste tu contraseña?",
                    style=ft.ButtonStyle(color="#06B6D4"),
                    on_click=lambda e: show_snack("Función disponible próximamente"),
                ),
            ),
        ],
    )

    # ------------------------------------------------------------------ #
    #  FORMULARIO REGISTRO                                                 #
    # ------------------------------------------------------------------ #

    register_username_field = styled_field("Nombre de usuario", ft.Icons.PERSON_OUTLINE_ROUNDED)
    register_email_field    = styled_field("Correo electrónico", ft.Icons.EMAIL_OUTLINED)

    birthdate_field = styled_field("Fecha de nacimiento", ft.Icons.CALENDAR_MONTH_ROUNDED, hint="DD/MM/AAAA")
    birthdate_field.read_only = True
    birthdate_iso = {"value": None}

    def on_date_change(e):
        if date_picker.value:
            birthdate_iso["value"] = date_picker.value.strftime("%Y-%m-%d")
            birthdate_field.value  = date_picker.value.strftime("%d/%m/%Y")
            page.update()

    date_picker = ft.DatePicker(
        first_date=datetime.date(1920, 1, 1),
        last_date=datetime.date.today(),
        on_change=on_date_change,
    )
    page.overlay.append(date_picker)
    birthdate_field.on_click = lambda e: (setattr(date_picker, "open", True), page.update())

    countries = [
        "Argentina","Bolivia","Chile","Colombia","Costa Rica","Cuba","Ecuador",
        "El Salvador","España","Estados Unidos","Guatemala","Honduras","México",
        "Nicaragua","Panamá","Paraguay","Perú","Puerto Rico","República Dominicana",
        "Uruguay","Venezuela","Otro",
    ]

    country_dropdown = ft.Dropdown(
        label="País",
        prefix_icon=ft.Icons.PUBLIC_ROUNDED,
        options=[ft.dropdown.Option(c) for c in countries],
        label_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        focused_border_color="#7C3AED",
        border_radius=ft.border_radius.all(14),
    )

    state_field             = styled_field("Estado / Provincia", ft.Icons.LOCATION_ON_OUTLINED)
    register_password_field = styled_field("Contraseña", ft.Icons.LOCK_OUTLINE_ROUNDED, password=True)
    register_confirm_field  = styled_field("Confirmar contraseña", ft.Icons.LOCK_OUTLINE_ROUNDED, password=True)

    # Info de requisitos de contraseña
    password_hint = ft.Container(
        padding=ft.padding.symmetric(horizontal=4),
        content=ft.Text(
            "Mín. 8 caracteres, una mayúscula, un número y un símbolo (ej: EduSong1!)",
            size=11,
            color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
        ),
    )

    register_form = ft.Column(
        spacing=14,
        visible=False,
        controls=[
            register_username_field,
            register_email_field,
            birthdate_field,
            country_dropdown,
            state_field,
            register_password_field,
            password_hint,
            register_confirm_field,
        ],
    )

    # ------------------------------------------------------------------ #
    #  BOTÓN PRINCIPAL                                                     #
    # ------------------------------------------------------------------ #

    submit_btn_text = ft.Text("Iniciar sesión", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700, size=14)
    submit_spinner  = ft.ProgressRing(width=18, height=18, stroke_width=2, color=ft.Colors.WHITE, visible=False)

    submit_btn = ft.Container(
        ink=True,
        border_radius=ft.border_radius.all(14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#7C3AED", "#06B6D4"],
        ),
        padding=ft.padding.symmetric(vertical=14),
        alignment=ft.alignment.center,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[submit_spinner, submit_btn_text],
        ),
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.3, "#7C3AED"),
            offset=ft.Offset(0, 6),
        ),
    )

    # ------------------------------------------------------------------ #
    #  TEXTO INFERIOR                                                      #
    # ------------------------------------------------------------------ #

    switch_text = ft.Text("¿No tienes cuenta?", size=12, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE))
    switch_link = ft.TextButton("Regístrate", style=ft.ButtonStyle(color="#06B6D4"))

    switch_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        controls=[switch_text, switch_link],
    )

    # ------------------------------------------------------------------ #
    #  LÓGICA DE SUBMIT                                                    #
    # ------------------------------------------------------------------ #

    async def on_submit(e):
        if state["loading"]:
            return

        # -- LOGIN --
        if state["is_login"]:
            email    = (login_email_field.value or "").strip()
            password = login_password_field.value or ""

            if not email or not password:
                show_snack("Completa correo y contraseña", error=True)
                return

            set_loading(True)
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        f"{API_BASE_URL}/login",
                        json={"email": email, "password": password},
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        page.client_storage.set("access_token",  data.get("AccessToken",  ""))
                        page.client_storage.set("id_token",      data.get("IdToken",       ""))
                        page.client_storage.set("refresh_token", data.get("RefreshToken",  ""))
                    except Exception:
                        pass
                    show_snack("Inicio de sesión exitoso")
                    page.go("/")
                else:
                    detail = "Correo o contraseña incorrectos"
                    try:
                        detail = resp.json().get("detail", detail)
                    except Exception:
                        pass
                    show_snack(detail, error=True)

            except httpx.RequestError:
                show_snack("No se pudo conectar con el servidor", error=True)
            finally:
                set_loading(False)

        # -- REGISTRO --
        else:
            username    = (register_username_field.value or "").strip()
            email       = (register_email_field.value    or "").strip()
            password    = register_password_field.value  or ""
            confirm     = register_confirm_field.value   or ""
            country     = country_dropdown.value
            state_value = (state_field.value or "").strip()

            if not all([username, email, birthdate_iso["value"], country, state_value, password, confirm]):
                show_snack("Completa todos los campos", error=True)
                return
            if "@" not in email or "." not in email:
                show_snack("Ingresa un correo válido", error=True)
                return
            if password != confirm:
                show_snack("Las contraseñas no coinciden", error=True)
                return

            set_loading(True)
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        f"{API_BASE_URL}/register",
                        json={
                            "email":     email,
                            "password":  password,
                            "username":  username,
                            "birthdate": birthdate_iso["value"],
                            "country":   country,
                            "state":     state_value,
                        },
                    )

                if resp.status_code == 200:
                    show_snack("¡Cuenta creada! Ahora inicia sesión")
                    set_mode(True)
                    login_email_field.value = email
                    page.update()
                else:
                    detail = "No se pudo completar el registro"
                    try:
                        detail = resp.json().get("detail", detail)
                    except Exception:
                        pass
                    show_snack(detail, error=True)

            except httpx.RequestError:
                show_snack("No se pudo conectar con el servidor", error=True)
            finally:
                set_loading(False)

    submit_btn.on_click = on_submit

    # ------------------------------------------------------------------ #
    #  CAMBIO DE MODO                                                      #
    # ------------------------------------------------------------------ #

    def set_mode(is_login: bool):
        state["is_login"]      = is_login
        login_form.visible     = is_login
        register_form.visible  = not is_login

        if is_login:
            tab_login.bgcolor          = ft.Colors.with_opacity(0.15, "#7C3AED")
            tab_login.content.color    = "#06B6D4"
            tab_register.bgcolor       = ft.Colors.TRANSPARENT
            tab_register.content.color = ft.Colors.with_opacity(0.5, ft.Colors.WHITE)
            title_text.value           = "Bienvenido de nuevo"
            subtitle_text.value        = "Inicia sesión para continuar"
            submit_btn_text.value      = "Iniciar sesión"
            switch_text.value          = "¿No tienes cuenta?"
            switch_link.text           = "Regístrate"
        else:
            tab_register.bgcolor       = ft.Colors.with_opacity(0.15, "#7C3AED")
            tab_register.content.color = "#06B6D4"
            tab_login.bgcolor          = ft.Colors.TRANSPARENT
            tab_login.content.color    = ft.Colors.with_opacity(0.5, ft.Colors.WHITE)
            title_text.value           = "Crea tu cuenta"
            subtitle_text.value        = "Regístrate para empezar a crear canciones"
            submit_btn_text.value      = "Crear cuenta"
            switch_text.value          = "¿Ya tienes cuenta?"
            switch_link.text           = "Inicia sesión"

        page.update()

    tab_login.on_click    = lambda e: set_mode(True)
    tab_register.on_click = lambda e: set_mode(False)
    switch_link.on_click  = lambda e: set_mode(not state["is_login"])

    set_mode(True)

    # ------------------------------------------------------------------ #
    #  LAYOUT                                                              #
    # ------------------------------------------------------------------ #

    body = ft.Column(
        controls=[
            header,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=24),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Container(height=8),
                        logo_icon,
                        ft.Container(height=8),
                        title_text,
                        subtitle_text,
                        ft.Container(height=16),
                    ],
                ),
            ),
            tabs_switcher,
            ft.Container(height=20),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=24),
                content=ft.Column(
                    spacing=18,
                    controls=[
                        login_form,
                        register_form,
                        submit_btn,
                        ft.Container(height=4),
                        switch_row,
                        ft.Container(height=20),
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
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#0F0A1A", "#0A0F1A", "#0F0A1A"],
        ),
    )

    return ft.View(
        route="/login",
        controls=[main],
        bgcolor="#0F0A1A",
        padding=0,
    )