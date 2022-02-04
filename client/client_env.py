"""
Client loads a stripped down env to help with rendering results
"""
import typing as T

from engine.env import Environment
from engine.match import CreepRoundManager
from engine.match import Matchmaker
from engine.models.base import Entity
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.models.state import State
from engine.pokemon import EvolutionManager
from engine.pokemon import PokemonFactory
from engine.shop import ShopManager
from engine.sprites import SpriteManager
from engine.weather import WeatherManager

from utils.collections_util import extract_from_container_by_id
from utils.collections_util import pad_list_to_length


class ClientState(State):
    """
    Do not load associative containers

    ...
    and probably some other shit
    """

    def load_containers(self):
        """
        Do not load from associations

        Use the provided ID mappings to map objects
        """
        return

    # NOTE: this should all be constructed from the client state only.
    # This is because association information is not transmitted over the web.
    def roster(self, player: Player):
        return self.player_roster[player]

    def assemble_collection(
        self,
        entity_ids: T.List[T.Optional[str]],
        roster: T.List[Entity]
    ) -> T.List[Entity]:
        """
        Given a list of Pokemon IDs and a roster, grab the Pokemon objects.
        """
        collection: T.List[Entity] = []
        for _id in entity_ids:
            if _id is not None:
                entity = extract_from_container_by_id(roster, _id)
            else:
                entity = None
            collection.append(entity)

        return collection

    def party(self, player: Player) -> T.List[T.Optional[Pokemon]]:
        if player not in self.player_roster:
            raise ValueError(f"Do not have any knowledge of {player}")
        party = self.assemble_collection(
            player.party_config.party, self.player_roster[player]
        )
        pad_list_to_length(party, 6)
        return party

    def team(self, player: Player):
        if player not in self.player_roster:
            raise ValueError(f"Do not have any knowledge of {player}")

        team: T.List[Pokemon] = self.assemble_collection(
            player.party_config.team, self.player_roster[player]
        )
        pad_list_to_length(team, 3)
        return team


class ClientEnvironment(Environment):

    @property
    def default_component_classes(self):
        return [
            WeatherManager,
            PokemonFactory,
            Matchmaker,
            CreepRoundManager,
            EvolutionManager,
            ShopManager,
            SpriteManager,
        ]

    @property
    def state_factory(self):
        return ClientState.default

    def initialize(self):
        """
        Do not modify the phase
        """
        for component in self.components:
            component.initialize()
