"""
FastAPI Client

Abstracts things like connecting to the game server and making requests
"""
import json
import requests
from uuid import uuid4

from pydantic import BaseModel

# make request imports from API modules
from api.base import ReportingResponse
from api.lobby import CreateGameRequest
from api.lobby import CreateGameResponse
from api.lobby import DeleteGameRequest
from api.lobby import JoinGameRequest
from api.lobby import LeaveGameRequest
from api.player import Player as PlayerModel


class ServerRequestFailure(Exception):
    """
    Usually suggests a handled failure
    """


class GameServerClient:
    """
    Really just for debugging for now...

    Really looking like the monorepo design is coming in soon lol
    """

    def __init__(self, bind="http://localhost:8000"):
        self.bind = bind

    def get(self, endpoint, **kwargs) -> str:
        addr = "{}/{}".format(self.bind, endpoint)
        print("Issuing get request to {}".format(addr))
        response = requests.get(addr, **kwargs)
        if response.status_code == 200:
            return response.text
        response.raise_for_status()

    def post(self, endpoint: str, data: BaseModel, response_type=BaseModel, **kwargs):
        addr = "{}/{}".format(self.bind, endpoint)
        print("Issuing post request to {}".format(addr))
        response = requests.post(addr, data.json(), **kwargs)
        if response.status_code == 200:
            return response_type.parse_raw(response.text)
        response.raise_for_status()

    def get_games(self):
        """
        Issue a request to get all current games
        """
        return json.loads(self.get("lobby/all"))

    def create_game(self, number_of_players: int = 8):
        """
        Issue a create game request
        """
        request = CreateGameRequest(number_of_players=number_of_players)
        return self.post("lobby/create", request, response_type=CreateGameResponse)

    def delete_game(self, game_id: str, force: bool = False):
        """
        Issue a delete game request
        """
        request = DeleteGameRequest(game_id=game_id, force=force)
        response = self.post("lobby/delete", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def join_game(self, game_id: str, player: PlayerModel):
        """
        Have a player join the game
        """
        request = JoinGameRequest(game_id=game_id, player=player)
        response = self.post("lobby/join", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def leave_game(self, game_id: str, player: PlayerModel):
        """
        Have a player leave a game
        """
        request = LeaveGameRequest(game_id=game_id, player=player)
        response = self.post("lobby/leave", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def get_players(self, game_id: str):
        """
        Get the list of players in a game
        """
        return json.loads(self.get("game/players", params={'game_id': game_id}))


if __name__ == "__main__":
    client = GameServerClient()
    test_player = PlayerModel(id=str(uuid4()), name='Albert Yang')
    import IPython; IPython.embed()
