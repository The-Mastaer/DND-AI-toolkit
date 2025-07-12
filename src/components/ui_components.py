# src/components/ui_components.py

import flet as ft

def create_compact_textfield(label: str, multiline: bool = False, min_lines: int = 1, expand: bool = False) -> ft.TextField:
    """
    Creates a compact ft.TextField with consistent styling.

    Args:
        label (str): The label for the text field.
        multiline (bool): Whether the text field should be multiline.
        min_lines (int): The minimum number of lines for a multiline field.
        expand (bool): Whether the text field should expand to fill available width.

    Returns:
        ft.TextField: A configured Flet TextField control.
    """
    return ft.TextField(
        label=label,
        multiline=multiline,
        min_lines=min_lines,
        text_size=12,
        dense=True,
        expand=expand
    )

def create_compact_dropdown(label: str, options: list[str], expand: bool = False) -> ft.Dropdown:
    """
    Creates a compact ft.Dropdown with consistent styling, including a "Random" option.

    Args:
        label (str): The label for the dropdown.
        options (list[str]): A list of string options for the dropdown.
        expand (bool): Whether the dropdown should expand to fill available width.

    Returns:
        ft.Dropdown: A configured Flet Dropdown control.
    """
    return ft.Dropdown(
        label=label,
        options=[ft.dropdown.Option("Random")] + [ft.dropdown.Option(opt) for opt in options],
        value="Random",
        text_size=12,
        dense=True,
        expand=expand
    )
