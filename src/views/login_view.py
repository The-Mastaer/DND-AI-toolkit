# src/views/login_view.py

import flet as ft
import asyncio
import json
from ..services.supabase_service import supabase


class LoginView(ft.View):
    """
    A view for user sign-up and sign-in. This is the entry point for
    unauthenticated users.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/login"

        # --- UI Controls ---
        self.email_field = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
        self.password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
        self.error_text = ft.Text("", color=ft.Colors.RED)
        self.progress_ring = ft.ProgressRing(visible=False)

        # --- LAYOUT ---
        self.controls = [
            ft.Column(
                [
                    ft.Text("D&D AI Toolkit", style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Text("Please sign in or create an account."),
                    self.email_field,
                    self.password_field,
                    ft.Row(
                        [
                            ft.ElevatedButton("Sign In", on_click=self.signin_click),
                            ft.ElevatedButton("Sign Up", on_click=self.signup_click),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row([self.progress_ring, self.error_text], alignment=ft.MainAxisAlignment.CENTER)
                ],
                width=400,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        ]
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    async def signup_click(self, e):
        """Handles the sign-up button click."""
        self.show_progress(True)
        email = self.email_field.value
        password = self.password_field.value

        if not email or not password:
            self.show_error("Email and password cannot be empty.")
            self.show_progress(False)
            return

        try:
            await supabase.sign_up(email, password)
            self.show_error("Success! Please check your email for a confirmation link.", color=ft.Colors.GREEN)
        except Exception as ex:
            self.show_error(f"Sign-up failed: {ex}")
        finally:
            self.show_progress(False)

    async def signin_click(self, e):
        """Handles the sign-in button click."""
        self.show_progress(True)
        email = self.email_field.value
        password = self.password_field.value

        if not email or not password:
            self.show_error("Email and password cannot be empty.")
            self.show_progress(False)
            return

        try:
            session_response = await supabase.sign_in_with_password(email, password)
            if session_response and session_response.session:
                print("Sign-in successful, saving session and navigating to home.")
                # *** FIX: Save session to client storage for persistence ***
                session_data = {
                    "access_token": session_response.session.access_token,
                    "refresh_token": session_response.session.refresh_token,
                }
                await asyncio.to_thread(
                    self.page.client_storage.set, "supabase.session", json.dumps(session_data)
                )
                self.page.go("/")
            else:
                self.show_error("Sign-in failed. Please check your credentials.")
        except Exception as ex:
            self.show_error(f"Sign-in error: {ex}")
        finally:
            self.show_progress(False)

    def show_error(self, message, color=ft.Colors.RED):
        """Displays an error message to the user."""
        self.error_text.value = message
        self.error_text.color = color
        self.update()

    def show_progress(self, visible: bool):
        """Shows or hides the progress ring."""
        self.progress_ring.visible = visible
        self.update()
