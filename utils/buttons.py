"""
Helpers for buttons
"""
from email.charset import QP
import typing as T
from PyQt5.QtWidgets import QLabel, QPushButton
from engine.models.enums import PokemonId
from engine.models.items import Item

from engine.models.pokemon import Pokemon
from engine.shop import ShopManager
from engine.sprites import SpriteManager

if T.TYPE_CHECKING:
    from engine.pokemon import PokemonFactory

TRANSPARENT_IMAGE = '{}'


def clear_button_image(button):
    """
    Reset the button image
    """
    button.setStyleSheet("border: 1px solid;")

def set_button_color(button, color):
    button.setText('')
    button.setStyleSheet("background-color: {color};".format(color=color))


def set_button_image(button, image, color):
    """
    Set a scaled image with background color
    """
    button.setText('')
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


class SpriteButton:
    """
    Wraps a QPushButton.

    Renders a sprite or text or blank, depending on configuration.
    """

    def __init__(self, button, env, default_text="", label=None):
        self.button: QPushButton = button
        self.label: QLabel = label
        self.env = env
        self.default_text = default_text

    def clear(self):
        clear_button_image(self.button)
        self.set_label('')
        self.button.setText(self.default_text)

    def set_label(self, text):
        if self.label:
            self.label.setText(text)

    def enable(self):
        self.button.setDisabled(False)

    def disable(self):
        self.button.setDisabled(True)


class ItemButton(SpriteButton):
    """
    Wraps a QPushButton

    Renders an item sprite or text or blank, depending on configuration.
    """

    def __init__(self, button, env, default_text="", label=None):
        super().__init__(button, env, default_text=default_text, label=label)
        self.item: Item = None

    def set_item(self, item: T.Optional[Item]):
        self.item = item
        self.render_item()

    def render_item(self):
        if self.item is None:
            self.clear()
            self.disable()
            return

        self.enable()
        sprite_manager: SpriteManager = self.env.sprite_manager
        sprite = sprite_manager.get_item_sprite(self.item.__class__)
        if sprite is not None:
            # TODO: implement item tier colors here
            set_button_image(self.button, sprite, "transparent")
            self.button.setText('')
            self.set_label(str(self.item))
        else:
            clear_button_image(self.button)
            self.button.setText(str(self.item))
            self.set_label('')


class PokemonButton(SpriteButton):

    def __init__(self, button, env, default_text="", label=None):
        super().__init__(button, env, default_text=default_text, label=label)
        self.pokemon: Pokemon = None
        # TODO: add some more config options here probably

    def set_pokemon(self, pokemon: T.Optional[Pokemon]):
        self.pokemon = pokemon
        self.render_pokemon_card(pokemon)

    def render_pokemon_card(self, pokemon: Pokemon):
        """
        Use game state info to render a Pokemon.
        """
        if pokemon is None:
            self.clear()
            self.disable()
            return

        self.enable()
        sprite_manager: SpriteManager = self.env.sprite_manager
        if pokemon.battle_card.shiny:
            sprite = sprite_manager.get_shiny_sprite(pokemon.name.name)
        else:
            sprite = sprite_manager.get_normie_sprite(pokemon.name.name)

        if sprite is None:
            # set text to pokemon name
            clear_button_image(self.button)
            self.button.setText(str(pokemon))
            self.set_label('')
        else:
            set_button_image(self.button, sprite, "transparent")
            self.button.setText('')
            self.set_label(str(pokemon))


class ShopPokemonButton(PokemonButton):
    """
    Renders a Shop Pokemon.

    A shop Pokemon is not yet instantiated and does not have any unique characteristics to display.
    Defaults should be used when rendering context.
    """

    def __init__(self, button, state, default_text=""):
        super().__init__(button, state, default_text=default_text)

    def set_pokemon(self, pokemon_id_enum: PokemonId):
        if pokemon_id_enum is None:
            self.clear()
            self.disable()
            return

        pokemon_name = pokemon_id_enum.name
        pokemon_factory: PokemonFactory = self.env.pokemon_factory
        if self.pokemon is None:
            # create new object
            self.pokemon = pokemon_factory.create_pokemon_by_name(pokemon_name)
        elif pokemon_name != self.pokemon.name.name:
            # create new default
            # delete old object first
            self.pokemon.delete()
            self.pokemon = pokemon_factory.create_pokemon_by_name(pokemon_name)

        # otherwise can assume it did not change and no need to instantiate a new one
        self.render_pokemon_card(self.pokemon)

    def render_pokemon_card(self, pokemon: Pokemon):
        """
        Render a Pokemon shop card (string)
        """
        if not pokemon:
            self.clear()
            self.disable()
            return

        sprite_key: str = pokemon.name.name
        self.enable()
        sprite_manager: SpriteManager = self.env.sprite_manager
        sprite = sprite_manager.get_normie_sprite(sprite_key)

        if sprite is None:
            # set text to pokemon name
            clear_button_image(self.button)
            self.button.setText(str(pokemon))
        else:
            self.button.setText('')
            shop_manager: ShopManager = self.env.shop_manager
            tier = shop_manager.pokemon_tier_lookup[sprite_key]
            color = shop_manager.tier_colors[tier]
            set_button_image(self.button, sprite, color)
