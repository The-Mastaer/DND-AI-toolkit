import logging
import flet as ft
from config import SUPPORTED_LANGUAGES, AVAILABLE_TEXT_MODELS, AVAILABLE_IMAGE_MODELS
from ui_components import ChatBubble
import threading


# ==============================================================================
# Main Menu View
# ==============================================================================
def create_main_menu_view(page: ft.Page, app_state: dict) -> ft.Control:
    """
    Creates the main application view content.
    """
    db = app_state["data_manager"]
    ai = app_state["api_service"]
    settings = app_state["app_settings"]

    # --- Chat UI Helper ---
    def _create_chat_ui(history_listview, input_textfield, persona):
        return ft.Column(
            [
                history_listview,
                ft.Row(
                    [
                        input_textfield,
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            tooltip="Send",
                            on_click=lambda e: send_message(input_textfield.value, history_listview, persona)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            tooltip="Clear Chat",
                            on_click=lambda e: clear_chat(history_listview, persona)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            expand=True
        )

    # --- Chat Logic ---
    def send_message(message, history_control, persona):
        user_message = message.strip()
        if not user_message: return

        if persona == "lore_master":
            lore_master_input.value = ""
        elif persona == "rules_lawyer":
            rules_lawyer_input.value = ""

        history_control.controls.append(ChatBubble(message=user_message, role="user"))
        thinking_bubble = ChatBubble(message="Thinking...", role="model")
        history_control.controls.append(thinking_bubble)
        page.update()
        threading.Thread(target=get_ai_response, args=(user_message, persona, thinking_bubble), daemon=True).start()

    def get_ai_response(user_message, persona, thinking_bubble):
        try:
            response_text = ai.send_chat_message(user_message, persona)
            page.loop.call_soon_threadsafe(update_chat_bubble, thinking_bubble, response_text)
        except Exception as e:
            logging.error(f"Error getting AI response: {e}")
            page.loop.call_soon_threadsafe(update_chat_bubble, thinking_bubble, f"Error: {e}")

    def update_chat_bubble(bubble, new_text):
        bubble.update_message(new_text)
        page.update()

    def clear_chat(history_control, persona):
        history_control.controls.clear()
        ai.clear_chat_session(persona)
        logging.info(f"Chat history for '{persona}' cleared.")
        page.update()

    def refresh_home_display():
        logging.info("Refreshing home display...")
        settings._load_settings()  # Ensure settings are fresh
        world_id = settings.get("active_world_id")
        campaign_id = settings.get("active_campaign_id")
        lang = settings.get("active_language")

        world_name, campaign_name = "N/A", "No Campaign Selected"
        info_text = "Go to Settings to select your active world and campaign."

        if world_id and campaign_id:
            try:
                world_trans = db.get_world_translation(world_id, lang)
                if world_trans: world_name = world_trans.get('world_name', 'N/A')

                all_campaigns = db.get_campaigns_for_world(world_id)
                campaign_data = next((c for c in all_campaigns if c['campaign_id'] == campaign_id), None)

                if campaign_data:
                    campaign_name = campaign_data['campaign_name']
                    info_text = f"World: {world_name}  |  Language: {SUPPORTED_LANGUAGES.get(lang, lang)}"
            except Exception as e:
                logging.error(f"Database connection failed during refresh: {e}")
                info_text = "Error: Could not connect to the database."

        campaign_title_label.value = campaign_name
        campaign_info_label.value = info_text
        page.update()

    app_state["refresh_home_view"] = refresh_home_display

    campaign_title_label = ft.Text("No Campaign Selected", size=28, font_family="Cinzel", weight=ft.FontWeight.BOLD)
    campaign_info_label = ft.Text("Go to Settings to select a campaign.", size=14, italic=True, font_family="Roboto")

    lore_master_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    rules_lawyer_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    lore_master_input = ft.TextField(hint_text="Ask the Lore Master...",
                                     on_submit=lambda e: send_message(e.control.value, lore_master_history,
                                                                      "lore_master"), expand=True, border_radius=10)
    rules_lawyer_input = ft.TextField(hint_text="Ask the Rules Lawyer...",
                                      on_submit=lambda e: send_message(e.control.value, rules_lawyer_history,
                                                                       "rules_lawyer"), expand=True, border_radius=10)

    chat_tabs = ft.Tabs(selected_index=0, animation_duration=300, tabs=[
        ft.Tab(text="Lore Master", icon=ft.Icons.BOOK_OUTLINED,
               content=_create_chat_ui(lore_master_history, lore_master_input, "lore_master")),
        ft.Tab(text="Rules Lawyer", icon=ft.Icons.GAVEL_OUTLINED,
               content=_create_chat_ui(rules_lawyer_history, rules_lawyer_input, "rules_lawyer")),
        ft.Tab(text="NPC Actor", icon=ft.Icons.THEATER_COMEDY,
               content=ft.Column([ft.Text("NPC Actor Coming Soon!")], alignment=ft.MainAxisAlignment.CENTER,
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER))], expand=True)

    # Initial load
    refresh_home_display()

    return ft.Column([ft.Container(content=ft.Column([campaign_title_label, campaign_info_label]),
                                   padding=ft.padding.only(left=20, top=20, bottom=10, right=20)), chat_tabs],
                     expand=True)


# ==============================================================================
# World Manager View
# ==============================================================================
def create_world_manager_view(page: ft.Page, app_state: dict) -> ft.Control:
    db = app_state["data_manager"]
    settings = app_state["app_settings"]
    ai = app_state["api_service"]

    worlds_in_current_lang = []
    selected_world_data = None

    async def on_world_click(e):
        await select_world(e.control.data)

    language_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
        value=settings.get("active_language", "en"), expand=True)
    world_list_view = ft.ListView(expand=True, spacing=5, padding=10)
    world_name_entry = ft.TextField(label="World Name", disabled=True, border_radius=10)
    world_lore_textbox = ft.TextField(label="World Lore", multiline=True, min_lines=15, max_lines=15, expand=True,
                                      disabled=True, border_radius=10)
    status_label = ft.Text("Select a world or create a new one.", italic=True, font_family="Roboto")
    delete_button = ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_400,
                                  tooltip="Delete Selected World", disabled=True)
    campaign_button = ft.ElevatedButton("Manage Campaigns", icon=ft.Icons.GROUP_WORK, disabled=True)
    translate_button = ft.ElevatedButton("Translate", icon=ft.Icons.TRANSLATE, disabled=True)
    save_button = ft.ElevatedButton("Save World", icon=ft.Icons.SAVE, disabled=True)

    async def open_translate_dialog(e):
        if not selected_world_data: return

        target_lang_dd = ft.Dropdown(
            label="Translate to...",
            options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items() if
                     code != language_dropdown.value]
        )

        async def do_translation(e):
            if not target_lang_dd.value: return

            translate_dialog.content = ft.Row([ft.ProgressRing(), ft.Text("Translating...")],
                                              alignment=ft.MainAxisAlignment.CENTER)
            translate_dialog.actions = []
            page.update()

            try:
                translated_name = await page.loop.run_in_executor(page.executor, ai.translate_text,
                                                                  selected_world_data['world_name'],
                                                                  target_lang_dd.value)
                translated_lore = await page.loop.run_in_executor(page.executor, ai.translate_text,
                                                                  selected_world_data['world_lore'],
                                                                  target_lang_dd.value)

                await page.loop.run_in_executor(page.executor, db.update_world_translation,
                                                selected_world_data['world_id'], target_lang_dd.value, translated_name,
                                                translated_lore)

                translate_dialog.open = False
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Successfully translated to {SUPPORTED_LANGUAGES[target_lang_dd.value]}!"), open=True)
            except Exception as ex:
                logging.error(f"Translation failed: {ex}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Error: Translation failed. {ex}"), open=True)
                translate_dialog.open = False

            await load_and_display_worlds()
            page.update()

        translate_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Translate World"),
            content=ft.Column([
                ft.Text(
                    f"Translate '{selected_world_data['world_name']}' from {SUPPORTED_LANGUAGES[language_dropdown.value]} to:"),
                target_lang_dd
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(translate_dialog, 'open', False) or page.update()),
                ft.ElevatedButton("Translate", on_click=do_translation),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog = translate_dialog
        translate_dialog.open = True
        page.update()

    translate_button.on_click = open_translate_dialog

    async def select_world(w_data):
        nonlocal selected_world_data
        selected_world_data = w_data
        app_state["selected_world_for_campaigns"] = w_data
        world_name_entry.value = w_data.get("world_name", "")
        world_lore_textbox.value = w_data.get("world_lore", "")
        status_label.value = f"Editing '{w_data.get('world_name')}'"

        world_name_entry.disabled = False
        world_lore_textbox.disabled = False
        save_button.disabled = False
        delete_button.disabled = False
        campaign_button.disabled = False
        translate_button.disabled = False

        await highlight_selected_world()
        page.update()

    async def highlight_selected_world():
        if not selected_world_data: return
        for button in world_list_view.controls:
            is_selected = (button.data['world_id'] == selected_world_data['world_id'])
            button.style.bgcolor = ft.Colors.TEAL_ACCENT_700 if is_selected else "transparent"
        page.update()

    async def load_and_display_worlds():
        nonlocal worlds_in_current_lang
        active_lang = language_dropdown.value
        worlds_in_current_lang = await page.loop.run_in_executor(page.executor, db.get_all_worlds, active_lang)

        world_list_view.controls.clear()
        for world_data in worlds_in_current_lang:
            world_button = ft.ElevatedButton(text=world_data['world_name'], data=world_data, on_click=on_world_click,
                                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                  bgcolor="transparent"))
            world_list_view.controls.append(world_button)
        await clear_main_panel()
        page.update()

    async def clear_main_panel():
        nonlocal selected_world_data
        selected_world_data = None
        app_state["selected_world_for_campaigns"] = None
        world_name_entry.value = ""
        world_lore_textbox.value = ""
        world_name_entry.disabled = True
        world_lore_textbox.disabled = True
        status_label.value = "Select a world or create a new one."
        delete_button.disabled = True
        campaign_button.disabled = True
        translate_button.disabled = True
        save_button.disabled = True
        for button in world_list_view.controls:
            button.style.bgcolor = "transparent"

    async def new_world(e):
        await clear_main_panel()
        world_name_entry.disabled = False
        world_lore_textbox.disabled = False
        save_button.disabled = False
        status_label.value = f"Creating new world in {SUPPORTED_LANGUAGES[language_dropdown.value]}"
        page.update()

    async def save_world_click(e):
        name = world_name_entry.value.strip()
        lore = world_lore_textbox.value.strip()
        lang = language_dropdown.value
        if not name:
            status_label.value = "Error: World Name cannot be empty."
            page.update()
            return

        try:
            if selected_world_data:
                world_id = selected_world_data['world_id']
                await page.loop.run_in_executor(page.executor, db.update_world_translation, world_id, lang, name, lore)
            else:
                await page.loop.run_in_executor(page.executor, db.create_world, name, lang, lore)

            await load_and_display_worlds()
            status_label.value = "World saved successfully!"
        except Exception as ex:
            logging.error(f"Error saving world: {ex}")
            status_label.value = f"Error: Could not save world. {ex}"
        page.update()

    language_dropdown.on_change = lambda e: page.run_task(load_and_display_worlds)
    save_button.on_click = save_world_click
    campaign_button.on_click = lambda _: page.go("/campaigns")
    page.run_task(load_and_display_worlds)

    sidebar = ft.Card(content=ft.Container(content=ft.Column([ft.Text("Your Worlds", size=24, font_family="Cinzel"),
                                                              ft.Row([ft.Text("Language:", font_family="Roboto"),
                                                                      language_dropdown]),
                                                              ft.Container(content=world_list_view, expand=True,
                                                                           border_radius=10,
                                                                           border=ft.border.all(1, ft.Colors.WHITE24)),
                                                              ft.Row([ft.ElevatedButton("New", icon=ft.Icons.ADD,
                                                                                        on_click=new_world),
                                                                      delete_button],
                                                                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                                              ft.Row([campaign_button, translate_button],
                                                                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN)],
                                                             spacing=10), padding=10), width=350)
    main_content = ft.Column(
        [world_name_entry, world_lore_textbox, status_label, ft.Container(expand=True), save_button], expand=True,
        spacing=10)

    return ft.Container(content=ft.Column([ft.Text("World Manager", size=32, font_family="Cinzel"),
                                           ft.Row([sidebar, main_content], expand=True,
                                                  vertical_alignment=ft.CrossAxisAlignment.STRETCH)], expand=True,
                                          spacing=20), padding=20, expand=True)


# ==============================================================================
# Campaign Manager View
# ==============================================================================
def create_campaign_manager_view(page: ft.Page, app_state: dict) -> ft.Control:
    db = app_state["data_manager"]
    world_data = app_state.get("selected_world_for_campaigns")

    if not world_data:
        return ft.Container(content=ft.Column([ft.Text("No World Selected", size=32, font_family="Cinzel"), ft.Text(
            "Please go to the World Manager and select a world to see its campaigns."),
                                               ft.ElevatedButton("Go to Worlds",
                                                                 on_click=lambda _: page.go("/worlds"))]),
                            alignment=ft.alignment.center, expand=True)

    campaigns_in_view = []
    selected_campaign_data = None

    async def on_campaign_click(e):
        await select_campaign(e.control.data)

    campaign_list_view = ft.ListView(expand=True, spacing=5, padding=10)
    campaign_name_entry = ft.TextField(label="Campaign Name", disabled=True, border_radius=10)
    party_info_textbox = ft.TextField(label="Party Info", multiline=True, min_lines=8, disabled=True, border_radius=10)
    session_history_textbox = ft.TextField(label="Session History", multiline=True, min_lines=8, disabled=True,
                                           border_radius=10)
    status_label = ft.Text("Select a campaign or create a new one.", italic=True)
    delete_button = ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_400,
                                  tooltip="Delete Selected Campaign", disabled=True)
    save_button = ft.ElevatedButton("Save Campaign", icon=ft.Icons.SAVE, disabled=True)

    async def select_campaign(c_data):
        nonlocal selected_campaign_data
        selected_campaign_data = c_data
        campaign_name_entry.value = c_data.get("campaign_name", "")
        party_info_textbox.value = c_data.get("party_info", "")
        session_history_textbox.value = c_data.get("session_history", "")
        status_label.value = f"Editing '{c_data.get('campaign_name')}'"

        campaign_name_entry.disabled = False
        party_info_textbox.disabled = False
        session_history_textbox.disabled = False
        save_button.disabled = False
        delete_button.disabled = False

        page.update()

    async def load_and_display_campaigns():
        nonlocal campaigns_in_view
        all_campaigns = await page.loop.run_in_executor(page.executor, db.get_campaigns_for_world,
                                                        world_data['world_id'])
        campaigns_in_view = [c for c in all_campaigns if c['language'] == world_data['language']]

        campaign_list_view.controls.clear()
        for c_data in campaigns_in_view:
            campaign_button = ft.ElevatedButton(text=c_data['campaign_name'], data=c_data, on_click=on_campaign_click,
                                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                     bgcolor="transparent"))
            campaign_list_view.controls.append(campaign_button)
        await clear_main_panel()
        page.update()

    async def clear_main_panel():
        nonlocal selected_campaign_data
        selected_campaign_data = None
        campaign_name_entry.value = ""
        party_info_textbox.value = ""
        session_history_textbox.value = ""
        campaign_name_entry.disabled = True
        party_info_textbox.disabled = True
        session_history_textbox.disabled = True
        status_label.value = "Select a campaign or create a new one."
        delete_button.disabled = True
        save_button.disabled = True

    async def new_campaign(e):
        await clear_main_panel()
        campaign_name_entry.disabled = False
        party_info_textbox.disabled = False
        session_history_textbox.disabled = False
        save_button.disabled = False
        status_label.value = "Creating new campaign..."
        page.update()

    async def save_campaign_click(e):
        name = campaign_name_entry.value.strip()
        if not name: status_label.value = "Error: Campaign Name cannot be empty."; page.update(); return

        party_info = party_info_textbox.value
        session_history = session_history_textbox.value
        lang = world_data['language']

        try:
            if selected_campaign_data:
                await page.loop.run_in_executor(page.executor, db.update_campaign,
                                                selected_campaign_data['campaign_id'], name, lang, party_info,
                                                session_history)
            else:
                await page.loop.run_in_executor(page.executor, db.create_campaign, world_data['world_id'], name, lang,
                                                party_info, session_history)
            await load_and_display_campaigns()
            status_label.value = "Campaign saved successfully!"
        except Exception as ex:
            logging.error(f"Error saving campaign: {ex}");
            status_label.value = f"Error: Could not save campaign. {ex}"
        page.update()

    save_button.on_click = save_campaign_click
    page.run_task(load_and_display_campaigns)

    sidebar = ft.Card(content=ft.Container(content=ft.Column(
        [ft.Text("Campaigns", size=24, font_family="Cinzel"), ft.Text(f"for '{world_data['world_name']}'", italic=True),
         ft.Container(content=campaign_list_view, expand=True, border_radius=10,
                      border=ft.border.all(1, ft.Colors.WHITE24)),
         ft.Row([ft.ElevatedButton("New", icon=ft.Icons.ADD, on_click=new_campaign), delete_button],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], spacing=10), padding=10), width=350)

    main_content = ft.Column(
        [campaign_name_entry, party_info_textbox, session_history_textbox, status_label, ft.Container(expand=True),
         save_button], expand=True, spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

    return ft.Container(content=ft.Column([ft.Text("Campaign Manager", size=32, font_family="Cinzel"),
                                           ft.Row([sidebar, main_content], expand=True,
                                                  vertical_alignment=ft.CrossAxisAlignment.STRETCH)], expand=True,
                                          spacing=20), padding=20, expand=True)


# ==============================================================================
# Settings View
# ==============================================================================
def create_settings_view(page: ft.Page, app_state: dict) -> ft.Control:
    settings = app_state["app_settings"]
    db = app_state["data_manager"]

    def _create_prompt_tab(tab_view, name, content):
        textbox = ft.TextField(value=content, multiline=True, min_lines=10, expand=True, border_radius=10)
        tab_view.tabs.append(ft.Tab(text=name, content=ft.Container(textbox, padding=10)))
        return textbox

    def on_theme_selected(e):
        page.theme_mode = ft.ThemeMode(theme_var.value.upper())
        page.update()

    def save_settings(e):
        settings.set("active_language", lang_var.value)
        selected_world_name = world_var.value
        world = next((w for w in all_worlds if w['world_name'] == selected_world_name), None)
        if world: settings.set("active_world_id", world['world_id'])

        selected_campaign_name = campaign_var.value
        campaign = next((c for c in campaigns_for_world if c['campaign_name'] == selected_campaign_name), None)
        if campaign: settings.set("active_campaign_id", campaign['campaign_id'])

        settings.set("text_model", text_model_var.value)
        settings.set("image_model", image_model_var.value)
        settings.set("theme", theme_var.value)

        prompts = settings.get("prompts", {})
        prompts["lore_master"] = lore_master_prompt_textbox.value
        prompts["rules_lawyer"] = rules_lawyer_prompt_textbox.value
        prompts["npc_generation"] = npc_gen_prompt_textbox.value
        prompts["translation"] = translation_prompt_textbox.value
        prompts["npc_simulation_short"] = sim_short_prompt_textbox.value
        prompts["npc_simulation_long"] = sim_long_prompt_textbox.value
        settings.set("prompts", prompts)

        settings.save()
        if app_state.get("refresh_home_view"):
            app_state["refresh_home_view"]()

        page.snack_bar = ft.SnackBar(ft.Text("Settings Saved!"), open=True)
        page.update()

    lang_var = ft.Dropdown(options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
                           value=settings.get("active_language"))
    world_var = ft.Dropdown(hint_text="Select a world", disabled=True)
    campaign_var = ft.Dropdown(hint_text="Select a campaign", disabled=True)
    text_model_var = ft.Dropdown(options=[ft.dropdown.Option(m) for m in AVAILABLE_TEXT_MODELS],
                                 value=settings.get("text_model"))
    image_model_var = ft.Dropdown(options=[ft.dropdown.Option(m) for m in AVAILABLE_IMAGE_MODELS],
                                  value=settings.get("image_model"))
    theme_var = ft.Dropdown(options=[ft.dropdown.Option(t) for t in ["Light", "Dark", "System"]],
                            value=settings.get("theme"), on_change=on_theme_selected)

    all_worlds = []
    campaigns_for_world = []

    def load_worlds_for_settings():
        nonlocal all_worlds
        all_worlds = db.get_all_worlds(lang_var.value)
        world_var.options = [ft.dropdown.Option(w['world_name']) for w in all_worlds]
        active_world_id = settings.get("active_world_id")
        active_world = next((w for w in all_worlds if w['world_id'] == active_world_id), None)
        if active_world: world_var.value = active_world['world_name']
        world_var.disabled = False
        load_campaigns_for_settings()
        page.update()

    def load_campaigns_for_settings():
        nonlocal campaigns_for_world
        selected_world_name = world_var.value
        world = next((w for w in all_worlds if w['world_name'] == selected_world_name), None)
        if not world:
            campaign_var.options = [];
            campaign_var.value = None;
            campaign_var.disabled = True
            return

        campaigns_for_world = [c for c in db.get_campaigns_for_world(world['world_id']) if
                               c['language'] == lang_var.value]
        campaign_var.options = [ft.dropdown.Option(c['campaign_name']) for c in campaigns_for_world]
        active_campaign_id = settings.get("active_campaign_id")
        active_campaign = next((c for c in campaigns_for_world if c['campaign_id'] == active_campaign_id), None)
        if active_campaign: campaign_var.value = active_campaign['campaign_name']
        campaign_var.disabled = False
        page.update()

    lang_var.on_change = lambda e: load_worlds_for_settings()
    world_var.on_change = lambda e: load_campaigns_for_settings()

    load_worlds_for_settings()

    active_campaign_tab = ft.Column(
        [ft.Row([ft.Text("Active Language:"), lang_var]), ft.Row([ft.Text("Active World:"), world_var]),
         ft.Row([ft.Text("Active Campaign:"), campaign_var])], spacing=15)
    ai_settings_tab = ft.Column(
        [ft.Row([ft.Text("Text Model:"), text_model_var]), ft.Row([ft.Text("Image Model:"), image_model_var])],
        spacing=15)
    appearance_tab = ft.Column([ft.Row([ft.Text("Theme:"), theme_var])], spacing=15)

    prompts_tab_view = ft.Tabs(tabs=[], expand=True)
    prompts = settings.get("prompts", {})
    lore_master_prompt_textbox = _create_prompt_tab(prompts_tab_view, "Lore Master", prompts.get("lore_master", ""))
    rules_lawyer_prompt_textbox = _create_prompt_tab(prompts_tab_view, "Rules Lawyer", prompts.get("rules_lawyer", ""))
    npc_gen_prompt_textbox = _create_prompt_tab(prompts_tab_view, "NPC Gen", prompts.get("npc_generation", ""))
    translation_prompt_textbox = _create_prompt_tab(prompts_tab_view, "Translation", prompts.get("translation", ""))
    sim_short_prompt_textbox = _create_prompt_tab(prompts_tab_view, "Sim (Short)",
                                                  prompts.get("npc_simulation_short", ""))
    sim_long_prompt_textbox = _create_prompt_tab(prompts_tab_view, "Sim (Long)", prompts.get("npc_simulation_long", ""))

    tabs = ft.Tabs(selected_index=0, expand=True,
                   tabs=[ft.Tab(text="Active Campaign", content=ft.Container(active_campaign_tab, padding=20)),
                         ft.Tab(text="AI Settings", content=ft.Container(ai_settings_tab, padding=20)),
                         ft.Tab(text="Appearance", content=ft.Container(appearance_tab, padding=20)),
                         ft.Tab(text="Prompts", content=prompts_tab_view)])

    return ft.Container(content=ft.Column([ft.Text("Settings", size=32, font_family="Cinzel"), tabs,
                                           ft.ElevatedButton("Save All Settings", icon=ft.Icons.SAVE,
                                                             on_click=save_settings)], spacing=20), padding=20,
                        expand=True)