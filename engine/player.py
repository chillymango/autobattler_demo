"""
Player Manager Component
"""
import typing as T

from engine.base import Component
from engine.models.association import PlayerInventory, PlayerRoster, PokemonHeldItem, associate, dissociate
from engine.models.items import Item
from engine.models.party import PartyConfig
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.items import ItemManager
from engine.pokemon import PokemonFactory


class PlayerManager(Component):
    """
    Keeps track of players from turn to turn
    """

    def initialize(self):
        for player in self.state.players:
            player.is_alive = True
            player.hitpoints = 20
            player.balls = 10

    def turn_setup(self):
        """
        Add balls, run special events before prep phase
        """
        # base update
        # TODO: make this scale as the game goes on
        for player in self.state.players:
            player.balls += 6
            player.energy += 3

    def turn_cleanup(self):
        """
        Check if any player has health at 0 or less. If so, mark them as dead.
        """
        for player in self.state.players:
            if player.hitpoints <= 0:
                self.log("You have died!", recipient=player)
                player.is_alive = False

    def player_roster(self, player: Player) -> T.List[Pokemon]:
        return PlayerRoster.get_roster(player)

    def player_party(self, player: Player) -> T.List[T.Union[Pokemon, None]]:
        """
        Use the players party config and their current roster to generate a party.
        """
        return [Pokemon.get_by_id(x)() if x else None for x in player.party_config.party]

    def player_storage(self, player: Player) -> T.List[Pokemon]:
        """
        Calculate what's in the player roster but not in player party
        """
        # some cringe below...
        return list(set(self.player_roster(player)) - set(self.player_party(player)))

    def player_team(self, player: Player) -> T.List[Pokemon]:
        """
        Use the players party config to generate a team
        """
        return [Pokemon.get_by_id(x)() if x else None for x in player.party_config.team]

    def get_pokemon_holder(self, pokemon: Pokemon) -> T.Optional[Player]:
        """
        Get the player that currently holds a Pokemon
        """
        for player in self.state.players:
            if pokemon in player.roster:
                return player

    def give_pokemon_to_player(self, player: Player, pokemon: Pokemon):
        """
        Give an already existing Pokemon to a player
        """
        associate(PlayerRoster, player, pokemon)

    def create_and_give_pokemon_to_player(self, player: Player, pokemon_name: str) -> Pokemon:
        """
        Create a default Pokemon by name and give it to a player
        """
        pokemon_factory: PokemonFactory = self.env.pokemon_factory
        pokemon = pokemon_factory.create_pokemon_by_name(pokemon_name)
        associate(PlayerRoster, player, pokemon)
        # update party config to put pokemon in party if party is not full
        self.state._pokemon_registry.append(pokemon)
        player.party_config.add_to_party(pokemon.id)
        print(f'{player} - {pokemon.name}: {pokemon.id}')
        return pokemon

    def create_and_give_item_to_player(self, player: Player, item_name: str) -> Item:
        """
        Create an item by item name and give it to a player
        """
        item_manager: ItemManager = self.env.item_manager
        item = item_manager.create_item(item_name)
        associate(PlayerInventory, player, item)
        return item

    def remove_item_from_player(self, player: Player, item: Item):
        """
        Remove an item from a player
        """
        dissociate(PlayerInventory, player, item)

    def give_item_to_pokemon(self, pokemon: Pokemon, item: Item):
        """
        Move an Item from a player inventory into a Pokemon battle card.

        TODO: implement phase checks to ensure that these ops don't happen during combat
        """
        player: Player = item.holder

        if not isinstance(player, Player):
            raise Exception(f"Tried to give item to {pokemon} that wasn't ready to give")

        if pokemon not in player.roster:
            raise Exception(f"{item} does not belong to {player}")

        # TODO: make this block atomic
        dissociate(PlayerInventory, player, item)
        associate(PokemonHeldItem, pokemon, item)

    def take_item_from_pokemon(self, pokemon: Pokemon) -> Item:
        """
        Remove an item from a Pokemon and put it in its players inventory.
        """
        player: Player = pokemon.player
        item = pokemon.battle_card.berry

        # TODO: make this block atomic
        dissociate(PokemonHeldItem, pokemon, item)
        associate(PlayerInventory, player, item)
        return item

    def release_pokemon(self, player: Player, pokemon: Pokemon):
        """
        Release a Pokemon
        """
        dissociate(PlayerRoster, player, pokemon)
        self.state._pokemon_registry.remove(pokemon)
