import logging
import os
import sys
import typing as T
import websockets
from qasync import asyncSlot
from qasync import asyncClose
from qasync import QEventLoop
from fastapi_websocket_pubsub import PubSubClient
from fastapi_websocket_rpc.logger import logging_config, LoggingModes
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from client.client_env import ClientEnvironment
from client.screens.base import GameWindow

from engine.match import Matchmaker
from engine.player import Player
from engine.pubsub import Message
from engine.models.state import State
from client.screens.debug_battle_window import Ui as DebugWindow
from client.screens.storage_window import Ui as StorageWindow
from utils.buttons import PokemonButton
from server.api.user import User
from utils.context import GameContext
from server.api.user import User
from utils.client import AsynchronousServerClient
from utils.phase import GamePhase
from utils.error_window import error_window
from utils.websockets_client import WebSocketClient

if T.TYPE_CHECKING:
    pass

logging_config.set_mode(LoggingModes.UVICORN, level=logging.WARNING)


class Ui(QtWidgets.QMainWindow, GameWindow):

    DEBUG = os.environ.get('DEBUG')
    CREATE_AND_START_GAME = True

    def __init__(self, user, client: AsynchronousServerClient = None, game_id: str = None, websocket = None):
        super(Ui, self).__init__()
        self.user = user
        self.websocket = WebSocketClient(websocket)
        self.client = client

        # create an environment to support rendering
        self.env: ClientEnvironment = ClientEnvironment(8, id=game_id)
        # should load an initial state first?
        print('Initializing env')
        self.env.initialize()

        self.game_id = game_id

        uic.loadUi('client/qtassets/battlewindow.ui', self)

        # declare child pages
        self.storage_window = None
        self.debug_window = None

        self.pubsub_client = PubSubClient()
        self.state = None

        if self.DEBUG:
            self.debug_window = DebugWindow(self, self.env, ctx=self.context)

        # add buttons
        self.add_shop_interface()
        self.add_opposing_party_interface()
        self.add_party_interface()
        self.add_team_interface()
        self.add_message_interface()

        self.render_functions = [
            self.render_party,
            self.render_shop,
            self.render_team,
            self.render_player_stats,
            self.render_opponent_party,
            self.render_time_to_next_stage,
        ]

    @property
    def context(self) -> GameContext:
        return GameContext(self.env, self.player)

    @property
    def player(self):
        state: "State" = self.state
        print(state)
        for player in state.players:
            if player.id == self.user.id:
                return player
        return None

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
        self.messages: T.List[Message] = []
        self.logMessages = self.findChild(QtWidgets.QTextBrowser, "logMessages")
        self.logMessages.moveCursor(QtGui.QTextCursor.End)

    def render_log_messages(self):
        """
        Update log messages

        TODO: this is going to change a lot in multiplayer but get something working for now
        Each player should get a unique message stream from the server.
        """
        print(self.messages)
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

    def render_player_stats(self):
        player: Player = self.player
        self.pokeBallCount.setText(str(player.balls))
        self.energyCount.setText(str(player.energy))
        self.hitPoints.setText(str(player.hitpoints))

    def render_opponent_party(self):
        player: Player = self.player
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
        player = self.player
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
        player = self.player
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

        for idx, pokemon_name in enumerate(shop_window[self.player]):
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
        self.env.state = self.state = State.parse_raw(data)
        print(self.state)

        for method in self.render_functions:
            method()

        # if other windows are alive, update those too?
        if self.storage_window is not None:
            self.storage_window.update_state()
            self.storage_window.render_party()
            self.storage_window.render_storage()

        if self.debug_window is not None:
            self.debug_window.update_game_phase()

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
        idx = 0
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback1(self):
        idx = 1
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback2(self):
        idx = 2
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback3(self):
        idx = 3
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback4(self):
        idx = 4
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def add_to_team_callback5(self):
        idx = 5
        return await self.websocket.add_to_team(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback(self, idx):
        print("Removing team member at idx {} from team".format(idx))

    @asyncSlot()
    async def remove_team_member_callback0(self):
        idx = 0
        print("Removing team member at idx {} from team".format(idx))
        return await self.websocket.remove_team_member(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback1(self):
        idx = 1
        print("Removing team member at idx {} from team".format(idx))
        return await self.websocket.remove_team_member(self.context, idx)

    @asyncSlot()
    async def remove_team_member_callback2(self):
        idx = 2
        print("Removing team member at idx {} from team".format(idx))
        return await self.websocket.remove_team_member(self.context, idx)

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
        return await self.websocket.shift_team_up(self.context, idx)

    @asyncSlot()
    async def shift_up_callback1(self):
        idx = 1
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        return await self.websocket.shift_team_up(self.context, idx)

    @asyncSlot()
    async def shift_up_callback2(self):
        idx = 2
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        return await self.websocket.shift_team_up(self.context, idx)

    @asyncSlot()
    async def shift_down_callback(self, idx):
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.websocket.shift_team_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback0(self):
        idx = 0
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.websocket.shift_team_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback1(self):
        idx = 1
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.websocket.shift_team_down(self.context, idx)

    @asyncSlot()
    async def shift_down_callback2(self):
        idx = 2
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        return await self.websocket.shift_team_down(self.context, idx)

    def subscribe_pubsub_state(self):
        pubsub_topic = f"pubsub-state-{self.game_id}"
        self.pubsub_client.subscribe(pubsub_topic, callback=self._state_callback)

    def subscribe_pubsub_messages(self):
        msg_global = f"pubsub-msg-all-{self.game_id}"
        msg_player = f"pubsub-msg-{self.user.id}-{self.game_id}"
        self.pubsub_client.subscribe(msg_player, callback=self._message_callback)
        self.pubsub_client.subscribe(msg_global, callback=self._message_callback)

    @asyncClose
    async def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
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
#    try:
#        await loop.create_task(window.client.start_game(game_id))
#    except Exception as exc:
#        print(f"Exception in starting game: {repr(exc)}")
#        raise
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
