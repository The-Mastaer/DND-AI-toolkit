import flet as ft


class MainView(ft.View):
    """
    The main view of the application, which acts as a persistent shell.
    It contains the primary navigation rail and the main content area
    where other views are displayed. This view corresponds to the root route '/'.
    """

    def __init__(self, page: ft.Page):
        """
        Initializes the MainView.

        Args:
            page (ft.Page): The Flet page object for the application.
        """
        super().__init__()
        self.page = page
        self.route = "/"  # The root route

        # --- Navigation Rail ---
        # This is the primary navigation element on the left side of the app.
        # It allows the user to switch between the main sections of the toolkit.
        self.navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,  # Provides more space for labels if needed
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    # Corrected syntax: ft.icons -> ft.Icons
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationRailDestination(
                    # Corrected syntax: ft.icons -> ft.Icons
                    icon=ft.Icons.LANGUAGE_OUTLINED,
                    selected_icon=ft.Icons.LANGUAGE,
                    label="Worlds",
                ),
                ft.NavigationRailDestination(
                    # Corrected syntax: ft.icons -> ft.Icons
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self.nav_change,
        )

        # --- Main Content Area ---
        # This is the content displayed for the root route ('/').
        # When other views are pushed onto the stack (like WorldsView), they will
        # appear on top of this view, but the navigation rail will remain.
        self.main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Welcome to the D&D AI Toolkit!", style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Text(f"Signed in as: {self.page.session.get('user_name')}", italic=True),
                    ft.Text("Select an option from the left to get started.", style=ft.TextThemeStyle.BODY_LARGE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            expand=True,
            alignment=ft.alignment.center,
            padding=20,
        )

        # --- Assembling the View ---
        # The main layout is a Row containing the navigation rail and the content.
        self.controls = [
            ft.Row(
                [
                    self.navigation_rail,
                    ft.VerticalDivider(width=1),
                    self.main_content,
                ],
                expand=True,
            )
        ]

    def nav_change(self, e):
        """
        Handles navigation when a destination on the NavigationRail is selected.
        It updates the page's route, which triggers the route_change handler in main.py.

        Args:
            e (ft.ControlEvent): The event object from the navigation change.
        """
        index = e.control.selected_index
        if index == 0:
            self.page.go("/")
        elif index == 1:
            self.page.go("/worlds")
        elif index == 2:
            self.page.go("/settings")
        else:
            # Fallback to the home route if an unexpected index is received.
            self.page.go("/")

