# src/views/main_view.py

import flet as ft
import asyncio

from services.supabase_service import supabase
from services.gemini_service import GeminiService
from prompts import SRD_QUERY_PROMPT
from config import DEFAULT_TEXT_MODEL, GEMINI_SRD_FILE_NAME


class MainView(ft.View):
    """
    The main view of the application, which acts as a persistent shell.
    It contains the primary navigation rail and the main content area,
    which now features the core AI chatbot interface. This view corresponds to the root route '/'.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService):
        """
        Initializes the MainView.

        Args:
            page (ft.Page): The Flet page object for the application.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
        """
        super().__init__()
        self.page = page
        self.route = "/"
        self.gemini_service = gemini_service

        # --- State Management ---
        self.lore_chat_session = None
        self.gemini_srd_file_uri: str | None = None

        # --- Control Management ---
        self.chat_controls = {}

        # --- Navigation Rail ---
        self.navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.BOOK_ONLINE_OUTLINED,
                    selected_icon=ft.Icons.BOOK_ONLINE,
                    label="Worlds",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PEOPLE_OUTLINE,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Characters",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self.nav_change,
        )

        # --- Main Content Area with Tabs ---
        self.main_content = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_change=self.tabs_changed,
            tabs=[
                ft.Tab(
                    text="Lore Master",
                    icon=ft.Icons.MENU_BOOK_ROUNDED,
                    content=self.build_chat_view(key="lore", hint_text="Ask the Lore Master..."),
                ),
                ft.Tab(
                    text="Rules Lawyer",
                    icon=ft.Icons.GAVEL_ROUNDED,
                    content=self.build_chat_view(key="rules", hint_text="Ask the Rules Lawyer..."),
                ),
            ],
            expand=True,
        )

        # --- Assembling the Full View ---
        self.controls = [
            ft.Row(
                [
                    self.navigation_rail,
                    ft.VerticalDivider(width=1),
                    ft.Column([self.main_content], expand=True)
                ],
                expand=True,
            )
        ]

    def build_chat_view(self, key: str, hint_text: str):
        """Builds a UNIQUE and self-contained chat interface for a tab."""
        # Create NEW instances of all controls for this tab.
        chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        user_input = ft.TextField(
            hint_text=hint_text,
            expand=True,
            on_submit=self.send_message_click,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
        )
        send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Send Message",
            on_click=self.send_message_click,
        )
        chat_progress = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False)

        # Store these new, unique controls in our dictionary.
        self.chat_controls[key] = {
            "input": user_input,
            "button": send_button,
            "progress": chat_progress,
            "history": chat_history,
        }

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([chat_progress]),
                    chat_history,
                    ft.Row(controls=[user_input, send_button]),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    def did_mount(self):
        """Initializes the view when it's added to the page."""
        # Load the context for the initially selected tab (Lore Master)
        self.page.run_task(self.initialize_lore_master)

    def nav_change(self, e):
        """Handles navigation when a destination on the NavigationRail is selected."""
        index = e.control.selected_index
        if index == 0:
            self.page.go("/")
        elif index == 1:
            self.page.go("/worlds")
        elif index == 2:
            self.page.go("/characters")
        elif index == 3:
            self.page.go("/settings")

    def tabs_changed(self, e):
        """Handles switching between Lore Master and Rules Lawyer tabs."""
        selected_index = e.control.selected_index
        if selected_index == 0:  # Lore Master
            self.page.run_task(self.initialize_lore_master)
        else:  # Rules Lawyer
            if not self.gemini_srd_file_uri:
                self.page.run_task(self.initialize_rules_lawyer)
        # The update call can remain, it doesn't hurt.
        self.update()

    async def initialize_lore_master(self):
        """Sets up the Lore Master chat, loading context from the database."""
        lore_controls = self.chat_controls["lore"]
        lore_history = lore_controls["history"]
        lore_history.controls.clear()
        lore_history.controls.append(ft.Text("Loading campaign context...", italic=True))
        self.update()

        keys_to_fetch = ["active_language_code", "active_world_id", "active_campaign_id", "ai.model"]
        tasks = [asyncio.to_thread(self.page.client_storage.get, key) for key in keys_to_fetch]
        results = await asyncio.gather(*tasks)
        settings = dict(zip(keys_to_fetch, results))

        lang_code = settings.get("active_language_code") or "en"
        world_id = settings.get("active_world_id")
        campaign_id = settings.get("active_campaign_id")
        model_name = settings.get("ai.model") or DEFAULT_TEXT_MODEL

        if not world_id or not campaign_id:
            lore_history.controls.clear()
            lore_history.controls.append(
                ft.Text("No active world or campaign selected in Settings.", color=ft.Colors.RED))
            self.update()
            return

        # The rest of your logic remains the same, just make sure it
        # appends to 'lore_history' instead of 'self.lore_chat_history'.
        try:
            world_response = await supabase.get_world_details(int(world_id))
            world_data = world_response.data if world_response else None

            campaign_response = await supabase.get_campaign_details(int(campaign_id))
            campaign_data = campaign_response.data if campaign_response else None

            if not world_data or not campaign_data:
                raise Exception("World or Campaign data could not be loaded.")

            context = f"""
            World: {world_data['name']}
            Lore: {world_data.get('lore', {}).get(lang_code, "N/A")}
            Campaign: {campaign_data.get('name', {}).get(lang_code, "N/A")}
            Party: {campaign_data.get('party_info', {}).get(lang_code, "N/A")}
            History: {campaign_data.get('session_history', {}).get(lang_code, "N/A")}
            """
            self.lore_chat_session = self.gemini_service.start_chat_session(
                initial_context=context,
                model_name=model_name
            )
            lore_history.controls.clear()
            lore_history.controls.append(
                ft.Text("Context loaded. Ask about your campaign!", color=ft.Colors.GREEN_700))
        except Exception as e:
            lore_history.controls.clear()
            lore_history.controls.append(ft.Text(f"Error loading context: {e}", color=ft.Colors.RED))
        self.update()

    async def initialize_rules_lawyer(self):
        """
        Loads the permanent SRD file from Gemini using the ID from the application config.
        """
        rules_controls = self.chat_controls["rules"]
        rules_history = rules_controls["history"]
        rules_history.controls.clear()
        rules_history.controls.append(ft.Text("Initializing Rules Lawyer...", italic=True))
        self.update()

        if not GEMINI_SRD_FILE_NAME:
            rules_history.controls.clear()
            rules_history.controls.append(ft.Text("SRD document is not configured.", color=ft.Colors.RED))
            self.update()
            return

        self.gemini_srd_file_uri = GEMINI_SRD_FILE_NAME
        rules_history.controls.clear()
        rules_history.controls.append(ft.Text("SRD document ready. Ask a rules question.", color=ft.Colors.GREEN))
        self.update()

    def send_message_click(self, e):
        """Handles sending a message and kicks off the background task."""
        # 1. Identify which set of controls is active.
        selected_index = self.main_content.selected_index
        active_key = "lore" if selected_index == 0 else "rules"
        controls = self.chat_controls[active_key]

        user_input = controls["input"]
        user_text = user_input.value
        if not user_text: return

        # 2. Provide INSTANT UI feedback using the correct controls.
        user_input.value = ""
        controls["button"].disabled = True
        controls["progress"].visible = True
        controls["history"].controls.append(
            ft.Row([ft.Icon(ft.Icons.PERSON), ft.Text(user_text, selectable=True, expand=True)])
        )
        self.update()

        # 3. Run the long-running API call in the background.
        self.page.run_task(self.get_gemini_response, user_text, active_key)

    async def get_gemini_response(self, user_text: str, active_key: str):
        """Background task that calls the API and updates the correct UI when done."""
        controls = self.chat_controls[active_key]
        active_chat_history = controls["history"]

        try:
            model_name = await asyncio.to_thread(self.page.client_storage.get, "ai.model") or DEFAULT_TEXT_MODEL

            if active_key == "lore":
                if self.lore_chat_session:
                    response_text, updated_history = await self.gemini_service.send_chat_message(
                        model_name=model_name, message=user_text, history=self.lore_chat_session
                    )
                    self.lore_chat_session = updated_history
                else:
                    response_text = "Error: Lore Master session not initialized."
            else:  # rules
                if self.gemini_srd_file_uri:
                    srd_prompt = await asyncio.to_thread(self.page.client_storage.get,
                                                         "prompt.rules_lawyer") or SRD_QUERY_PROMPT
                    response_text = await self.gemini_service.query_srd_file(
                        question=user_text, srd_file_uri=self.gemini_srd_file_uri, system_prompt=srd_prompt,
                        model_name=model_name
                    )
                else:
                    response_text = "Error: SRD document not ready."

            active_chat_history.controls.append(
                ft.Row([ft.Icon(ft.Icons.SMART_TOY),
                        ft.Markdown(response_text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    expand=True)])
            )
        except Exception as ex:
            active_chat_history.controls.append(ft.Text(f"An error occurred: {ex}", color=ft.Colors.RED))
        finally:
            # Update the correct controls to re-enable the UI
            controls["button"].disabled = False
            controls["progress"].visible = False
            self.update()