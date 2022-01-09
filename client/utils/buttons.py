"""
Helpers for buttons
"""
from PyQt5.QtWidgets import QPushButton

from engine.pokemon import Pokemon
from engine.shop import ShopManager
from engine.sprites import SpriteManager

TRANSPARENT_IMAGE = '{}'


def clear_button_image(button):
    """
    Reset the button image
    """
    button.setStyleSheet("border: 1px solid;")


def set_button_image(button, image, color):
    """
    Set a scaled image with background color
    """
    button.setStyleSheet(
        "border-image: url('{image}');"
        "background-color: {color};"
        .format(image=image, color=color)
    )


def set_border_color(button: QPushButton, color: str, width: int = 5) -> None:
    """
    Set a border and a color
    """
    button.setStyleSheet(
        "border: {width}px solid;"
        "border-top-color: {color};"
        "border-left-color: {color};"
        "border-right-color: {color};"
        "border-bottom-color: {color};"
        .format(width=width, color=color)
    )


def set_border_color_and_image(button, image, color, width=5):
    button.setStyleSheet(
        "border-image: url('{image}');"
        "border: {width}px solid;"
        "border-top-color: {color};"
        "border-left-color: {color};"
        "border-right-color: {color};"
        "border-bottom-color: {color};"
        .format(image=image, width=width, color=color)
    )


class PokemonButton:
    """
    Wraps a QPushButton.

    Renders a Pokemon sprite or text or blank, depending on configuration.
    """

    def __init__(self, button, state, default_text=""):
        self.button: QPushButton = button
        self.state = state
        self.default_text = default_text
        # TODO: add some more config options here probably

    def clear(self):
        clear_button_image(self.button)
        self.button.setText(self.default_text)

    def render_shop_card(self, pokemon_name: str):
        """
        Render a Pokemon shop card (string)
        """
        if not pokemon_name:
            self.clear()
            self.disable()
            return

        self.enable()
        sprite_manager: SpriteManager = self.state.sprite_manager
        sprite = sprite_manager.get_normie_sprite(pokemon_name)

        if sprite is None:
            # set text to pokemon name
            clear_button_image(self.button)
            self.button.setText(pokemon_name)
        else:
            self.button.setText('')
            shop_manager: ShopManager = self.state.shop_manager
            tier = shop_manager.pokemon_tier_lookup[pokemon_name]
            color = shop_manager.tier_colors[tier]
            set_button_image(self.button, sprite, color)

    def enable(self):
        self.button.setDisabled(False)

    def disable(self):
        self.button.setDisabled(True)

    def render_pokemon_card(self, pokemon: Pokemon):
        """
        Use game state info to render a Pokemon.
        """
        if pokemon is None:
            self.clear()
            self.disable()
            return

        self.enable()
        sprite_manager: SpriteManager = self.state.sprite_manager
        if pokemon.battle_card.shiny:
            sprite = sprite_manager.get_shiny_sprite(pokemon.name)
        else:
            sprite = sprite_manager.get_normie_sprite(pokemon.name)

        if sprite is None:
            # set text to pokemon name
            clear_button_image(self.button)
            self.button.setText(pokemon.nickname)
        else:
            set_button_image(self.button, sprite, "transparent")
            self.button.setText('')
