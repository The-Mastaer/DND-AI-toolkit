import flet as ft

class ChatBubble(ft.Row):
    """
    A custom chat bubble widget, rebuilt for Flet 1.0+.
    Inherits from Row to align its content.
    """

    def __init__(self, message, role="user"):
        super().__init__()
        self.message = message
        self.role = role

        self.text_control = ft.Text(
            value=self.message,
            selectable=True,
            width=600,
            font_family="Roboto" # Ensure consistent font
        )

        if self.role == "user":
            # Use string-based theme colors
            bubble_color = "primary_container"
            self.alignment = ft.MainAxisAlignment.END
        else:
            # Use string-based theme colors
            bubble_color = "secondary_container"
            self.alignment = ft.MainAxisAlignment.START

        self.bubble_card = ft.Card(
            content=ft.Container(
                content=self.text_control,
                padding=10,
            ),
            color=bubble_color,
            elevation=2
        )

        self.controls = [self.bubble_card]

    def update_message(self, new_message):
        """Allows updating the bubble's text after it has been created."""
        self.text_control.value = new_message
        self.update()