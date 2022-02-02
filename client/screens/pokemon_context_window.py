"""
Context Window
"""
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from engine.models.pokemon import SHINY_STAT_MULT
from engine.models.enums import PokemonType
from engine.models.stats import Stats
from engine.utils.battle_utils import atk_per_sec

from utils.buttons import clear_button_image
from utils.buttons import set_button_image

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.gamemaster import GameMaster
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
        self.spdStat = self.findChild(QtWidgets.QLineEdit, "spdStat")

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

        battle_card = pokemon.battle_card
        atk_base = battle_card.atk_
        def_base = battle_card.def_
        hp_base = battle_card.health

        atk_ = atk_base + pokemon.modifiers[Stats.ATK]
        def_ = def_base + pokemon.modifiers[Stats.DEF]
        hp_ = hp_base + pokemon.modifiers[Stats.HP]
        spd_ = battle_card.spd_ + pokemon.modifiers[Stats.SPD]
        atk_per_sec_ = battle_card.atk_per_sec_for_spd_stat(spd_)

        self.atkStat.setText(str(int(atk_)))
        self.defStat.setText(str(int(def_)))
        self.hpStat.setText(str(int(hp_)))
        self.spdStat.setText(str("{:.2f}".format(atk_per_sec)))

        # TODO: set modified colors if there are any
        if pokemon.modifiers[Stats.ATK] or pokemon.battle_card.shiny:
            self.atkStat.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.atkStat.setStyleSheet("color: black;")

        if pokemon.modifiers[Stats.DEF] or pokemon.battle_card.shiny:
            self.defStat.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.defStat.setStyleSheet("color: black;")

        if pokemon.modifiers[Stats.HP] or pokemon.battle_card.shiny:
            self.hpStat.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.hpStat.setStyleSheet("color: black;")

        if atk_per_sec_ > battle_card.atk_per_secL
            self.spdStat.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.spdStat.setStyleSheet("color: black;")

        pokemon_name = pokemon.name.name
        primary_type, secondary_type = pokemon_factory.get_pokemon_type_reference(pokemon_name)
        self.set_type_icon(self.primaryTypeIcon, primary_type.name)
        if secondary_type is None or secondary_type == PokemonType.none:
            secondary_type = primary_type
        self.set_type_icon(self.secondaryTypeIcon, secondary_type.name)

        self.set_type_icon(self.fastMoveTypeIcon, pokemon.battle_card.f_move_type.name)
        self.set_type_icon(self.chargeMoveTypeIcon, pokemon.battle_card.ch_move_type.name)

        # only set TM if enabled
        if pokemon.battle_card.tm_flag:
            self.set_type_icon(self.tmMoveTypeIcon, pokemon.battle_card.tm_move_type.name)
        else:
            clear_button_image(self.tmMoveTypeIcon)

        if pokemon.battle_card.shiny:
            sprite = sprite_manager.get_shiny_sprite(pokemon_name)
        else:
            sprite = sprite_manager.get_normie_sprite(pokemon_name)
        if not sprite:
            self.pokemonPicture.setText(pokemon.nickname)
        else:
            self.pokemonPicture.setText('')
            set_button_image(self.pokemonPicture, sprite, "transparent")

    def set_type_icon(self, icon: QtWidgets.QPushButton, _type: str):
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
