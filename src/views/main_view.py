import flet as ft
import asyncio

from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService


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
        self.lore_chat_session = None

        # --- Caching for Rules Lawyer ---
        self.gemini_srd_file = None  # This will hold the Gemini File object in memory

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
                    icon=ft.Icons.LANGUAGE_OUTLINED,
                    selected_icon=ft.Icons.LANGUAGE,
                    label="Worlds",
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
        # FIX: Create separate ListView instances for each chat to isolate their state.
        self.lore_chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.rules_chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.active_chat_history = self.lore_chat_history  # Start with Lore Master active

        self.user_input = ft.TextField(
            hint_text="Ask the Lore Master...",
            expand=True,
            on_submit=self.send_message_click,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Send Message",
            on_click=self.send_message_click,
        )
        self.chat_progress = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False)

        # --- Assembling the Chat Interface ---
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
                    ft.Column([
                        self.main_content
                    ],
                        expand=True)
                ],
                expand=True,
            )
        ]

    def build_chat_view(self, chat_list_view: ft.ListView):
        """Builds the reusable chat interface container for a specific chat history."""
        return ft.Container(
            content=ft.Column(
                [
                    self.chat_progress,
                    chat_list_view,  # Use the provided ListView instance
                    ft.Row(
                        controls=[
                            self.user_input,
                            self.send_button,
                        ]
                    ),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    def did_mount(self):
        """Initializes the view and loads the correct chat context."""
        self.initialize_lore_master()

    def nav_change(self, e):
        """Handles navigation when a destination on the NavigationRail is selected."""
        index = e.control.selected_index
        if index == 0:
            self.page.go("/")
        elif index == 1:
            self.page.go("/worlds")
        elif index == 2:
            self.page.go("/settings")
        else:
            self.page.go("/")

    def tabs_changed(self, e):
        """Handles switching between Lore Master and Rules Lawyer tabs."""
        selected_index = e.control.selected_index
        if selected_index == 0:
            self.user_input.hint_text = "Ask the Lore Master..."
            self.active_chat_history = self.lore_chat_history
            self.initialize_lore_master()
        else:
            self.user_input.hint_text = "Ask the Rules Lawyer..."
            self.active_chat_history = self.rules_chat_history
            # FIX: Use page.run_task to correctly run a coroutine from a sync handler
            self.page.run_task(self.initialize_rules_lawyer)
        self.update()

    def initialize_lore_master(self):
        """Sets up the Lore Master chat, loading context from the database."""
        self.lore_chat_history.controls.clear()
        self.lore_chat_history.controls.append(ft.Text("Loading campaign context...", italic=True))
        self.update()

        lang_code = self.page.client_storage.get("active_language_code") or "en"
        world_id = self.page.client_storage.get("active_world_id")
        campaign_id = self.page.client_storage.get("active_campaign_id")

        if not world_id or not campaign_id:
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(
                ft.Text("No active world or campaign selected.", color=ft.Colors.RED))
            self.update()
            return

        try:
            world_res = supabase.client.table('worlds').select('name, lore').eq('id', world_id).single().execute()
            campaign_res = supabase.client.table('campaigns').select('name, party_info, session_history').eq('id',
                                                                                                             campaign_id).single().execute()
            context = f"""
            World: {world_res.data['name']}
            Lore: {world_res.data.get('lore', {}).get(lang_code, "N/A")}
            Campaign: {campaign_res.data.get('name', {}).get(lang_code, "N/A")}
            Party: {campaign_res.data.get('party_info', {}).get(lang_code, "N/A")}
            History: {campaign_res.data.get('session_history', {}).get(lang_code, "N/A")}
            """
            self.lore_chat_session = self.gemini_service.start_chat_session(initial_prompt=context)
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(
                ft.Text("Context loaded. Ask about the campaign!", color=ft.Colors.GREEN_700))
        except Exception as e:
            self.lore_chat_history.controls.clear()
            self.lore_chat_history.controls.append(ft.Text(f"Error loading context: {e}", color=ft.Colors.RED))
        self.update()

    async def initialize_rules_lawyer(self):
        """
        Loads the SRD document into memory and prepares it for Gemini, if not already loaded.
        """
        if self.gemini_srd_file:
            self.rules_chat_history.controls.append(
                ft.Text("SRD document is ready. Ask a rules question.", color=ft.Colors.GREEN_700))
            self.update()
            return

        self.rules_chat_history.controls.append(ft.Text("Loading SRD document...", italic=True))
        self.update()

        srd_uploaded = self.page.client_storage.get("srd_document_uploaded")
        if not srd_uploaded:
            self.rules_chat_history.controls.clear()
            self.rules_chat_history.controls.append(ft.Text("No SRD document found.", color=ft.Colors.ORANGE))
            self.update()
            return

        srd_bucket_path = self.page.client_storage.get("srd_document_bucket_path")

        gemini_file = await asyncio.to_thread(
            self.gemini_service.upload_srd_to_gemini,
            srd_bucket_path
        )

        if gemini_file:
            self.gemini_srd_file = gemini_file
            self.rules_chat_history.controls.clear()
            self.rules_chat_history.controls.append(
                ft.Text("SRD document is ready. Ask a rules question.", color=ft.Colors.GREEN_700))
        else:
            self.rules_chat_history.controls.clear()
            self.rules_chat_history.controls.append(ft.Text("Failed to load SRD document.", color=ft.Colors.RED))
        self.update()

    async def send_message_click(self, e):
        """Handles the sending of a message from the user input field."""
        user_text = self.user_input.value
        if not user_text:
            return

        self.user_input.value = ""
        self.send_button.disabled = True
        self.chat_progress.visible = True
        self.update()

        self.active_chat_history.controls.append(
            ft.Row([ft.Icon(ft.Icons.PERSON), ft.Text(user_text, selectable=True)]))
        self.update()

        try:
            selected_tab = self.main_content.selected_index
            response_text = ""

            if selected_tab == 0:  # Lore Master
                if self.lore_chat_session:
                    response = await asyncio.to_thread(self.lore_chat_session.send_message, user_text)
                    response_text = response.text
                else:
                    response_text = "Error: Lore Master session not initialized."

            else:  # Rules Lawyer
                if self.gemini_srd_file:
                    response_text = await asyncio.to_thread(
                        self.gemini_service.query_srd_file,
                        question=user_text,
                        srd_file=self.gemini_srd_file
                    )
                else:
                    response_text = "Error: SRD document not ready. Please wait or switch tabs."

            self.active_chat_history.controls.append(ft.Row(
                [ft.Icon(ft.Icons.SMART_TOY), ft.Markdown(response_text, selectable=True, extension_set="gitHubWeb")]))

        except Exception as ex:
            self.active_chat_history.controls.append(ft.Text(f"An error occurred: {ex}", color=ft.Colors.RED))

        finally:
            self.send_button.disabled = False
            self.chat_progress.visible = False
            self.update()