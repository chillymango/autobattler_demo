"""
Context Window
"""
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

from utils.buttons import clear_button_image
from utils.buttons import set_button_image

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.models.pokemon import Pokemon
    from engine.pokemon import PokemonFactory
    from engine.sprites import SpriteManager


class Ui(QtWidgets.QMainWindow):
    """
    Context Window ("Pokedex")
    """

    def __init__(self, env: "Environment", pokemon=None):
        super(Ui, self).__init__()
        self.setStyleSheet("background-color: rgb(255,179,179); "
                           "border: 3px red")
        uic.loadUi('client/qtassets/contextwindow.ui', self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowTitle("Pokedex")
        self.env = env
        self.pokemon = pokemon

        # declare fields to populate
        self.atkStat = self.findChild(QtWidgets.QLineEdit, "atkStat")
        self.defStat = self.findChild(QtWidgets.QLineEdit, "defStat")
        self.hpStat = self.findChild(QtWidgets.QLineEdit, "hpStat")

        # type icons
        self.primaryTypeIcon = self.findChild(QtWidgets.QPushButton, "primaryTypeIcon")
        self.secondaryTypeIcon = self.findChild(QtWidgets.QPushButton, "secondaryTypeIcon")
        self.fastMoveTypeIcon = self.findChild(QtWidgets.QPushButton, "fastMoveTypeIcon")
        self.chargeMoveTypeIcon = self.findChild(QtWidgets.QPushButton, "chargeMoveTypeIcon")
        self.tmMoveTypeIcon = self.findChild(QtWidgets.QPushButton, "tmMoveTypeIcon")

        # pokemon picture
        self.pokemonPicture = self.findChild(QtWidgets.QPushButton, "pokemonPicture")
        self.pokemonName = self.findChild(QtWidgets.QLabel, "pokemonName")

        self.offset = self.pos()

    def clear(self):
        """
        Input blanks for everything
        """
        self.atkStat.setText('')
        self.defStat.setText('')
        self.hpStat.setText('')
        clear_button_image(self.primaryTypeIcon)
        clear_button_image(self.secondaryTypeIcon)
        clear_button_image(self.fastMoveTypeIcon)
        clear_button_image(self.chargeMoveTypeIcon)
        clear_button_image(self.tmMoveTypeIcon)
        clear_button_image(self.pokemonPicture)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.offset = event.pos()

    def mouseMoveEvent(self, event) -> None:
        # if the left-mouse is pressed, move the window
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def set_pokemon(self, pokemon: "Pokemon"):
        self.pokemon: "Pokemon" = pokemon
        if pokemon is None:
            self.clear()
            return

        self.pokemonName.setText(self.pokemon.nickname)
        sprite_manager: "SpriteManager" = self.env.sprite_manager
        pokemon_factory: "PokemonFactory" = self.env.pokemon_factory

        # TODO: implement full stat calc formula
        _atk = pokemon.battle_card.a_iv
        _def = pokemon.battle_card.d_iv
        _hp = pokemon.battle_card.hp_iv

        self.atkStat.setText(str(_atk))
        self.defStat.setText(str(_def))
        self.hpStat.setText(str(_hp))

        primary_type, secondary_type = pokemon_factory.get_pokemon_type_reference(pokemon.name)
        self.set_type_icon(self.primaryTypeIcon, primary_type)
        if secondary_type is None:
            secondary_type = primary_type
        self.set_type_icon(self.secondaryTypeIcon, secondary_type)

        self.set_type_icon(self.fastMoveTypeIcon, pokemon.battle_card.f_move_type)
        self.set_type_icon(self.chargeMoveTypeIcon, pokemon.battle_card.ch_move_type)

        # only set TM if enabled
        if pokemon.battle_card.tm_flag:
            self.set_type_icon(self.tmMoveTypeIcon, pokemon.battle_card.tm_move_type)
        else:
            clear_button_image(self.tmMoveTypeIcon)

        if pokemon.battle_card.shiny:
            sprite = sprite_manager.get_shiny_sprite(pokemon.name)
        else:
            sprite = sprite_manager.get_normie_sprite(pokemon.name)
        if not sprite:
            self.pokemonPicture.setText(pokemon.nickname)
        else:
            self.pokemonPicture.setText('')
            set_button_image(self.pokemonPicture, sprite, "transparent")

    def set_type_icon(self, icon, _type):
        """
        Set a type icon
        """
        if _type is None:
            clear_button_image(icon)
            icon.setText('')
            return

        sprite_manager: "SpriteManager" = self.env.sprite_manager
        type_icon = sprite_manager.get_type_sprite(_type)
        if type_icon is None:
            icon.setText(_type)
        else:
            icon.setText('')
            set_button_image(icon, type_icon, "transparent")
