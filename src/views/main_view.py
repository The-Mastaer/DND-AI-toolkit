# src/views/main_view.py

import flet as ft
import asyncio

from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService
from ..prompts import SRD_QUERY_PROMPT


class MainView(ft.View):
    """
    The main view of the application, which acts as a persistent shell.
    It contains the primary navigation rail and the main content area,
    which now features the core AI chatbot interface. This view corresponds to the root route '/'.
    """

    def __init__(self, page: ft.Page):
        """
        Initializes the MainView.

        Args:
            page (ft.Page): The Flet page object for the application.
        """
        super().__init__()
        self.page = page
        self.route = "/"
        self.gemini_service = GeminiService()

        # --- State Management ---
        self.lore_chat_session = None
        self.gemini_srd_file = None # Stores the actual Gemini File object (types.File)

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
                    icon=ft.Icons.PEOPLE_OUTLINE, # Corrected Icon
                    selected_icon=ft.Icons.PEOPLE, # Corrected Selected Icon
                    label="Characters", # Corrected Label
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self.nav_change,
        )

        # --- Chat UI Controls ---
        self.lore_chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.rules_chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.active_chat_history = self.lore_chat_history

        self.user_input = ft.TextField(
            hint_text="Ask the Lore Master...",
            expand=True,
            on_submit=self.send_message_click,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Send Message",
            on_click=self.send_message_click,
        )
        self.chat_progress = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False)

        # --- Main Content Area with Tabs ---
        self.main_content = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_change=self.tabs_changed,
            tabs=[
                ft.Tab(
                    text="Lore Master",
                    icon=ft.Icons.MENU_BOOK_ROUNDED,
                    content=self.build_chat_view(self.lore_chat_history),
                ),
                ft.Tab(
                    text="Rules Lawyer",
                    icon=ft.Icons.GAVEL_ROUNDED,
                    content=self.build_chat_view(self.rules_chat_history),
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

    def build_chat_view(self, chat_list_view: ft.ListView):
        """Builds the reusable chat interface container."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.chat_progress]),
                    chat_list_view,
                    ft.Row(controls=[self.user_input, self.send_button]),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    def did_mount(self):
        """Initializes the view when it's added to the page."""
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
        if selected_index == 0:
            self.user_input.hint_text = "Ask the Lore Master..."
            self.active_chat_history = self.lore_chat_history
            self.page.run_task(self.initialize_lore_master)
        else:
            self.user_input.hint_text = "Ask the Rules Lawyer..."
            self.active_chat_history = self.rules_chat_history
            self.page.run_task(self.initialize_rules_lawyer)
        self.update()

    async def initialize_lore_master(self):
        """Sets up the Lore Master chat, loading context from the database."""
        self.lore_chat_history.controls.clear()
        self.lore_chat_history.controls.append(ft.Text("Loading campaign context...", italic=True))
        self.update()

        keys_to_fetch = ["active_language_code", "active_world_id", "active_campaign_id", "prompt.lore_master"]
        tasks = [asyncio.to_thread(self.page.client_storage.get, key) for key in keys_to_fetch]
        results = await asyncio.gather(*tasks)
        settings = dict(zip(keys_to_fetch, results))

        lang_code = settings.get("active_language_code") or "en"
        world_id = settings.get("active_world_id")
        campaign_id = settings.get("active_campaign_id")

        if not world_id or not campaign_id:
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(
                ft.Text("No active world or campaign selected in Settings.", color=ft.Colors.RED))
            self.update()
            return

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
            self.lore_chat_session = self.gemini_service.start_chat_session(initial_context=context)
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(
                ft.Text("Context loaded. Ask about your campaign!", color=ft.Colors.GREEN_700))
        except Exception as e:
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(ft.Text(f"Error loading context: {e}", color=ft.Colors.RED))
        self.update()

    async def initialize_rules_lawyer(self):
        """Loads the SRD document and prepares it for Gemini, if not already loaded or retrieved."""
        self.rules_chat_history.controls.clear()
        self.rules_chat_history.controls.append(ft.Text("Loading SRD document...", italic=True))
        self.update()

        # Try to retrieve Gemini File URI from client storage
        gemini_srd_file_name = await asyncio.to_thread(self.page.client_storage.get, "gemini_srd_file_name")

        if gemini_srd_file_name:
            print(f"Attempting to retrieve Gemini SRD file '{gemini_srd_file_name}' from Gemini API...")
            self.gemini_srd_file = await self.gemini_service.get_gemini_file_by_name(gemini_srd_file_name)

        if self.gemini_srd_file:
            self.rules_chat_history.controls.clear()
            self.rules_chat_history.controls.append(ft.Text("SRD document ready. Ask a rules question.", color=ft.Colors.GREEN_700))
        else:
            # If not found in Gemini or retrieval failed, proceed with Supabase download and Gemini upload
            srd_bucket_path = await asyncio.to_thread(self.page.client_storage.get, "srd_document_bucket_path")
            if not srd_bucket_path:
                self.rules_chat_history.controls.clear()
                self.rules_chat_history.controls.append(
                    ft.Text("No SRD document uploaded in Settings.", color=ft.Colors.ORANGE))
                self.update()
                return

            print(f"SRD file not found in Gemini, attempting to upload from Supabase path: {srd_bucket_path}")
            uploaded_file_name = await self.gemini_service.upload_srd_to_gemini(srd_bucket_path)

            if uploaded_file_name:
                # Store the Gemini File URI for future sessions
                await asyncio.to_thread(self.page.client_storage.set, "gemini_srd_file_name", uploaded_file_name)
                self.gemini_srd_file = await self.gemini_service.get_gemini_file_by_name(uploaded_file_name) # Get the actual File object

                if self.gemini_srd_file:
                    self.rules_chat_history.controls.clear()
                    self.rules_chat_history.controls.append(
                        ft.Text("SRD document ready. Ask a rules question.", color=ft.Colors.GREEN_700))
                else:
                    self.rules_chat_history.controls.clear()
                    self.rules_chat_history.controls.append(ft.Text("Failed to retrieve SRD document from Gemini after upload.", color=ft.Colors.RED))
            else:
                self.rules_chat_history.controls.clear()
                self.rules_chat_history.controls.append(ft.Text("Failed to upload SRD document to Gemini.", color=ft.Colors.RED))
        self.update()


    async def send_message_click(self, e):
        """Handles the sending of a message from the user input field."""
        user_text = self.user_input.value
        if not user_text: return

        self.user_input.value = ""
        self.send_button.disabled = True
        self.chat_progress.visible = True
        self.update()

        # Add user message to chat history, with expand=True for wrapping
        self.active_chat_history.controls.append(
            ft.Row([ft.Icon(ft.Icons.PERSON), ft.Text(user_text, selectable=True, expand=True)])
        )
        self.update()

        try:
            selected_tab = self.main_content.selected_index
            response_text = ""
            if selected_tab == 0:
                if self.lore_chat_session:
                    # Run the synchronous send_message in a separate thread
                    response = await asyncio.to_thread(self.lore_chat_session.send_message, user_text)
                    response_text = response.text
                else:
                    response_text = "Error: Lore Master session not initialized."
            else:
                if self.gemini_srd_file:
                    srd_prompt = await asyncio.to_thread(self.page.client_storage.get,
                                                         "prompt.rules_lawyer") or SRD_QUERY_PROMPT
                    response_text = await self.gemini_service.query_srd_file(question=user_text,
                                                                             srd_file=self.gemini_srd_file,
                                                                             system_prompt=srd_prompt)
                else:
                    response_text = "Error: SRD document not ready."

            # Add AI response to chat history, with expand=True for wrapping
            self.active_chat_history.controls.append(
                ft.Row([ft.Icon(ft.Icons.SMART_TOY),
                        ft.Markdown(response_text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, expand=True)])
            )
        except Exception as ex:
            self.active_chat_history.controls.append(ft.Text(f"An error occurred: {ex}", color=ft.Colors.RED))
        finally:
            self.send_button.disabled = False
            self.chat_progress.visible = False
            self.update()