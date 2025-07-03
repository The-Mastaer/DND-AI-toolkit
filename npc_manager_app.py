import tkinter
import customtkinter
from tkinter import filedialog
import threading
import io
import logging
from PIL import Image, UnidentifiedImageError

# Import constants and options from the config file
from config import (
    GENDER_OPTIONS, ATTITUDE_OPTIONS, RARITY_OPTIONS, ENVIRONMENT_OPTIONS,
    RACE_OPTIONS, CLASS_OPTIONS, BACKGROUND_OPTIONS
)
from npc_simulator_app import NpcSimulatorApp


# We remove the direct import of MainMenuApp from here to prevent a circular import

class NpcApp(customtkinter.CTk):
    """
    The main application window for the NPC Manager.
    Handles the display and interaction for creating and editing NPCs.
    """

    def __init__(self, data_manager, api_service):
        super().__init__()
        self.db = data_manager
        self.ai = api_service

        self.title("D&D NPC Manager")
        self.minsize(1100, 750)

        self.npcs = self.db.load_data()
        self.selected_npc_name = None
        self._npc_in_workshop = {}
        self._workshop_original_name = None
        self.roster_ctk_image = None
        self.workshop_ctk_image = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.update_npc_list()
        self.select_first_npc()

        self.after(100, lambda: self.state('zoomed'))

    def _create_widgets(self):
        """Initializes and lays out all the main UI components."""
        self._setup_sidebar()
        self._setup_main_tabs()

    def _setup_sidebar(self):
        """Creates the left sidebar with the NPC list."""
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)  # Adjust row for list frame

        customtkinter.CTkLabel(self.sidebar_frame, text="Your NPCs",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))

        customtkinter.CTkButton(self.sidebar_frame, text="🏠 Home", command=self.go_home).grid(row=1, column=0, padx=20,
                                                                                              pady=10, sticky="ew")

        customtkinter.CTkButton(self.sidebar_frame, text="+ New NPC", command=self.go_to_workshop_new).grid(row=2,
                                                                                                            column=0,
                                                                                                            padx=20,
                                                                                                            pady=10,
                                                                                                            sticky="ew")

        self.npc_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame, label_text="NPC Roster")
        self.npc_list_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.npc_buttons = {}

    def _setup_main_tabs(self):
        """Creates the main tab view for NPC Details and Workshop."""
        self.tabview = customtkinter.CTkTabview(self, corner_radius=10, command=self._on_tab_change)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("NPC Details")
        self.tabview.add("NPC Workshop")

        self._setup_details_tab()
        self._setup_workshop_tab()

    def _setup_details_tab(self):
        """Creates all widgets within the 'NPC Details' tab."""
        details_tab = self.tabview.tab("NPC Details")
        details_tab.grid_columnconfigure(0, weight=1)
        details_tab.grid_rowconfigure(0, weight=1)

        main_details_frame = customtkinter.CTkFrame(details_tab, fg_color="transparent")
        main_details_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        main_details_frame.grid_columnconfigure(0, weight=2)
        main_details_frame.grid_columnconfigure(1, weight=1)
        main_details_frame.grid_rowconfigure(0, weight=1)

        text_fields_frame = customtkinter.CTkFrame(main_details_frame)
        text_fields_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        text_fields_frame.grid_columnconfigure(1, weight=1)
        text_fields_frame.grid_rowconfigure(6, weight=1)  # Roleplaying Tips
        text_fields_frame.grid_rowconfigure(5, weight=2)  # Backstory

        self.roster_name_label = self._create_roster_label_field(text_fields_frame, "Name:", 0)
        self.roster_race_class_label = self._create_roster_label_field(text_fields_frame, "Race/Class:", 1)

        tags_frame = customtkinter.CTkFrame(text_fields_frame)
        tags_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(tags_frame, text="Tags:", font=customtkinter.CTkFont(weight="bold")).pack(side="left",
                                                                                                         padx=(10, 5))
        self.roster_tags_label = customtkinter.CTkLabel(tags_frame, text="", anchor="w")
        self.roster_tags_label.pack(side="left", padx=5, fill="x", expand=True)

        self.roster_appearance_textbox = self._create_roster_textbox_field(text_fields_frame, "Appearance:", 3)
        self.roster_personality_textbox = self._create_roster_textbox_field(text_fields_frame, "Personality:", 4)
        self.roster_backstory_textbox = self._create_roster_textbox_field(text_fields_frame, "Backstory:", 5)
        self.roster_plothooks_textbox = self._create_roster_textbox_field(text_fields_frame, "Plot Hooks:", 6)
        self.roster_roleplaying_textbox = self._create_roster_textbox_field(text_fields_frame, "Roleplaying Tips:", 7)

        portrait_frame = customtkinter.CTkFrame(main_details_frame)
        portrait_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        portrait_frame.grid_rowconfigure(0, weight=1)
        portrait_frame.grid_columnconfigure(0, weight=1)
        self.roster_portrait_label = customtkinter.CTkLabel(portrait_frame, text="No Portrait", width=300, height=300)
        self.roster_portrait_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        bottom_button_frame = customtkinter.CTkFrame(details_tab, fg_color="transparent")
        bottom_button_frame.grid(row=1, column=0, pady=(10, 10), sticky="s")
        customtkinter.CTkButton(bottom_button_frame, text="Launch Simulator", command=self.launch_simulator_app).pack(
            side="left", padx=10)
        customtkinter.CTkButton(bottom_button_frame, text="Edit this NPC", command=self.go_to_workshop_edit).pack(
            side="left", padx=10)
        customtkinter.CTkButton(bottom_button_frame, text="Delete this NPC", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_npc).pack(side="left", padx=10)

    def _setup_workshop_tab(self):
        """Creates all widgets within the 'NPC Workshop' tab with a redesigned layout."""
        workshop_tab = self.tabview.tab("NPC Workshop")
        workshop_tab.grid_columnconfigure(0, weight=1)
        workshop_tab.grid_rowconfigure(0, weight=1)

        main_workshop_frame = customtkinter.CTkFrame(workshop_tab, fg_color="transparent")
        main_workshop_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_workshop_frame.grid_columnconfigure(0, weight=1)
        main_workshop_frame.grid_columnconfigure(1, weight=1)
        main_workshop_frame.grid_rowconfigure(0, weight=1)

        edit_text_frame = customtkinter.CTkFrame(main_workshop_frame)
        edit_text_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        edit_text_frame.grid_columnconfigure(1, weight=1)
        edit_text_frame.grid_rowconfigure(2, weight=1)
        edit_text_frame.grid_rowconfigure(3, weight=1)
        edit_text_frame.grid_rowconfigure(4, weight=2)
        edit_text_frame.grid_rowconfigure(5, weight=1)
        edit_text_frame.grid_rowconfigure(6, weight=1)  # Roleplaying Tips

        self.workshop_name_entry = self._create_workshop_entry_field(edit_text_frame, "Name:", 0)
        self.workshop_race_entry = self._create_workshop_entry_field(edit_text_frame, "Race/Class:", 1)
        self.workshop_appearance_textbox = self._create_workshop_textbox_field(edit_text_frame, "Appearance:", 2)
        self.workshop_personality_textbox = self._create_workshop_textbox_field(edit_text_frame, "Personality:", 3)
        self.workshop_backstory_textbox = self._create_workshop_textbox_field(edit_text_frame, "Backstory:", 4)
        self.workshop_plothooks_textbox = self._create_workshop_textbox_field(edit_text_frame, "Plot Hooks:", 5)
        self.workshop_roleplaying_textbox = self._create_workshop_textbox_field(edit_text_frame, "Roleplaying Tips:", 6)

        right_panel_frame = customtkinter.CTkFrame(main_workshop_frame)
        right_panel_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_panel_frame.grid_columnconfigure(0, weight=1)
        right_panel_frame.grid_rowconfigure(1, weight=1)

        edit_portrait_frame = customtkinter.CTkFrame(right_panel_frame)
        edit_portrait_frame.grid(row=0, column=0, pady=(0, 10), sticky="new")
        edit_portrait_frame.grid_columnconfigure(0, weight=1)
        self.workshop_portrait_label = customtkinter.CTkLabel(edit_portrait_frame, text="No Portrait", width=250,
                                                              height=250)
        self.workshop_portrait_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        workshop_portrait_buttons = customtkinter.CTkFrame(edit_portrait_frame, fg_color="transparent")
        workshop_portrait_buttons.grid(row=1, column=0, pady=10)
        customtkinter.CTkButton(workshop_portrait_buttons, text="Generate Portrait",
                                command=self.start_image_generation_thread).pack(side="left", padx=5, expand=True)
        customtkinter.CTkButton(workshop_portrait_buttons, text="Upload Portrait", command=self.upload_portrait).pack(
            side="left", padx=5, expand=True)

        tags_and_gen_frame = customtkinter.CTkFrame(right_panel_frame, fg_color="transparent")
        tags_and_gen_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        tags_and_gen_frame.grid_columnconfigure(0, weight=1)
        tags_and_gen_frame.grid_rowconfigure(1, weight=1)

        generator_options_frame = customtkinter.CTkFrame(tags_and_gen_frame)
        generator_options_frame.grid(row=0, column=0, sticky="ew")
        generator_options_frame.grid_columnconfigure(1, weight=1)
        generator_options_frame.grid_columnconfigure(3, weight=1)

        self.gender_var = customtkinter.StringVar(value=GENDER_OPTIONS[0])
        self.attitude_var = customtkinter.StringVar(value=ATTITUDE_OPTIONS[0])
        self.rarity_var = customtkinter.StringVar(value=RARITY_OPTIONS[0])
        self.environment_var = customtkinter.StringVar(value=ENVIRONMENT_OPTIONS[0])
        self.race_var = customtkinter.StringVar(value=RACE_OPTIONS[0])
        self.class_var = customtkinter.StringVar(value=CLASS_OPTIONS[0])
        self.background_var = customtkinter.StringVar(value=BACKGROUND_OPTIONS[0])

        option_map = {
            "Gender": (self.gender_var, GENDER_OPTIONS), "Attitude": (self.attitude_var, ATTITUDE_OPTIONS),
            "Rarity": (self.rarity_var, RARITY_OPTIONS), "Environment": (self.environment_var, ENVIRONMENT_OPTIONS),
            "Race": (self.race_var, RACE_OPTIONS), "Class": (self.class_var, CLASS_OPTIONS),
            "Background": (self.background_var, BACKGROUND_OPTIONS)
        }

        row_counter = 0
        for i, (label, (var, values)) in enumerate(option_map.items()):
            col = (i % 2) * 2
            if i > 0 and col == 0:
                row_counter += 1
            self._create_workshop_option_menu(generator_options_frame, label, var, values, row_counter, col)

        customtkinter.CTkLabel(tags_and_gen_frame, text="Custom Prompt:",
                               font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=(10, 0),
                                                                               sticky="w")
        self.custom_prompt_textbox = customtkinter.CTkTextbox(tags_and_gen_frame, height=100, wrap="word")
        self.custom_prompt_textbox.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.generate_button = customtkinter.CTkButton(tags_and_gen_frame, text="Generate with AI", height=40,
                                                       command=self.start_generation_thread)
        self.generate_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.workshop_status_textbox = customtkinter.CTkTextbox(right_panel_frame, height=100, wrap="word",
                                                                state="disabled")
        self.workshop_status_textbox.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        customtkinter.CTkButton(workshop_tab, text="Save NPC in Workshop", height=40,
                                command=self.save_workshop_npc).grid(row=1, column=0, padx=10, pady=(10, 10),
                                                                     sticky="s")

    def go_home(self):
        """Schedules the window to close and the main menu to open."""
        self.after(10, self._go_home_task)

    def _go_home_task(self):
        """The actual task of closing the window and opening the main menu."""
        from main_menu_app import MainMenuApp
        self.destroy()
        main_menu = MainMenuApp(data_manager=self.db, api_service=self.ai)
        main_menu.mainloop()

    def _create_roster_label_field(self, parent, text, row):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        label = customtkinter.CTkLabel(parent, text="", anchor="w")
        label.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        return label

    def _create_roster_textbox_field(self, parent, text, row):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=0, padx=10, pady=5, sticky="nw")
        textbox = customtkinter.CTkTextbox(parent, state="disabled", wrap="word")
        textbox.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")
        return textbox

    def _create_workshop_entry_field(self, parent, text, row):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        entry = customtkinter.CTkEntry(parent)
        entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        return entry

    def _create_workshop_textbox_field(self, parent, text, row):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=0, padx=10, pady=5, sticky="nw")
        textbox = customtkinter.CTkTextbox(parent, wrap="word")
        textbox.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")
        return textbox

    def _create_workshop_option_menu(self, parent, text, variable, values, row, col):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=col, padx=(10, 5), pady=5, sticky="w")
        customtkinter.CTkOptionMenu(parent, variable=variable, values=values).grid(row=row, column=col + 1,
                                                                                   padx=(0, 10), pady=5, sticky="ew")

    def update_npc_list(self):
        """Clears and repopulates the NPC list in the sidebar."""
        for widget in self.npc_list_frame.winfo_children():
            widget.destroy()

        sorted_npc_names = sorted(self.npcs.keys())
        self.npc_buttons = {}
        for name in sorted_npc_names:
            button = customtkinter.CTkButton(self.npc_list_frame, text=name, command=lambda n=name: self.select_npc(n))
            button.pack(pady=5, padx=5, fill="x")
            self.npc_buttons[name] = button
        self.highlight_selected_npc()

    def highlight_selected_npc(self):
        """Visually highlights the currently selected NPC in the list."""
        for name, button in self.npc_buttons.items():
            is_selected = (name == self.selected_npc_name)
            button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"] if is_selected else
            customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def populate_roster_fields(self, npc_data):
        """Fills all the fields in the Roster tab with data from a given NPC."""
        self.roster_name_label.configure(text=npc_data.get("name", "N/A"))
        self.roster_race_class_label.configure(text=npc_data.get("race_class", "N/A"))

        tags = [
            npc_data.get('gender'), npc_data.get('attitude'), npc_data.get('rarity'),
            npc_data.get('environment'), npc_data.get('race'), npc_data.get('character_class'),
            npc_data.get('background')
        ]
        self.roster_tags_label.configure(text=" | ".join(filter(None, tags)))

        self._update_textbox(self.roster_appearance_textbox, npc_data.get("appearance", ""))
        self._update_textbox(self.roster_personality_textbox, npc_data.get("personality", ""))
        self._update_textbox(self.roster_backstory_textbox, npc_data.get("backstory", ""))
        self._update_textbox(self.roster_plothooks_textbox, npc_data.get("plot_hooks", ""))
        self._update_textbox(self.roster_roleplaying_textbox, npc_data.get("roleplaying_tips", ""))

        self.roster_ctk_image = self._create_ctk_image_from_data(npc_data.get("image_data"))
        self.roster_portrait_label.configure(image=self.roster_ctk_image,
                                             text="" if self.roster_ctk_image else "No Portrait")

    def populate_workshop_fields(self, npc_data):
        """Fills all the fields in the Workshop tab with data for editing."""
        self._npc_in_workshop = npc_data.copy()
        self._workshop_original_name = npc_data.get('name')

        self.workshop_name_entry.delete(0, "end")
        self.workshop_name_entry.insert(0, self._npc_in_workshop.get("name", ""))
        self.workshop_race_entry.delete(0, "end")
        self.workshop_race_entry.insert(0, self._npc_in_workshop.get("race_class", ""))

        self._update_textbox(self.workshop_appearance_textbox, self._npc_in_workshop.get("appearance", ""),
                             state="normal")
        self._update_textbox(self.workshop_personality_textbox, self._npc_in_workshop.get("personality", ""),
                             state="normal")
        self._update_textbox(self.workshop_backstory_textbox, self._npc_in_workshop.get("backstory", ""),
                             state="normal")
        self._update_textbox(self.workshop_plothooks_textbox, self._npc_in_workshop.get("plot_hooks", ""),
                             state="normal")
        self._update_textbox(self.custom_prompt_textbox, self._npc_in_workshop.get("custom_prompt", ""), state="normal")
        self._update_textbox(self.workshop_roleplaying_textbox, self._npc_in_workshop.get("roleplaying_tips", ""),
                             state="normal")

        self.gender_var.set(self._npc_in_workshop.get('gender') or GENDER_OPTIONS[0])
        self.attitude_var.set(self._npc_in_workshop.get('attitude') or ATTITUDE_OPTIONS[0])
        self.rarity_var.set(self._npc_in_workshop.get('rarity') or RARITY_OPTIONS[0])
        self.environment_var.set(self._npc_in_workshop.get('environment') or ENVIRONMENT_OPTIONS[0])
        self.race_var.set(self._npc_in_workshop.get('race') or RACE_OPTIONS[0])
        self.class_var.set(self._npc_in_workshop.get('character_class') or CLASS_OPTIONS[0])
        self.background_var.set(self._npc_in_workshop.get('background') or BACKGROUND_OPTIONS[0])

        self._update_workshop_image_display()
        self._update_textbox(self.workshop_status_textbox, "")

    def _update_workshop_image_display(self):
        """Updates the image in the workshop based on current workshop data."""
        self.workshop_ctk_image = self._create_ctk_image_from_data(self._npc_in_workshop.get("image_data"),
                                                                   size=(250, 250))
        self.workshop_portrait_label.configure(image=self.workshop_ctk_image,
                                               text="" if self.workshop_ctk_image else "No Portrait")

    def _update_textbox(self, textbox, text, state="disabled"):
        """Safely updates the content of a CTkTextbox."""
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state=state)

    def _create_ctk_image_from_data(self, image_bytes, size=(300, 300)):
        """Creates a CTkImage from byte data, handling errors."""
        if not image_bytes:
            return None
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            return customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        except (UnidentifiedImageError, io.UnsupportedOperation) as e:
            logging.error(f"Failed to create image from data: {e}")
            return None

    def _on_tab_change(self):
        """Event handler for when the user switches tabs."""
        selected_tab = self.tabview.get()
        if selected_tab == "NPC Details" and self.selected_npc_name:
            self.populate_roster_fields(self.npcs.get(self.selected_npc_name, {}))

    def select_npc(self, name):
        """Handles the selection of an NPC from the list."""
        if name in self.npcs:
            self.selected_npc_name = name
            npc_data = self.npcs.get(name, {})
            self.populate_roster_fields(npc_data)
            self.highlight_selected_npc()
            self.tabview.set("NPC Details")
        else:
            logging.warning(f"Attempted to select non-existent NPC: {name}")

    def select_first_npc(self):
        """Selects the first NPC in the list, or goes to create a new one."""
        if self.npcs:
            first_npc_name = sorted(self.npcs.keys())[0]
            self.select_npc(first_npc_name)
        else:
            self.go_to_workshop_new()

    def go_to_workshop_new(self):
        """Switches to the workshop tab with empty fields to create a new NPC."""
        self.populate_workshop_fields({})
        self.tabview.set("NPC Workshop")

    def go_to_workshop_edit(self):
        """Switches to the workshop tab with the selected NPC's data."""
        if self.selected_npc_name and self.selected_npc_name in self.npcs:
            self.populate_workshop_fields(self.npcs[self.selected_npc_name])
            self.tabview.set("NPC Workshop")
        else:
            logging.warning("Edit button clicked with no NPC selected.")

    def save_workshop_npc(self):
        """Gathers data from workshop fields and saves the NPC to the database."""
        new_name = self.workshop_name_entry.get().strip()
        if not new_name:
            self._update_textbox(self.workshop_status_textbox, "Error: NPC name cannot be empty.")
            return

        self._npc_in_workshop['name'] = new_name
        self._npc_in_workshop['race_class'] = self.workshop_race_entry.get()
        self._npc_in_workshop['appearance'] = self.workshop_appearance_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['personality'] = self.workshop_personality_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['backstory'] = self.workshop_backstory_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['plot_hooks'] = self.workshop_plothooks_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['roleplaying_tips'] = self.workshop_roleplaying_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['gender'] = self.gender_var.get()
        self._npc_in_workshop['attitude'] = self.attitude_var.get()
        self._npc_in_workshop['rarity'] = self.rarity_var.get()
        self._npc_in_workshop['environment'] = self.environment_var.get()
        self._npc_in_workshop['race'] = self.race_var.get()
        self._npc_in_workshop['character_class'] = self.class_var.get()
        self._npc_in_workshop['background'] = self.background_var.get()
        self._npc_in_workshop['custom_prompt'] = self.custom_prompt_textbox.get("1.0", "end-1c")

        all_db_keys = ["name", "race_class", "appearance", "personality", "backstory", "plot_hooks", "attitude",
                       "rarity", "race", "character_class", "environment", "background", "gender", "image_data",
                       "custom_prompt", "roleplaying_tips"]
        for key in all_db_keys:
            if key not in self._npc_in_workshop:
                self._npc_in_workshop[key] = None

        self.db.save_npc(self._npc_in_workshop, old_name=self._workshop_original_name)

        if self._workshop_original_name and self._workshop_original_name in self.npcs and self._workshop_original_name != new_name:
            del self.npcs[self._workshop_original_name]
        self.npcs[new_name] = self._npc_in_workshop.copy()

        self.update_npc_list()
        self.select_npc(new_name)

    def delete_npc(self):
        """Deletes the currently selected NPC from the database."""
        if self.selected_npc_name:
            self.db.delete_npc(self.selected_npc_name)
            del self.npcs[self.selected_npc_name]
            self.selected_npc_name = None
            self.populate_roster_fields({})
            self.update_npc_list()
            self.select_first_npc()

    def upload_portrait(self):
        """Opens a file dialog to upload an image for the NPC portrait."""
        try:
            file_path = filedialog.askopenfilename(title="Select a Portrait",
                                                   filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
            if file_path:
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                self._npc_in_workshop['image_data'] = image_bytes
                self._update_workshop_image_display()
                logging.info(f"Image loaded from {file_path}")
        except Exception as e:
            logging.error(f"Failed to upload image: {e}")
            self._update_textbox(self.workshop_status_textbox, "Error: Image Upload Failed.")

    def launch_simulator_app(self):
        """Closes the manager and launches the simulator with the selected NPC."""
        if not self.selected_npc_name:
            logging.warning("Launch simulator clicked with no NPC selected.")
            return

        self.destroy()
        npc_data = self.npcs.get(self.selected_npc_name)
        sim_app = NpcSimulatorApp(api_service=self.ai, data_manager=self.db, npc_data=npc_data)
        sim_app.mainloop()

    def start_generation_thread(self):
        """Starts a new thread for AI NPC generation to avoid freezing the UI."""
        if not self.ai.is_api_key_valid():
            self._update_textbox(self.workshop_status_textbox, "Error: Gemini API Key is missing or invalid.")
            return
        threading.Thread(target=self._run_generation_task, daemon=True).start()

    def _run_generation_task(self):
        """The actual task of calling the AI to generate NPC data."""
        self.after(0, lambda: self.generate_button.configure(state="disabled"))
        self.after(0, lambda: self._update_textbox(self.workshop_status_textbox, "Generating NPC with Gemini..."))
        try:
            params = {
                'gender': self.gender_var.get(),
                'attitude': self.attitude_var.get(),
                'rarity': self.rarity_var.get(),
                'environment': self.environment_var.get(),
                'race': self.race_var.get(),
                'character_class': self.class_var.get(),
                'background': self.background_var.get(),
                'custom_prompt': self.custom_prompt_textbox.get("1.0", "end-1c").strip()
            }
            npc_data, _ = self.ai.generate_npc(params)

            if self._npc_in_workshop and 'image_data' in self._npc_in_workshop:
                npc_data['image_data'] = self._npc_in_workshop.get('image_data')

            self.after(0, self.populate_workshop_fields, npc_data)
        except Exception as e:
            logging.error(f"Generation failed: {e}")
            self.after(0, lambda: self._update_textbox(self.workshop_status_textbox, f"Generation Error:\n\n{str(e)}"))
        finally:
            self.after(0, lambda: self.generate_button.configure(state="normal"))

    def start_image_generation_thread(self):
        """Starts a new thread for AI image generation."""
        if not self.ai.is_api_key_valid():
            self._update_textbox(self.workshop_status_textbox, "Error: API Key is missing.")
            return

        appearance_prompt = self.workshop_appearance_textbox.get("1.0", "end-1c").strip()
        if not appearance_prompt:
            self._update_textbox(self.workshop_status_textbox, "Error: 'Appearance' field must be filled out.")
            return

        threading.Thread(target=self._image_generation_worker, args=(appearance_prompt,), daemon=True).start()

    def _image_generation_worker(self, appearance_prompt):
        """The actual task of calling the AI to generate an image."""
        self.after(0, lambda: self._update_textbox(self.workshop_status_textbox, "Generating portrait..."))
        try:
            image_bytes = self.ai.generate_npc_portrait(appearance_prompt)
            self._npc_in_workshop['image_data'] = image_bytes
            self.after(0, self._update_workshop_image_display)
            self.after(0,
                       lambda: self._update_textbox(self.workshop_status_textbox, "Portrait generated successfully!"))
        except NotImplementedError as e:
            logging.warning(f"Image generation skipped: {e}")
            prompt_text = f"A digital painting portrait of a D&D character: {appearance_prompt}. Fantasy art, character concept, detailed, high quality."
            message = f"Feature requires a billed account.\n\nTo generate manually, use this prompt in an image generator:\n\n'{prompt_text}'"
            self.after(0, lambda: self._update_textbox(self.workshop_status_textbox, message))
        except Exception as e:
            logging.error(f"Image generation failed in worker: {e}")
            self.after(0,
                       lambda: self._update_textbox(self.workshop_status_textbox, f"Image Generation Failed:\n\n{e}"))