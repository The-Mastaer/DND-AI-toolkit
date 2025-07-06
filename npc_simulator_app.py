import customtkinter
import threading
import logging
import io
from PIL import Image, UnidentifiedImageError


class NpcSimulatorApp(customtkinter.CTkToplevel):
    """
    A dedicated Toplevel window for simulating an NPC with different levels of detail.
    """

    def __init__(self, master, api_service, data_manager, npc_data=None, campaign_data=None):
        super().__init__(master)
        self.master = master
        self.ai = api_service
        self.db = data_manager
        self.npc_data = npc_data
        self.campaign_data = campaign_data or {}

        self.title("NPC Simulator")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.go_home)

        if self.npc_data:
            self._create_simulator_view()
        else:
            self._create_selection_view()

    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _create_selection_view(self):
        self._clear_window()
        self.title("NPC Simulator - Select an NPC")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        container = customtkinter.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, rowspan=2, padx=20, pady=20, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        title_label = customtkinter.CTkLabel(container, text="Select an NPC to Simulate",
                                             font=customtkinter.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="w")
        scrollable_frame = customtkinter.CTkScrollableFrame(container, label_text="Available NPCs")
        scrollable_frame.grid(row=1, column=0, sticky="nsew")
        home_button = customtkinter.CTkButton(container, text="🏠 Home", command=self.go_home)
        home_button.grid(row=2, column=0, pady=(10, 0), sticky="ew")
        npcs = self.db.load_data()
        if not npcs:
            customtkinter.CTkLabel(scrollable_frame, text="No NPCs found in the database.").pack(pady=20)
            return
        for name in sorted(npcs.keys()):
            button = customtkinter.CTkButton(scrollable_frame, text=name,
                                             command=lambda n=name: self._on_npc_selected(n))
            button.pack(pady=5, padx=10, fill="x")

    def _on_npc_selected(self, npc_name):
        npcs = self.db.load_data()
        self.npc_data = npcs.get(npc_name)
        if self.npc_data:
            self._create_simulator_view()
        else:
            logging.error(f"Failed to load data for selected NPC: {npc_name}")

    def _create_simulator_view(self):
        self._clear_window()
        npc_name = self.npc_data.get('name', 'Unknown NPC')
        self.title(f"Simulator: {npc_name}")
        self.grid_columnconfigure(0, weight=1, minsize=250)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        self._setup_sidebar()
        self._setup_main_content()

    def _setup_sidebar(self):
        sidebar = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(2, weight=1)
        portrait_image = self._create_ctk_image_from_data(self.npc_data.get("image_data"), size=(200, 200))
        portrait_label = customtkinter.CTkLabel(sidebar, image=portrait_image,
                                                text="" if portrait_image else "No Portrait")
        portrait_label.grid(row=0, column=0, padx=10, pady=10)
        portrait_label.image = portrait_image
        home_button = customtkinter.CTkButton(sidebar, text="🏠 Home", command=self.go_home)
        home_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        info_frame = customtkinter.CTkScrollableFrame(sidebar, label_text="Character Info")
        info_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        info_frame.grid_columnconfigure(0, weight=1)
        name_label = customtkinter.CTkLabel(info_frame, text=self.npc_data.get("name", "N/A"),
                                            font=customtkinter.CTkFont(size=16, weight="bold"), wraplength=200)
        name_label.pack(pady=(0, 5), fill="x")
        race_class_label = customtkinter.CTkLabel(info_frame, text=self.npc_data.get("race_class", "N/A"),
                                                  font=customtkinter.CTkFont(size=12), wraplength=200)
        race_class_label.pack(pady=(0, 10), fill="x")
        tags = [self.npc_data.get('gender'), self.npc_data.get('attitude'), self.npc_data.get('rarity')]
        tags_text = " | ".join(filter(None, tags))
        tags_label = customtkinter.CTkLabel(info_frame, text=tags_text, font=customtkinter.CTkFont(size=10),
                                            wraplength=200)
        tags_label.pack(pady=(0, 15), fill="x")
        customtkinter.CTkLabel(info_frame, text="Roleplaying Cues:",
                               font=customtkinter.CTkFont(size=12, weight="bold")).pack(fill="x")
        tips_textbox = customtkinter.CTkTextbox(info_frame, wrap="word", fg_color="transparent", border_width=0)
        tips_textbox.insert("1.0", self.npc_data.get("roleplaying_tips", "N/A"))
        tips_textbox.configure(state="disabled")
        tips_textbox.pack(pady=5, fill="both", expand=True)

    def _setup_main_content(self):
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

        customtkinter.CTkLabel(main_frame, text="Situation:", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                              column=0,
                                                                                                              pady=(0,
                                                                                                                    5),
                                                                                                              sticky="w")
        self.prompt_entry = customtkinter.CTkTextbox(main_frame, height=100, wrap="word")
        self.prompt_entry.grid(row=1, column=0, pady=5, sticky="nsew")
        self.prompt_entry.insert("1.0", "The players enter the tavern and approach your character...")

        customtkinter.CTkLabel(main_frame, text="NPC's Reaction:", font=customtkinter.CTkFont(weight="bold")).grid(
            row=2, column=0, pady=(10, 5), sticky="w")
        self.response_textbox = customtkinter.CTkTextbox(main_frame, wrap="word", state="disabled")
        self.response_textbox.grid(row=3, column=0, pady=5, sticky="nsew")

        # --- Bottom controls ---
        bottom_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, pady=(10, 0), sticky="ew")
        bottom_frame.grid_columnconfigure(1, weight=1)

        self.sim_type_var = customtkinter.StringVar(value="Short")
        sim_type_selector = customtkinter.CTkSegmentedButton(
            bottom_frame,
            values=["Short", "Long"],
            variable=self.sim_type_var
        )
        sim_type_selector.grid(row=0, column=0, padx=(0, 10))

        self.simulate_button = customtkinter.CTkButton(bottom_frame, text="Simulate Reaction", height=40,
                                                       command=self.start_simulation_thread)
        self.simulate_button.grid(row=0, column=1, sticky="ew")

    def go_home(self):
        self.master.deiconify()
        self.destroy()

    def start_simulation_thread(self):
        if not self.ai.is_api_key_valid():
            self._update_textbox(self.response_textbox, "Error: Gemini API Key is missing or invalid.")
            return
        threading.Thread(target=self._run_simulation_task, daemon=True).start()

    def _run_simulation_task(self):
        self.after(0, lambda: self.simulate_button.configure(state="disabled"))
        self.after(0, lambda: self._update_textbox(self.response_textbox, "Simulating with Gemini... Please wait."))
        try:
            situation = self.prompt_entry.get("1.0", "end-1c").strip()
            sim_type = self.sim_type_var.get()
            if not situation:
                self.after(0,
                           lambda: self._update_textbox(self.response_textbox, "Please enter a situation to simulate."))
                return

            response_text = self.ai.simulate_reaction(
                npc_data=self.npc_data,
                situation=situation,
                campaign_data=self.campaign_data,
                sim_type=sim_type
            )
            self.after(0, lambda: self._update_textbox(self.response_textbox, response_text))
        except Exception as e:
            logging.error(f"Simulation failed: {e}")
            self.after(0, lambda err=e: self._update_textbox(self.response_textbox, f"An error occurred:\n\n{err}"))
        finally:
            self.after(0, lambda: self.simulate_button.configure(state="normal"))

    def _update_textbox(self, textbox, text):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

    def _create_ctk_image_from_data(self, image_bytes, size=(300, 300)):
        if not image_bytes: return None
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            return customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        except (UnidentifiedImageError, io.UnsupportedOperation) as e:
            logging.error(f"Failed to create image from data: {e}")
            return None