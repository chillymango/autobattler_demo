import functools
import logging
import os
import sys
import typing as T
from asyncqt import asyncSlot
from asyncqt import asyncClose
from asyncqt import QEventLoop
from fastapi_websocket_pubsub import PubSubClient
from fastapi_websocket_rpc.logger import logging_config, LoggingModes
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from client.client_env import ClientEnvironment
from client.screens.base import AsyncCallback
from engine.match import Match
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player
from engine.shop import ShopManager
from engine.state import GamePhase
from engine.state import State
from client.screens.debug_battle_window import Ui as DebugWindow
from client.screens.storage_window import Ui as StorageWindow
from client.utils.buttons import set_border_color, set_border_color_and_image, set_button_image
from client.utils.buttons import clear_button_image
from client.utils.buttons import PokemonButton
from server.api.player import Player as PlayerModel
from utils.async_util import async_partial
from utils.context import GameContext
from utils.user import User
from utils.client import AsynchronousServerClient, GameServerClient

if T.TYPE_CHECKING:
    pass

logging_config.set_mode(LoggingModes.UVICORN, level=logging.WARNING)


class Ui(QtWidgets.QMainWindow):

    DEBUG = os.environ.get('DEBUG')

    def __init__(self, server_addr: str = None, game_id: str = None):
        super(Ui, self).__init__()
        self.server_addr = server_addr
        #game_id = self.create_and_join_game()
        game_id = 'a3414ef8-1231-4c79-8cd1-4fde53a6c9be'
        self.client = AsynchronousServerClient(bind=server_addr)
        client = GameServerClient(self.server_addr)
        self.create_player()
        client.join_game(game_id, self.player)

        # create an environment to support rendering
        self.env: ClientEnvironment = ClientEnvironment(8, id=game_id)
        self.context: GameContext = GameContext(self.env, self.player)
        # should load an initial state first?
        self.env.initialize()

        self.game_id = game_id

        uic.loadUi('client/qtassets/battlewindow.ui', self)

        self.pubsub_client = PubSubClient()
        self.state = None

        # register remote state callbacks here
        self.pubsub_client.subscribe(f"pubsub-{game_id}", callback=self._state_callback)

        if self.DEBUG:
            self.window = DebugWindow(self.env, ctx=self.context)
            self.window.battle_window = self

        # add buttons
        self.add_shop_interface()
        self.add_opposing_party_interface()
        self.add_party_interface()
        self.add_team_interface()

        self.render_functions = [
            self.render_party,
            self.render_shop,
            self.render_team,
            self.render_player_stats,
            self.render_opponent_party,
            #self.render_time_to_next_stage,
            #self.render_log_messages,
        ]

    def create_and_join_game(self):
        # oh boy man
        client = GameServerClient(self.server_addr)
        #game = client.create_game()

    def create_player(self):
        # create Player objects
        # TODO: consolidate Player and PlayerModel because they're literally the fucking same
        user = User.from_cache()
        self.player_id = user.id
        self.current_player = Player.create_from_user(user)
        self.player = PlayerModel(id=user.id, name=user.name)

        #client.join_game(game.game_id, self.player)
        #client.start_game(game.game_id)

        return self.player

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
        self.shop_pokemon_buttons = []
        for idx, button in enumerate(self.shopPokemon):
            self.shop_pokemon_buttons.append(PokemonButton(button, self.env, ''))
            prop = getattr(self, 'catch_pokemon_callback{}'.format(idx))
            button.clicked.connect(prop)
        self.shop_pokemon_buttons = [
            PokemonButton(qbutton, self.env, "") for qbutton in self.shopPokemon
        ]

        self.exploreWilds.clicked.connect(self.roll_shop_callback)

    def add_party_interface(self):
        # party buttons
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
        for idx, add_party in enumerate(self.addParty):
            #add_party.clicked.connect(functools.partial(self.add_to_team_callback, idx))
            add_party.clicked.connect(getattr(self, f"add_to_team_callback{idx}"))

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

    def add_stage_timer_interface(self):
        # time to next stage
        self.timeToNextStage = self.findChild(QtWidgets.QProgressBar, "timeToNextStage")

    def add_message_interface(self):
        # update log messages
        self.logMessages = self.findChild(QtWidgets.QTextBrowser, "logMessages")
        self.logMessages.moveCursor(QtGui.QTextCursor.End)

    def render_log_messages(self):
        """
        Update log messages

        TODO: this is going to change a lot in multiplayer but get something working for now
        Each player should get a unique message stream from the server.
        """
        pass
        #self.logMessages.setText(self.env.logger.content)
        #self.logMessages.moveCursor(QtGui.QTextCursor.End)

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

        phase_duration_ms = int(1E3 * state.t_phase_elapsed)
        phase_time_ms = int(1E3 * state.t_phase_remaining)
        self.timeToNextStage.setFormat(text)
        self.timeToNextStage.setMaximum(phase_duration_ms)
        self.timeToNextStage.setValue(phase_time_ms)

    def open_storage_window(self):
        self.storage_window = StorageWindow(game_env=self.env)

    def render_player_stats(self):
        player: Player = self.current_player
        self.pokeBallCount.setText(str(player.balls))
        self.energyCount.setText(str(player.energy))
        self.hitPoints.setText(str(player.hitpoints))

    def render_opponent_party(self):
        player: Player = self.current_player
        state: State = self.state
        matchmaker: Matchmaker = self.env.matchmaker
        if state.current_matches is not None:
            opponent = matchmaker.get_player_opponent_in_round(player, state.current_matches)
            if opponent is not None:
                self.opponentName.setText("{} ({})".format(opponent.name, opponent.hitpoints))
                for idx in range(6):
                    button = self.opposing_pokemon_buttons[idx]
                    pokemon = opponent.party[idx]
                    button.render_pokemon_card(pokemon)
                return

        self.opponentName.setText("No Match Scheduled")
        for idx in range(6):
            self.opposingPokemon[idx].setText("Opposing Pokemon {}".format(idx + 1))
            self.opposingPokemon[idx].setDisabled(True)

    def render_party(self):
        player = self.current_player
        party = player.party
        for idx, party_member in enumerate(party):
            party_button = self.party_pokemon_buttons[idx]
            release_button = self.addParty[idx]
            item_button = self.partyItems[idx]
            party_button.render_pokemon_card(party_member)

            if party_member is None:
                release_button.setDisabled(True)
                item_button.setDisabled(True)
            else:
                release_button.setDisabled(False)
                item_button.setDisabled(False)

    def render_team(self):
        player = self.current_player
        team = player.team
        arr = [x for x in team]
        if len(arr) < 3:
            arr.extend([None] * (3 - len(arr)))
        for idx, team_member in enumerate(arr):
            team_member_button = self.team_member_button[idx]
            remove_team_member = self.removeTeamMember[idx]
            shift_team_up = self.shiftTeamMemberUp[idx]
            shift_team_down = self.shiftTeamMemberDown[idx]
            team_member_button.render_pokemon_card(team_member)
            if team_member is None:
                remove_team_member.setDisabled(True)
                shift_team_up.setDisabled(True)
                shift_team_down.setDisabled(True)
            else:
                shift_team_up.setDisabled(False)
                shift_team_down.setDisabled(False)
                remove_team_member.setDisabled(False)

    def render_shop(self):
        state: State = self.state
        shop_window: T.Dict[Player, str] = state.shop_window

        for idx, pokemon_name in enumerate(shop_window[self.current_player]):
            shop_button = self.shop_pokemon_buttons[idx]
            shop_button.render_shop_card(pokemon_name)

        # update shop location
        if self.state.turn_number:
            route = self.state.stage.location
            self.shopLocationLabel.setText(route)

    async def _state_callback(self, topic, data):
        """
        Updates the state every time a pubsub message is received
        """
        # refresh references
        #print(data)
        self.state = State.parse_raw(data)

        # TODO: make the below a weakref or something...
        self.current_player = self.state.get_player_by_id(self.player_id)

        for method in self.render_functions:
            method()

    @asyncSlot()
    async def roll_shop_callback(self):
        print("Rolling shop")
        await self.client.roll_shop(self.context)

    async def test_catch_pokemon_callback(self, idx):
        print("Acquiring Pokemon at index {}".format(idx))
        return await self.client.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback(self, idx):
        print("Acquiring Pokemon at index {}".format(idx))
        return await self.client.catch_pokemon(self.context, idx)

    # TODO: i hate this so much but i'm not smart enough to do something better
    # i will come back to this i swear
    @asyncSlot()
    async def catch_pokemon_callback0(self):
        idx = 0
        print("Acquiring Pokemon at index {}".format(idx))
        return await self.client.catch_pokemon(self.context, idx)

    @asyncSlot()
    async def catch_pokemon_callback1(self):
        print("Acquiring Pokemon at index 1")
        return await self.client.catch_pokemon(self.context, 1)

    @asyncSlot()
    async def catch_pokemon_callback2(self):
        print("Acquiring Pokemon at index 2")
        return await self.client.catch_pokemon(self.context, 2)

    @asyncSlot()
    async def catch_pokemon_callback3(self):
        print("Acquiring Pokemon at index 3")
        return await self.client.catch_pokemon(self.context, 3)

    @asyncSlot()
    async def catch_pokemon_callback4(self):
        print("Acquiring Pokemon at index 4")
        return await self.client.catch_pokemon(self.context, 4)

    @asyncSlot()
    def add_to_team_callback(self, idx):
        return self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback0(self):
        idx = 0
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback1(self):
        idx = 1
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback2(self):
        idx = 2
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback3(self):
        idx = 3
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback4(self):
        idx = 4
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback5(self):
        idx = 5
        return await self.client.add_to_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback(self, idx):
        print("Removing team member at idx {} from team".format(idx))
        #self.env.current_player.remove_from_team(idx)

    @asyncSlot()
    async def remove_team_member_callback0(self):
        idx = 0
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback1(self):
        idx = 1
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback2(self):
        idx = 2
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback3(self):
        idx = 3
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback4(self):
        idx = 4
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback5(self):
        idx = 5
        print("Removing team member at idx {} from team".format(idx))
        return await self.client.remove_from_team(self.context, idx)

    def shift_up_callback(self, idx):
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        self.env.current_player.team[idx], self.env.current_player.team[idx - 1] =\
            self.env.current_player.team[idx - 1], self.env.current_player.team[idx]

    @asyncSlot()
    async def shift_up_callback0(self):
        idx = 0
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        return await self.client.shift_team_member_up(self.context, idx)

    @asyncSlot()
    async def shift_up_callback1(self):
        idx = 1
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        return await self.client.shift_team_member_up(self.context, idx)

    @asyncSlot()
    async def shift_up_callback2(self):
        idx = 2
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        return await self.client.shift_team_member_up(self.context, idx)

    @asyncSlot()
    async def shift_down_callback(self, idx):
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.client.shift_team_member_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback0(self):
        idx = 0
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.client.shift_team_member_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback1(self):
        idx = 1
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.client.shift_team_member_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback2(self):
        idx = 2
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.client.shift_team_member_down(self.context, idx)

    @asyncClose
    async def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
        # have the player leave the game
        if self.game_id is not None:
            await self.client.leave_game(self.game_id, self.player)
            if not len(self.client.get_players(self.game_id)):
                print('Deleting game because last player left')
                await self.client.delete_game(self.game_id, force=True)


async def main():
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = Ui(server_addr="http://76.210.142.219:8000")
    window.show()
    window.pubsub_client.start_client("ws://76.210.142.219:8000/pubsub")
    await window.pubsub_client.wait_until_done()
    app.exec_()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())    
