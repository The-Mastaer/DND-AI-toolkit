# src/views/login_view.py

import flet as ft
from services.supabase_service import supabase
import asyncio
import json


class LoginView(ft.View):
    """
    The view for user login and registration.
    This view is displayed when the user is not authenticated.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/login"
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.vertical_alignment = ft.MainAxisAlignment.CENTER

        self.email_input = ft.TextField(label="Email", autofocus=True, width=300)
        self.password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        self.status_text = ft.Text(value="", color=ft.Colors.RED)

        self.controls = [
            ft.Column(
                [
                    ft.Text("D&D AI Toolkit", style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Text("Please sign in or register to continue"),
                    self.email_input,
                    self.password_input,
                    ft.Row(
                        [
                            ft.ElevatedButton("Sign In", on_click=self.login_clicked),
                            ft.OutlinedButton("Register", on_click=self.register_clicked),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.status_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        ]

    async def login_clicked(self, e):
        """
        Handles the login button click event.
        """
        email = self.email_input.value
        password = self.password_input.value

        if not email or not password:
            self.status_text.value = "Email and password are required."
            self.update()
            return

        try:
            session_response = await supabase.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            # --- START: Diagnostic Print Statements ---
            print("--- Login Successful from Supabase ---")
            # 1. Print the raw session object to see its structure
            print(f"Session object received: {session_response}")

            # Save session to client storage for persistence
            session_json = session_response.model_dump_json()
            # 2. Print the JSON string that will be stored
            print(f"Serialized session JSON to be stored: {session_json}")

            await asyncio.to_thread(self.page.client_storage.set, "supabase.session", session_json)
            # 3. Confirm the save operation was called
            print("--- Session JSON has been sent to client storage. ---")
            # --- END: Diagnostic Print Statements ---

            self.status_text.value = ""
            self.page.go("/")
        except Exception as ex:
            self.status_text.value = f"Login failed: {ex}"
            self.update()

    async def register_clicked(self, e):
        """
        Handles the register button click event.
        """
        email = self.email_input.value
        password = self.password_input.value

        if not email or not password:
            self.status_text.value = "Email and password are required."
            self.update()
            return

        try:
            await supabase.client.auth.sign_up({
                "email": email,
                "password": password
            })
            self.status_text.value = "Registration successful! Please check your email to verify."
            self.status_text.color = ft.Colors.GREEN
        except Exception as ex:
            self.status_text.value = f"Registration failed: {ex}"
            self.status_text.color = ft.Colors.RED
        self.update()