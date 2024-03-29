from io import StringIO
import functools
import logging
import os
import sys
import tempfile
import traceback
import typing as T
import websockets
from qasync import asyncSlot
from qasync import asyncClose
from qasync import QEventLoop
from fastapi_websocket_pubsub import PubSubClient
from fastapi_websocket_rpc.logger import logging_config, LoggingModes
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from client.client_env import ClientEnvironment, ClientState
from client.screens.base import GameWindow
from client.screens.battle_render import RenderWindow
from client.screens.pokemon_context_window import Ui as PokedexWindow
from client.screens.pokemon_item_window import Ui as PokeItemWindow

from engine.match import Matchmaker
from engine.models.battle import BattleRenderLog
from engine.models.enums import PokemonType
from engine.models.items import Item, ItemName, get_item_class_by_name
from engine.models.hero import Hero, HeroGrade
from engine.models.shop import ShopOffer
from engine.models.weather import WeatherType
from engine.player import Player
from engine.pokemon import EvolutionManager
from engine.pubsub import Message
from engine.sprites import SpriteManager
from engine.models.pokemon import Pokemon
from engine.models.state import State
from client.screens.player_item_window import Ui as PlayerItemWindow
from client.screens.debug_battle_window import Ui as DebugWindow
from client.screens.storage_window import Ui as StorageWindow
from engine.weather import WeatherManager
from utils.buttons import ItemButton, PokemonButton, clear_button_image, set_button_color, set_button_image
from utils.buttons import ShopPokemonButton
from utils.collections_util import extract_from_container_by_id
from utils.context import GameContext
from server.api.user import User
from utils.client import AsynchronousServerClient
from utils.collections_util import pad_list_to_length
from utils.strings import split_half_on_space
from engine.models.phase import GamePhase
from utils.error_window import error_window
from utils.websockets_client import WebSocketClient

if T.TYPE_CHECKING:
    pass

logging_config.set_mode(LoggingModes.UVICORN, level=logging.WARNING)


class Ui(QtWidgets.QMainWindow, GameWindow):

    DEBUG = os.environ.get('DEBUG')
    CREATE_AND_START_GAME = False

    def __init__(self, user, client: AsynchronousServerClient = None, game_id: str = None, websocket = None):
        super(Ui, self).__init__()
        self.user = user
        self.websocket = WebSocketClient(websocket)
        self.client = client

        self._state_callback_rising_edge = False

        # create an environment to support rendering
        self.env: ClientEnvironment = ClientEnvironment(8, id=game_id)
        # should load an initial state first?
        print('Initializing env')
        self.env.initialize()

        self.game_id = game_id

        uic.loadUi('client/qtassets/battlewindow.ui', self)

        # declare child pages
        self.render_window = None
        self.storage_window = None
        self.debug_window = None
        self.pokedex_window = PokedexWindow(self.env)
        self.poke_item_window = None
        self.player_item_window = None
        self.pubsub_client = PubSubClient()
        self.state: ClientState = None

        self.turns_rendered: T.Dict[int, bool] = dict()

        if self.DEBUG:
            self.debug_window = DebugWindow(self, self.env)

        # add buttons
        self.add_shop_interface()
        self.add_opposing_party_interface()
        self.add_party_interface()
        self.add_team_interface()
        self.add_message_interface()
        self.add_weather_interface()
        self.add_player_stats_interface()

        # register pokemon buttons for context window
        self.register_pokemon_buttons()

        self.render_functions = [
            self.render_party,
            self.render_shop,
            self.render_team,
            self.render_player_stats,
            self.render_opponent_party,
            self.render_time_to_next_stage,
            self.render_weather,
        ]

    @property
    def context(self):
        return GameContext(self.env, self.player)

    @property
    def player(self):
        return self.state.get_player_by_id(self.user.id)

    @property
    def player_hero(self):
        return self.state.player_hero[self.player.id]

    @property
    def shop_window(self) -> T.List[T.Union[ShopOffer, None]]:
        state: ClientState = self.state
        shop_window: T.List[ShopOffer] = state.shop_window[self.player]
        pad_list_to_length(shop_window, 5)
        return shop_window

    @property
    def party(self):
        """
        NOTE: the query attributes and instancing mechanisms don't seem to work in the client.
        I am not totally sure why that's the case.
        """
        return self.state.party(self.player)

    @property
    def team(self):
        return self.state.team(self.player)

    @property
    def storage(self):
        return [x for x in self.state.player_roster[self.player] if x not in self.party]

    @property
    def opposing_party(self):
        opponent = None
        if self.state.current_matches is not None:
            matchmaker: Matchmaker = self.env.matchmaker
            opponent_id = matchmaker.get_player_opponent_in_round(self.player, self.state.current_matches)
            opponent = self.state.get_player_by_id(opponent_id)
        if opponent is None:
            return [None] * 6
        opposing_party = self.state.party(opponent)
        return opposing_party

    @property
    def inventory(self):
        # re-populate inventory
        inventory: T.List[Item] = []
        for inv_raw in self.state.player_inventory[self.player]:
            if inv_raw.consumed:
                continue
            item_name = ItemName(inv_raw.name).name
            item_class = get_item_class_by_name(item_name)
            inventory.append(item_class(self.env, id=inv_raw.id))
        return inventory

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.RightButton:
            print('Right button clicked')
            # if the button supports pokedex context, open the window
            for button in self._pokemon_context_buttons:
                if button.button.underMouse():
                    # update and show context
                    self.pokedex_window.set_pokemon(button.pokemon)
                    self.pokedex_window.show()
                    self.pokedex_window.setWindowState(
                        self.pokedex_window.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive
                    )
                    self.pokedex_window.activateWindow()
                    return

        # if no context, hide context window
        self.pokedex_window.hide()

    def register_pokemon_buttons(self):
        """
        Find all Pokemon buttons that are a member of this window.

        Each Pokemon button should support right clicking for a context pop-up (Pokedex)
        The Pokedex should display information such as ATK, DEF, Primary / Secondary types,
        fast move type, charged move type, etc.
        """
        self._pokemon_context_buttons: T.List[PokemonButton] = []
        for attrname in dir(self):
            if attrname.startswith('_'):
                continue
            attr = getattr(self, attrname, None)
            if not attr:
                continue
            if isinstance(attr, PokemonButton):
                self._pokemon_context_buttons.append(attr)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, PokemonButton):
                        self._pokemon_context_buttons.append(item)
            # TODO: handle other kinds of containers
            else:
                continue

    def add_shop_interface(self):
        """
        Add shop interface buttons
        """
        self.shopLocationLabel = self.findChild(QtWidgets.QLabel, "shopLocationLabel")
        self.exploreWilds = self.findChild(QtWidgets.QPushButton, "exploreWilds")
        self.shopPokemon = [
            self.findChild(QtWidgets.QPushButton, "shopPokemon{}".format(idx))
            for idx in range(5)
        ]
        self.shop_pokemon_buttons: T.List[ShopPokemonButton] = []
        for idx, button in enumerate(self.shopPokemon):
            self.shop_pokemon_buttons.append(ShopPokemonButton(button, self.env, ''))
            prop = getattr(self, 'catch_pokemon_callback{}'.format(idx))
            button.clicked.connect(prop)

        self.exploreWilds.clicked.connect(self.roll_shop_callback)

    def add_party_interface(self):
        # party buttons
        self.manageItems = self.findChild(QtWidgets.QPushButton, "manageItems")
        self.manageItems.clicked.connect(self.open_player_item_window)
        self.manageStorage = self.findChild(QtWidgets.QPushButton, "manageStorage")
        self.manageStorage.clicked.connect(self.open_storage_window)
        self.partyLabel = [
            self.findChild(QtWidgets.QLabel, "party{}Label".format(idx))
            for idx in range(6)
        ]
        self.partyPokemon = [
            self.findChild(QtWidgets.QPushButton, "partyPokemon{}".format(idx))
            for idx in range(6)
        ]
        self.partyXp = [
            self.findChild(QtWidgets.QProgressBar, f"partyXp{idx}") for idx in range(6)
        ]
        # initialize to zero
        for xpbar in self.partyXp:
            xpbar.setFormat('')
            xpbar.setMaximum(1)
            xpbar.setValue(0)

        self.party_pokemon_buttons = [
            PokemonButton(
                self.partyPokemon[idx],
                self.env,
                "Party Pokemon {}".format(idx + 1),
                label=self.partyLabel[idx]
            )
            for idx in range(len(self.partyPokemon))
        ]
        self.addParty = [
            self.findChild(QtWidgets.QPushButton, "addParty{}".format(idx))
            for idx in range(6)
        ]
        self.partyItems = [
            self.findChild(QtWidgets.QPushButton, "partyItems{}".format(idx))
            for idx in range(6)
        ]
        self.party_item_buttons = [
            ItemButton(self.partyItems[idx], self.env, default_text="Items") for idx in range(6)
        ]
        for idx, add_party in enumerate(self.addParty):
            add_party.clicked.connect(getattr(self, f"add_to_team_callback{idx}"))
        for idx, party_items in enumerate(self.partyItems):
            party_items.clicked.connect(
                functools.partial(self.open_pokemon_item_window, idx)
            )

    def add_team_interface(self):
        # team buttons
        self.teamMember = [
            self.findChild(QtWidgets.QPushButton, "teamMember{}".format(idx))
            for idx in range(3)
        ]
        self.teamLabel = [
            self.findChild(QtWidgets.QLabel, "teamLabel{}".format(idx))
            for idx in range(3)
        ]
        self.team_member_button = [
            PokemonButton(
                self.teamMember[idx],
                self.env,
                default_text="Team {}".format(idx),
                label=self.teamLabel[idx]
            )
            for idx in range(len(self.teamMember))
        ]
        self.removeTeamMember = [
            self.findChild(QtWidgets.QPushButton, "removeTeamMember{}".format(idx))
            for idx in range(3)
        ]
        self.shiftTeamMemberUp = [
            self.findChild(QtWidgets.QPushButton, "shiftTeam{}Up".format(idx))
            for idx in range(3)
        ]
        self.shiftTeamMemberDown = [
            self.findChild(QtWidgets.QPushButton, "shiftTeam{}Down".format(idx))
            for idx in range(3)
        ]
        for idx in range(3):
            self.removeTeamMember[idx].clicked.connect(
                getattr(self, f"remove_team_member_callback{idx}")
            )
            self.shiftTeamMemberUp[idx].clicked.connect(
                getattr(self, f"shift_up_callback{idx}")
            )
            self.shiftTeamMemberDown[idx].clicked.connect(
                getattr(self, f"shift_down_callback{idx}")
            )

    def add_opposing_party_interface(self):
        # opposing party interface
        self.opponentName = self.findChild(QtWidgets.QLabel, "opponentName")
        self.opposingPokemon = [
            self.findChild(QtWidgets.QPushButton, "opposingPokemon{}".format(idx))
            for idx in range(6)
        ]
        self.opposingLabel = [
            self.findChild(QtWidgets.QLabel, "opposingLabel{}".format(idx))
            for idx in range(6)
        ]
        self.opposing_pokemon_buttons = [
            PokemonButton(
                self.opposingPokemon[idx],
                self.env,
                "Opponent {}".format(idx + 1),
                label=self.opposingLabel[idx]
            )
            for idx in range(6)
        ]

    def add_player_stats_interface(self):
        # player stats
        self.pokeBallCount = self.findChild(QtWidgets.QLineEdit, "pokeBallCount")
        self.energyCount = self.findChild(QtWidgets.QLineEdit, "energyCount")
        self.hitPoints = self.findChild(QtWidgets.QLineEdit, "hitPoints")
        self.masterBalls = self.findChild(QtWidgets.QLineEdit, "masterBalls")
        # player archetype, name, etc
        self.playerNameLabel = self.findChild(QtWidgets.QLabel, "playerNameLabel")
        self.playerArchetypeIcon = self.findChild(QtWidgets.QPushButton, "playerArchetypeIcon")
        self.playerArchetypeName = self.findChild(QtWidgets.QLabel, "playerArchetypeName")
        self.playerArchetypeAbility = self.findChild(QtWidgets.QLabel, "playerArchetypeAbility")
        self.playerArchetypeIconBackground = self.findChild(
            QtWidgets.QPushButton, "playerArchetypeIconBackground"
        )
        self.useAbility = self.findChild(QtWidgets.QPushButton, "useAbility")

        self.useAbility.clicked.connect(self.use_hero_power_callback)

    def add_stage_timer_interface(self):
        # time to next stage
        self.timeToNextStage = self.findChild(QtWidgets.QProgressBar, "timeToNextStage")

    def add_weather_interface(self):
        self.weatherIcon = self.findChild(QtWidgets.QPushButton, "weatherIcon")
        self.weatherType0 = self.findChild(QtWidgets.QPushButton, "weatherType0")
        self.weatherType1 = self.findChild(QtWidgets.QPushButton, "weatherType1")
        self.weatherType2 = self.findChild(QtWidgets.QPushButton, "weatherType2")

    def add_message_interface(self):
        # update log messages
        self.messages: T.List[Message] = []
        self.logMessages = self.findChild(QtWidgets.QTextBrowser, "logMessages")
        self.logMessages.moveCursor(QtGui.QTextCursor.End)

    def render_log_messages(self):
        """
        Update log messages

        TODO: don't recompute every time because it's probably getting really slow
        """
        self.logMessages.setText('\n'.join([msg.msg for msg in self.messages]))
        self.logMessages.moveCursor(QtGui.QTextCursor.End)

    def render_time_to_next_stage(self):
        state: "State" = self.state
        if state.phase not in [
            GamePhase.TURN_DECLARE_TEAM,
            GamePhase.TURN_PREPARE_TEAM,
            GamePhase.TURN_COMPLETE,
        ]:
            text = ""
            self.timeToNextStage.setFormat(text)
            self.timeToNextStage.setMaximum(1)
            self.timeToNextStage.setValue(0)
            return

        if state.phase == GamePhase.TURN_DECLARE_TEAM:
            text = "Party Declaration"
        elif state.phase == GamePhase.TURN_PREPARE_TEAM:
            text = "Team Preparation"
        elif state.phase == GamePhase.TURN_COMPLETE:
            text = "Match Complete"        

        # TODO: can probably just interpolate this based on starting time and get it
        # *HELLA* smooth (60fps baby)
        phase_time_ms = int(1E3 * state.t_phase_elapsed)
        if state.t_phase_duration != float('inf'):
            phase_duration_ms = int(1E3 * state.t_phase_duration)
        else:
            phase_time_ms = int(1E9)  # close enough eh?
        self.timeToNextStage.setFormat(text)
        self.timeToNextStage.setMaximum(phase_duration_ms)
        self.timeToNextStage.setValue(phase_time_ms)

    def open_storage_window(self):
        self.storage_window = StorageWindow(
            self,
            env=self.env,
            ctx=self.context,
            user=self.user,
            websocket=self.websocket,
        )

    def open_player_item_window(self):
        self.player_item_window = PlayerItemWindow(
            self,
            env=self.env,
            ctx=self.context,
            user=self.user,
            websocket=self.websocket,
        )

    def open_pokemon_item_window(self, party_idx: int):
        if self.party[party_idx] is None:
            return
        self.poke_item_window = PokeItemWindow(
            self,
            env=self.env,
            ctx=self.context,
            user=self.user,
            websocket=self.websocket,
            pokemon=self.party[party_idx]
        )

    def render_player_stats(self, update_player=False):
        player: Player = self.player
        self.pokeBallCount.setText(str(player.balls))
        self.energyCount.setText(str(player.energy))
        self.hitPoints.setText(str(player.hitpoints))
        self.masterBalls.setText(str(player.master_balls))

        # these don't change often so just check if the value is different
        if update_player:
            # fields might overflow, splitline if needed
            ability = split_half_on_space(self.player_hero.ability_name)
            self.playerNameLabel.setText(self.player.name)
            self.playerArchetypeName.setText(self.player_hero.name)
            self.playerArchetypeAbility.setText(ability)
            sprite_manager: SpriteManager = self.env.sprite_manager
            icon = sprite_manager.get_trainer_sprite(self.player_hero.name)
            if icon is not None:
                set_button_image(self.playerArchetypeIcon, icon, color=None)
                if self.player_hero._power == HeroGrade.PRISMATIC:
                    set_button_color(self.playerArchetypeIconBackground, 'gold')
                else:
                    set_button_color(self.playerArchetypeIconBackground, 'blue')
            else:
                clear_button_image(self.playerArchetypeIcon)

    def render_weather(self):
        weather_manager: WeatherManager = self.env.weather_manager
        weather = self.state.weather
        if weather is None or weather is WeatherType.NONE:
            self.weatherIcon.hide()
            self.weatherType0.hide()
            self.weatherType1.hide()
            self.weatherType2.hide()
            return
        sprite_manager: SpriteManager = self.env.sprite_manager
        icon = sprite_manager.get_weather_sprite(weather.name.lower())
        if icon is not None:
            # TODO: do a color lookup?
            set_button_image(self.weatherIcon, icon, color=None)
            self.weatherIcon.show()
        else:
            clear_button_image(self.weatherIcon)
            self.weatherIcon.setText(weather.name.capitalize())

        bonus_types = weather_manager.weather_bonuses[weather]
        for idx, button in enumerate((self.weatherType0, self.weatherType1, self.weatherType2)):
            try:
                type_enum: PokemonType = bonus_types[idx]
                type_icon = sprite_manager.get_type_sprite(type_enum.name)
                set_button_image(button, type_icon, "transparent")
                button.show()
            except IndexError:
                # clear button
                button.hide()
                clear_button_image(button)

    def render_opponent_party(self):
        player: Player = self.player
        state: ClientState = self.state
        matchmaker: Matchmaker = self.env.matchmaker
        if state.current_matches is not None:
            opponent_id = matchmaker.get_player_opponent_in_round(player, state.current_matches)
            if opponent_id is not None:
                opponent = self.state.get_player_by_id(opponent_id)

                sprite_manager: SpriteManager = self.env.sprite_manager
                if opponent.is_creep:
                    # set player icon from trainer sprites
                    icon = sprite_manager.get_pve_round_sprite(opponent.name.capitalize())
                else:
                    # set player icon from hero power
                    hero: Hero = self.state.player_hero[opponent.id]
                    icon = sprite_manager.get_trainer_sprite(hero.name.capitalize())
                set_button_image(self.opponentIcon, icon, 'transparent')

                self.opponentName.setText("{} ({})".format(opponent.name, opponent.hitpoints))
                for idx in range(6):
                    button = self.opposing_pokemon_buttons[idx]
                    pokemon = self.opposing_party[idx]
                    button.set_pokemon(pokemon)
                return

        self.opponentName.setText("No Match Scheduled")
        for idx in range(6):
            self.opposingPokemon[idx].setText("Opposing Pokemon {}".format(idx + 1))
            self.opposingPokemon[idx].setDisabled(True)

    def render_party(self):
        party = self.party
        evo_manager: EvolutionManager = self.env.evolution_manager
        for idx, party_member in enumerate(party):
            add_party_button = self.addParty[idx]
            item_button = self.party_item_buttons[idx]
            # render pokemon
            party_button = self.party_pokemon_buttons[idx]
            party_button.set_pokemon(party_member)
            if party_member is None:
                add_party_button.setDisabled(True)
                item_button.clear()
                continue
            else:
                add_party_button.setDisabled(False)

            # render item
            # TODO: refactor below
            poke_held_item_raw = self.state.pokemon_held_items_raw.get(party_member.id)
            if poke_held_item_raw is not None:
                item_name = ItemName(poke_held_item_raw.name).name
                item_class = get_item_class_by_name(item_name)
                item = item_class(self.env, id=poke_held_item_raw.id)
                item_button.set_item(item)
            else:
                item_button.clear()

            # render XP
            current_xp = party_member.xp
            max_xp = evo_manager.get_threshold(party_member.name) or 0
            self.partyXp[idx].setValue(current_xp)
            self.partyXp[idx].setMaximum(max_xp)

    def render_team(self):
        team = self.team
        arr = [x for x in team]
        if len(arr) < 3:
            arr.extend([None] * (3 - len(arr)))
        for idx, team_member in enumerate(arr):
            team_member_button = self.team_member_button[idx]
            remove_team_member = self.removeTeamMember[idx]
            shift_team_up = self.shiftTeamMemberUp[idx]
            shift_team_down = self.shiftTeamMemberDown[idx]
            team_member_button.set_pokemon(team_member)
            if team_member is None:
                remove_team_member.setDisabled(True)
                shift_team_up.setDisabled(True)
                shift_team_down.setDisabled(True)
            else:
                shift_team_up.setDisabled(False)
                shift_team_down.setDisabled(False)
                remove_team_member.setDisabled(False)

    def render_shop(self):
        for idx, offer in enumerate(self.shop_window):
            shop_button = self.shop_pokemon_buttons[idx]
            if offer.consumed:
                shop_button.set_pokemon(None)
            else:
                shop_button.set_pokemon(getattr(offer, 'pokemon', None))

        # update shop location
        if self.state.turn_number:
            route = self.state.stage.location
            self.shopLocationLabel.setText(route)

    async def _state_callback(self, topic, data):
        """
        Updates the state every time a pubsub message is received
        """

        # refresh references
        self.env.state = self.state = ClientState.parse_raw(data)

        if self.state.phase == GamePhase.TURN_RENDER:
            if not self.turns_rendered.get(self.state.turn_number, False):
                self.turns_rendered[self.state.turn_number] = True
                # pull the render file first
                render_model: BattleRenderLog = await self.websocket.render_battle(self.context)
                render_html = render_model.render
                # TODO(albert/will): shouldn't use game directory as working directory for temp
                _, output_path = tempfile.mkstemp(
                    prefix="temp_battle_",
                    dir=os.getcwd(),
                    suffix='.html'
                )
                print(f'RENDERING FILE AT {output_path}')
                with open(output_path, 'w+') as out:
                    out.write(render_html)
                self.render_window = RenderWindow(self, output_path, websocket=self.websocket)

        if not self._state_callback_rising_edge:
            self.render_player_stats(update_player=True)
            self._state_callback_rising_edge = True

        for method in self.render_functions:
            try:
                method()
            except Exception as exc:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback)
                print(f'Failed to run {method}:\n{repr(exc)}')

        # if other windows are alive, update those too?
        if self.storage_window is not None:
            self.storage_window.update_state()
            self.storage_window.render_party()
            self.storage_window.render_storage()

        if self.debug_window is not None:
            self.debug_window.update_game_phase()

        if self.poke_item_window is not None:
            self.poke_item_window.update_state()
            self.poke_item_window.render()

    async def _message_callback(self, topic, data):
        """
        Updates the message log
        """
        try:
            msg = Message.parse_raw(data)
            self.messages.append(msg)
        except Exception as exc:
            print(f'Failed to parse message: {repr(exc)}')
            raise
        self.render_log_messages()

    @asyncSlot()
    async def use_hero_power_callback(self):
        print("Using hero power")
        await self.websocket.use_hero_power(self.context)

    @asyncSlot()
    async def roll_shop_callback(self):
        print("Rolling shop")
        await self.websocket.roll_shop(self.context)

    async def test_catch_pokemon_callback(self, idx):
        print("Acquiring Pokemon at index {}".format(idx))
        return await self.client.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback(self, idx):
        print("Acquiring Pokemon at index {}".format(idx))
        await self.websocket.catch_pokemon(self.context, idx)

    # TODO: i hate this so much but i'm not smart enough to do something better
    # i will come back to this i swear
    @asyncSlot()
    async def catch_pokemon_callback0(self):
        idx = 0
        print(f"Acquiring Pokemon at index {idx}")
        await self.websocket.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback1(self):
        idx = 1
        print("Acquiring Pokemon at index 1")
        await self.websocket.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback2(self):
        idx = 2
        print("Acquiring Pokemon at index 2")
        await self.websocket.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback3(self):
        idx = 3
        print(f"Acquiring Pokemon at index {idx}")
        await self.websocket.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback4(self):
        idx = 4
        print(f"Acquiring Pokemon at index {idx}")
        await self.websocket.catch_pokemon(self.context, idx)

    @asyncSlot()
    def add_to_team_callback(self, idx):
        return self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback0(self):
        # update party config first and then make the websocket client call
        idx = 0
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def add_to_team_callback1(self):
        idx = 1
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def add_to_team_callback2(self):
        idx = 2
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def add_to_team_callback3(self):
        idx = 3
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def add_to_team_callback4(self):
        idx = 4
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def add_to_team_callback5(self):
        idx = 5
        self.player.party_config.add_to_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def remove_team_member_callback(self, idx):
        print("Removing team member at idx {} from team".format(idx))

    @asyncSlot()
    async def remove_team_member_callback0(self):
        idx = 0
        print("Removing team member at idx {} from team".format(idx))
        self.player.party_config.remove_from_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def remove_team_member_callback1(self):
        idx = 1
        print("Removing team member at idx {} from team".format(idx))
        self.player.party_config.remove_from_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def remove_team_member_callback2(self):
        idx = 2
        print("Removing team member at idx {} from team".format(idx))
        self.player.party_config.remove_from_team_by_idx(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def shift_up_callback0(self):
        return

    @asyncSlot()
    async def shift_up_callback1(self):
        idx = 1
        print("Shifting team member at {} up".format(idx))
        self.player.party_config.shift_team_up(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def shift_up_callback2(self):
        idx = 2
        print("Shifting team member at {} up".format(idx))
        self.player.party_config.shift_team_up(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def shift_down_callback0(self):
        idx = 0
        print("Shifting team member at {} down".format(idx))
        self.player.party_config.shift_team_down(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def shift_down_callback1(self):
        idx = 1
        print("Shifting team member at {} down".format(idx))
        self.player.party_config.shift_team_down(idx)
        return await self.websocket.update_party_config(self.context, self.player.party_config)

    @asyncSlot()
    async def shift_down_callback2(self):
        return

    def subscribe_pubsub_state(self):
        pubsub_topic = f"pubsub-state-{str(self.user.id)}-{self.game_id}"
        self.pubsub_client.subscribe(pubsub_topic, callback=self._state_callback)

    def subscribe_pubsub_messages(self):
        msg_global = f"pubsub-msg-all-{self.game_id}"
        msg_player = f"pubsub-msg-{self.user.id}-{self.game_id}"
        self.pubsub_client.subscribe(msg_player, callback=self._message_callback)
        self.pubsub_client.subscribe(msg_global, callback=self._message_callback)

    @asyncClose
    async def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
        # check if debug window exists and close it as well
        if self.debug_window is not None:
            self.debug_window.close()
        if self.poke_item_window is not None:
            self.poke_item_window.close()
        if self.pokedex_window is not None:
            self.pokedex_window.close()
        if self.storage_window is not None:
            self.storage_window.close()

        # have the player leave the game
        if self.game_id is not None:
            await self.client.leave_game(self.game_id, self.player)
            if not len(await self.client.get_players(self.game_id)):
                print('Deleting game because last player left')
                await self.client.delete_game(self.game_id, force=True)


async def main():
    print('doing shit')
    SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS', 'http://76.210.142.219:8000')
    ws_addr = f"{SERVER_ADDRESS.replace('http://', 'ws://')}/game_buttons"
    pubsub_addr = f"{SERVER_ADDRESS.replace('http://', 'ws://')}/pubsub"
    print('making websocket')
    try:
        ws = await websockets.connect(ws_addr)
    except Exception:
        error_window('Unable to connect to game')
        raise

    window = Ui(server_addr=SERVER_ADDRESS, websocket=ws)

    loop = asyncio.get_event_loop()
    if os.environ.get('CREATE_AND_START_GAME', False):
        task = loop.create_task(window.client.create_game())
        await task
        game = task.result()
        print(game)
        game_id = game.game_id
        window.env._id = game_id
        window.game_id = game_id
    else:
        game_id = 'a7c0ed20-b580-446d-97cb-3da0ecb3f2a6'

    # join the game with the current user
    player = window.create_player()
    await loop.create_task(window.client.join_game(game_id, player))
    window.show()
    window.subscribe_pubsub_state()
    window.subscribe_pubsub_messages()
    window.pubsub_client.start_client(pubsub_addr, loop=loop)
    print('started pubsub')
    await window.pubsub_client.wait_until_done()
    print('wait what')


if __name__ == "__main__":
    import asyncio
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    coro = main()
    loop.run_until_complete(coro)
