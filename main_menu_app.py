import logging
import threading
import flet as ft
from config import SUPPORTED_LANGUAGES
from ui_components import ChatBubble
from world_manager_app import WorldManagerApp

class MainMenuApp(ft.Row):
    def __init__(self, data_manager, api_service, app_settings):
        super().__init__(expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        self.db = data_manager
        self.ai = api_service
        self.settings = app_settings
        self.launch_char_button = ft.ElevatedButton(text="Character Manager", icon=ft.Icons.PEOPLE_OUTLINED, on_click=self.launch_character_manager, disabled=True)
        self.manage_worlds_button = ft.ElevatedButton(text="Manage Worlds", icon=ft.Icons.PUBLIC, on_click=self.launch_world_manager)
        self.settings_button = ft.ElevatedButton(text="Settings", icon=ft.Icons.SETTINGS_OUTLINED, on_click=self.launch_settings)
        self.campaign_title_label = ft.Text("No Campaign Selected", size=24, weight=ft.FontWeight.BOLD)
        self.campaign_info_label = ft.Text("Go to Settings to select a campaign.", size=14, italic=True)
        self.lore_master_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.rules_lawyer_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.lore_master_input = ft.TextField(hint_text="Ask the Lore Master...", on_submit=lambda e: self.send_message(e.control.value, self.lore_master_history, "lore_master"), expand=True)
        self.rules_lawyer_input = ft.TextField(hint_text="Ask the Rules Lawyer...", on_submit=lambda e: self.send_message(e.control.value, self.rules_lawyer_history, "rules_lawyer"), expand=True)
        sidebar = ft.Column([ft.Text("Tools", size=20, weight=ft.FontWeight.BOLD), self.launch_char_button, self.manage_worlds_button, ft.Text("More Tools Coming Soon...", italic=True), ft.Container(expand=True), self.settings_button], width=220, spacing=10, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        chat_tabs = ft.Tabs(selected_index=0, animation_duration=300, tabs=[ft.Tab(text="Lore Master", icon=ft.Icons.BOOK_OUTLINED, content=self._create_chat_ui(self.lore_master_history, self.lore_master_input, "lore_master")), ft.Tab(text="Rules Lawyer", icon=ft.Icons.GAVEL_OUTLINED, content=self._create_chat_ui(self.rules_lawyer_history, self.rules_lawyer_input, "rules_lawyer")), ft.Tab(text="NPC Actor", icon=ft.Icons.THEATER_COMEDY, content=ft.Column([ft.Text("NPC Actor Coming Soon!")], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))], expand=True)
        main_content = ft.Column([ft.Container(content=ft.Row([self.campaign_title_label, self.campaign_info_label], vertical_alignment=ft.CrossAxisAlignment.END), padding=ft.padding.only(left=20, top=10, bottom=10)), chat_tabs], expand=True)
        self.controls = [ft.Card(content=sidebar, elevation=10), main_content]

    def did_mount(self):
        self.refresh_display()

    def _create_chat_ui(self, history_listview, input_textfield, persona):
        return ft.Column([history_listview, ft.Row([input_textfield, ft.IconButton(icon=ft.Icons.SEND, tooltip="Send", on_click=lambda e: self.send_message(input_textfield.value, history_listview, persona)), ft.IconButton(icon=ft.Icons.CLEAR, tooltip="Clear Chat", on_click=lambda e: self.clear_chat(history_listview, persona))], alignment=ft.MainAxisAlignment.CENTER)], expand=True)

    def send_message(self, message, history_control, persona):
        user_message = message.strip()
        if not user_message: return
        if persona == "lore_master": self.lore_master_input.value = ""
        elif persona == "rules_lawyer": self.rules_lawyer_input.value = ""
        history_control.controls.append(ChatBubble(message=user_message, role="user"))
        thinking_bubble = ChatBubble(message="Thinking...", role="model")
        history_control.controls.append(thinking_bubble)
        self.update()
        threading.Thread(target=self.get_ai_response, args=(user_message, persona, thinking_bubble), daemon=True).start()

    def get_ai_response(self, user_message, persona, thinking_bubble):
        try:
            response_text = self.ai.send_chat_message(user_message, persona)
            self.page.call_soon(lambda: self.update_chat_bubble(thinking_bubble, response_text))
        except Exception as e:
            logging.error(f"Error getting AI response: {e}")
            self.page.call_soon(lambda: self.update_chat_bubble(thinking_bubble, f"Error: {e}"))

    def update_chat_bubble(self, bubble, new_text):
        bubble.update_message(new_text)
        self.update()

    def clear_chat(self, history_control, persona):
        history_control.controls.clear()
        self.ai.clear_chat_session(persona)
        logging.info(f"Chat history for '{persona}' cleared.")
        self.update()

    def refresh_display(self):
        logging.info("Refreshing main display...")
        self.settings._load_settings()
        world_id = self.settings.get("active_world_id")
        campaign_id = self.settings.get("active_campaign_id")
        lang = self.settings.get("active_language")
        world_name, campaign_name = "N/A", "No Campaign Selected"
        info_text = "Go to Settings to select your active world and campaign."
        char_button_disabled = True
        if world_id and self.db:
            try:
                world_trans = self.db.get_world_translation(world_id, lang)
                if world_trans: world_name = world_trans.get('world_name', 'N/A')
                if campaign_id:
                    all_campaigns = self.db.get_campaigns_for_world(world_id)
                    campaign_data = next((c for c in all_campaigns if c['campaign_id'] == campaign_id), None)
                    if campaign_data:
                        campaign_name = campaign_data['campaign_name']
                        info_text = f"World: {world_name}  |  Language: {SUPPORTED_LANGUAGES.get(lang, lang)}"
                        char_button_disabled = False
                    else:
                        self.settings.set("active_campaign_id", None); self.settings.save()
            except Exception as e:
                logging.error(f"Database connection failed during refresh: {e}")
                info_text = "Error: Could not connect to the database."
        self.campaign_title_label.value = campaign_name
        self.campaign_info_label.value = info_text
        self.launch_char_button.disabled = char_button_disabled
        if self.page: self.update()

    async def launch_world_manager(self, e):
        """Creates and displays the World Manager dialog using a robust async lifecycle."""
        if self.page:
            world_manager_dialog = WorldManagerApp(self, self.db, self.ai)
            self.page.dialog = world_manager_dialog
            world_manager_dialog.open = True
            await self.page.update_async() # Draw the empty dialog
            await world_manager_dialog.load_and_display_worlds() # THEN populate it

    def launch_settings(self, e):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Settings App not yet implemented in Flet."))
            self.page.snack_bar.open = True
            self.page.update()

    def launch_character_manager(self, e):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Character Manager not yet implemented in Flet."))
            self.page.snack_bar.open = True
            self.page.update()