import customtkinter

class ConfirmationDialog(customtkinter.CTkToplevel):
    """
    A modal dialog window to get user confirmation (Yes/No).
    """
    def __init__(self, master, title="Confirm", message="Are you sure?", command=None):
        super().__init__(master)
        self.master = master
        self.command = command
        self._result = False

        self.title(title)
        self.geometry("350x150")
        self.resizable(False, False)
        self.grab_set()  # Make this window modal

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        message_label = customtkinter.CTkLabel(main_frame, text=message, wraplength=300)
        message_label.pack(pady=(0, 20), expand=True, fill="x")

        button_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack()

        yes_button = customtkinter.CTkButton(button_frame, text="Yes", command=self.on_yes, width=100)
        yes_button.pack(side="left", padx=10)

        no_button = customtkinter.CTkButton(button_frame, text="No", command=self.on_no, width=100, fg_color="gray50", hover_color="gray30")
        no_button.pack(side="left", padx=10)

    def on_yes(self):
        self._result = True
        if self.command:
            self.command()
        self.destroy()

    def on_no(self):
        self._result = False
        self.destroy()