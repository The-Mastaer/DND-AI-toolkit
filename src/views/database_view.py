from encodings.punycode import selective_find

import flet as ft
import asyncio
from services.supabase_service import SupabaseService
from functools import partial


class DatabaseView(ft.View):
    """
    A view dedicated to searching the game database for items, spells, etc.
    Features a master-detail layout with advanced filtering.
    """

    def __init__(self, page: ft.Page, supabase_service: SupabaseService):
        super().__init__()
        self.page = page
        self.supabase_service = supabase_service
        self.route = "/database"

        self.appbar = ft.AppBar(
            title=ft.Text("Search"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.go_back,
                tooltip="Back to Dashboard"
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        )

        # --- State Management ---
        self.selected_item = None
        self.current_tab = "Items"

        # --- Filter Controls ---
        # General
        self.search_name_field = ft.TextField(label="Name contains...", expand=True, on_submit=self.handle_search)
        self.search_button = ft.ElevatedButton(text="Search", on_click=self.handle_search)
        self.progress_ring = ft.ProgressRing(visible=False)

        # Item Filters
        self.item_category_dd = ft.Dropdown(label="Category",expand=True, options=[ft.dropdown.Option(c) for c in
                                                                       ["Weapon", "Armor", "Tool", "Adventuring Gear",
                                                                        "Wondrous item"]])
        self.item_rarity_dd = ft.Dropdown(label="Rarity",expand=True, options=[ft.dropdown.Option(r) for r in
                                                                   ["Common", "Uncommon", "Rare", "Very Rare",
                                                                    "Legendary"]])
        self.item_attunement_switch = ft.Switch(label="Requires Attunement", value=False)
        self.item_properties_field = ft.TextField(label="Properties contain...", on_submit=self.handle_search)
        self.item_min_cost_field = ft.TextField(label="Min Cost (gp)", keyboard_type=ft.KeyboardType.NUMBER,
                                                on_submit=self.handle_search,expand=True)
        self.item_max_cost_field = ft.TextField(label="Max Cost (gp)", keyboard_type=ft.KeyboardType.NUMBER,
                                                on_submit=self.handle_search,expand=True)

        self.item_filters = ft.Column([
            ft.Row([self.item_category_dd,self.item_rarity_dd]),
            self.item_properties_field,
            ft.Row([self.item_min_cost_field, self.item_max_cost_field]),
            self.item_attunement_switch
        ], visible=True)

        # Spell Filters
        self.spell_level_dd = ft.Dropdown(label="Level",expand=True, options=[ft.dropdown.Option(str(i)) for i in range(10)])
        self.spell_school_dd = ft.Dropdown(label="School",expand=True, options=[ft.dropdown.Option(s) for s in
                                                                    ["Abjuration", "Conjuration", "Divination",
                                                                     "Enchantment", "Evocation", "Illusion",
                                                                     "Necromancy", "Transmutation"]])
        self.spell_ritual_switch = ft.Switch(label="Ritual", value=False)
        self.spell_concentration_switch = ft.Switch(label="Concentration", value=False)

        self.spell_filters = ft.Column([
            self.spell_level_dd,
            self.spell_school_dd,
            ft.Row([self.spell_ritual_switch,self.spell_concentration_switch])
        ], visible=False)

        # --- Results & Detail Panes ---
        self.results_list = ft.ListView(expand=True, spacing=5)
        self.detail_card = ft.Column([ft.Text("Select an item to see details.", italic=True)],
                                     alignment=ft.MainAxisAlignment.CENTER,
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True,
                                     scroll=ft.ScrollMode.ADAPTIVE)

        # --- Main Layout ---
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.handle_tab_change,
            tabs=[ft.Tab(text="Items"), ft.Tab(text="Spells")],
        )

        filter_controls = ft.Column([
            self.search_name_field,
            self.item_filters,
            self.spell_filters,
            ft.Row([self.search_button, self.progress_ring]),
        ])

        left_pane = ft.Column([
            self.tabs,
            filter_controls,
            ft.Divider(),
            ft.Text("Results", style=ft.TextThemeStyle.HEADLINE_SMALL),
            self.results_list
        ], expand=1,alignment=ft.MainAxisAlignment.START)

        right_pane = ft.Container(
            content=self.detail_card,
            expand=2,
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=ft.border_radius.all(5)
        )

        self.controls = [ft.Row([left_pane, ft.VerticalDivider(width=1), right_pane], expand=True)]

    def go_back(self, e):
        """Navigates back to the main dashboard view."""
        self.page.go("/")

    async def handle_tab_change(self, e):
        self.current_tab = e.control.tabs[e.control.selected_index].text
        is_items_tab = self.current_tab == "Items"
        self.item_filters.visible = is_items_tab
        self.spell_filters.visible = not is_items_tab
        self.results_list.controls.clear()
        self.detail_card.controls = [ft.Text("Select an item to see details.", italic=True)]
        self.update()

    async def handle_search(self, e):
        self.progress_ring.visible = True
        self.update()

        filters = {}
        response = None

        try:
            if self.current_tab == "Items":
                filters['item_name__ilike'] = self.search_name_field.value
                filters['category'] = self.item_category_dd.value
                filters['rarity'] = self.item_rarity_dd.value
                filters['requires_attunement'] = self.item_attunement_switch.value or None
                filters['properties__ilike'] = self.item_properties_field.value

                # Safely parse cost filters
                try:
                    if self.item_min_cost_field.value:
                        filters['min_cost_gp'] = float(self.item_min_cost_field.value)
                except (ValueError, TypeError):
                    pass  # Ignore invalid input
                try:
                    if self.item_max_cost_field.value:
                        filters['max_cost_gp'] = float(self.item_max_cost_field.value)
                except (ValueError, TypeError):
                    pass  # Ignore invalid input

                response = await self.supabase_service.search_items_rpc(filters)

            elif self.current_tab == "Spells":
                table_name = "spells"
                if self.search_name_field.value: filters['spell_name__ilike'] = self.search_name_field.value
                if self.spell_level_dd.value: filters['level'] = int(self.spell_level_dd.value)
                if self.spell_school_dd.value: filters['school'] = self.spell_school_dd.value
                if self.spell_ritual_switch.value: filters['is_ritual'] = True
                if self.spell_concentration_switch.value: filters['requires_concentration'] = True
                response = await self.supabase_service.execute_advanced_search(table_name, filters)

            self.results_list.controls.clear()
            if response and response.data:
                for item in response.data:
                    name = item.get('item_name') or item.get('spell_name')
                    self.results_list.controls.append(
                        ft.ListTile(title=ft.Text(name), on_click=partial(self.show_details, item), data=item)
                    )
            else:
                self.results_list.controls.append(ft.Text("No results found."))
        except Exception as ex:
            self.results_list.controls.append(ft.Text(f"An error occurred: {repr(ex)}", color=ft.Colors.ERROR))

        self.progress_ring.visible = False
        self.update()

    async def show_details(self, item_data, e):
        self.selected_item = item_data

        card_content = []
        name = self.selected_item.get('item_name') or self.selected_item.get('spell_name', 'N/A')
        card_content.append(ft.Text(name, style=ft.TextThemeStyle.HEADLINE_MEDIUM))

        if self.current_tab == "Items":
            rarity = self.selected_item.get('rarity', 'N/A')
            category = self.selected_item.get('category', 'N/A')
            attunement = " (requires attunement)" if self.selected_item.get('requires_attunement') else ""
            card_content.append(ft.Text(f"{category}, {rarity}{attunement}", italic=True, color=ft.Colors.SECONDARY))

            cost = self.selected_item.get('cost_gp')
            weight = self.selected_item.get('weight_lb')
            cost_weight_parts = []
            if cost is not None: cost_weight_parts.append(f"Cost: {cost} gp")
            if weight is not None: cost_weight_parts.append(f"Weight: {weight} lb")
            if cost_weight_parts:
                card_content.append(ft.Text(" | ".join(cost_weight_parts)))

            card_content.append(ft.Divider())

            # --- Display properties from JSONB objects ---
            wp = self.selected_item.get('weapon_properties')
            if wp and wp.get('item_name'):
                card_content.append(ft.Text("Weapon Properties", style=ft.TextThemeStyle.TITLE_MEDIUM))
                dmg = f"{wp.get('damage_dice', '')} {wp.get('damage_type', '')}"
                card_content.append(ft.Text(f"Damage: {dmg}"))
                card_content.append(ft.Text(f"Properties: {wp.get('properties', 'N/A')}"))

            ap = self.selected_item.get('armor_properties')
            if ap and ap.get('item_name'):
                card_content.append(ft.Text("Armor Properties", style=ft.TextThemeStyle.TITLE_MEDIUM))
                card_content.append(ft.Text(f"Armor Class: {ap.get('ac_base', 'N/A')}"))
                if ap.get('stealth_disadvantage'):
                    card_content.append(ft.Text("Stealth: Disadvantage"))

            tp = self.selected_item.get('tool_properties')
            if tp and tp.get('item_name'):
                card_content.append(ft.Text("Tool Properties", style=ft.TextThemeStyle.TITLE_MEDIUM))
                card_content.append(ft.Text(f"Ability: {tp.get('ability', 'N/A')}"))

            description = self.selected_item.get('description', 'No description available.')
            card_content.append(ft.Divider())
            card_content.append(ft.Text(description, selectable=True))

        elif self.current_tab == "Spells":
            level = self.selected_item.get('level', 0)
            school = self.selected_item.get('school', 'N/A')
            level_text = f"{level}{'st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th'}-level {school}" if level > 0 else f"{school} cantrip"
            card_content.append(ft.Text(level_text, italic=True, color=ft.Colors.SECONDARY))
            card_content.append(ft.Divider())

            card_content.append(ft.Text(f"Casting Time: {self.selected_item.get('casting_time', 'N/A')}"))
            card_content.append(ft.Text(f"Range: {self.selected_item.get('range', 'N/A')}"))
            card_content.append(ft.Text(f"Components: {self.selected_item.get('components', 'N/A')}"))
            card_content.append(ft.Text(f"Duration: {self.selected_item.get('duration', 'N/A')}"))

            description = self.selected_item.get('description', 'No description available.')
            card_content.append(ft.Divider())
            card_content.append(ft.Text(description, selectable=True))

        self.detail_card.controls = card_content
        self.update()
