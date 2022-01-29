"""
Player Manager Component
"""
from multiprocessing.sharedctypes import Value
import typing as T

from engine.base import Component
from engine.models.association import PlayerInventory, PlayerRoster, PlayerShop, PokemonHeldItem, associate, dissociate
from engine.models.items import InstantPlayerItem, Item, PlayerItem
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
                # TODO: remove all shop and pokemon

    def player_roster(self, player: Player) -> T.List[Pokemon]:
        return PlayerRoster.get_roster(player)

    def player_party(self, player: Player) -> T.List[T.Union[Pokemon, None]]:
        """
        Use the players party config and their current roster to generate a party.
        """
        party: T.List[T.Union[Pokemon, None]] = []
        for party_id in player.party_config.party:
            if party_id is None:
                continue
            poke = Pokemon.get_by_id(party_id)
            if poke is None:
                party.append(None)
                continue
            party.append(poke)
        return party

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
        return [Pokemon.get_by_id(x) if x else None for x in player.party_config.team]

    def use_item(self, player: Player, item: InstantPlayerItem):
        """
        Use a player item
        """
        if item not in PlayerInventory.get_inventory(player):
            raise Exception(f'{player} does not own {item}')
        item.immediate_action()

    def give_pokemon_to_player(self, player: Player, pokemon: Pokemon):
        """
        Give an already existing Pokemon to a player
        """
        associate(PlayerRoster, player, pokemon)
        if pokemon not in self.state._pokemon_registry:
            self.state._pokemon_registry.append(pokemon)
        player.party_config.add_to_party(pokemon.id)
        print(f'{player} - {pokemon.name}: {pokemon.id}')
        return pokemon

    def create_and_give_pokemon_to_player(self, player: Player, pokemon_name: str) -> Pokemon:
        """
        Create a default Pokemon by name and give it to a player
        """
        pokemon_factory: PokemonFactory = self.env.pokemon_factory
        pokemon = pokemon_factory.create_pokemon_by_name(pokemon_name)
        self.give_pokemon_to_player(player, pokemon)
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
        Remove an item from a player. This will destroy the item.
        """
        dissociate(PlayerInventory, player, item)
        item.delete()

    def give_item_to_pokemon(self, pokemon: Pokemon, item: Item):
        """
        Move an Item from a player inventory into a Pokemon battle card.

        TODO: implement phase checks to ensure that these ops don't happen during combat
        """
        player = PlayerRoster.all(entity2=pokemon)[0].entity1

        if not isinstance(player, Player):
            raise Exception(f"Tried to give item to {pokemon} that wasn't ready to give")

        # do not allow assignment if Pokemon already has item
        if PokemonHeldItem.get_held_item(pokemon) is not None:
            raise Exception(f"{pokemon} is already holding an item")

        # TODO: make this block atomic
        dissociate(PlayerInventory, player, item)
        associate(PokemonHeldItem, pokemon, item)

    def remove_item_from_pokemon(self, pokemon: Pokemon) -> Item:
        """
        Remove an item from a Pokemon and put it in its players inventory.
        """
        player = PlayerRoster.all(entity2=pokemon)[0].entity1
        if not player:
            raise Exception(f"No player found for {pokemon}")

        # TODO: make this block atomic
        item = PokemonHeldItem.get_held_item(pokemon)
        if item is not None:
            dissociate(PokemonHeldItem, pokemon, item)
            associate(PlayerInventory, player, item)
            return item
        print(f"{pokemon} does not have an item")
        return None

    def release_pokemon(self, player: Player, pokemon: Pokemon):
        """
        Release a Pokemon
        """
        dissociate(PlayerRoster, player, pokemon)
        self.state._pokemon_registry.remove(pokemon)
        player.party_config.remove_from_party(pokemon.id)
        player.party_config.remove_from_team(pokemon.id)
        pokemon.delete()

    def combine_player_items(self, player: Player, primary: Item, secondary: Item):
        """
        Attempt to combine two items
        """
        player_inventory = self.state.player_inventory[player]
        # combine inventory with all Pokemon-held items
        pokemon_inventory = [
            PokemonHeldItem.get_held_item(p) for p in self.state.player_roster[player]
        ]
        inventory = player_inventory + pokemon_inventory
        if primary not in inventory:
            raise Exception(f"{player} does not own {primary}")
        if secondary not in inventory:
            raise Exception(f"{player} does not own {secondary}")

        item_manager: ItemManager = self.env.item_manager
        combined_item = item_manager.combine_items(primary, secondary)

        # if we got a combined item successfully, delete the old items
        # and assign the new one.
        # if the items were held by player, put in player inventory
        if primary in player_inventory and secondary in player_inventory:
            # TODO: make this block atomic ... zawazawazawazawazawa
            dissociate(PlayerInventory, player, primary)
            dissociate(PlayerInventory, player, secondary)
            associate(PlayerInventory, player, combined_item)
        # if one of the items was held by a Pokemon, give the item to the Pokemon
        elif primary in player_inventory and secondary in pokemon_inventory:
            poke = PokemonHeldItem.get_item_holder(secondary)
            dissociate(PlayerInventory, player, primary)
            dissociate(PokemonHeldItem, poke, secondary)
            associate(PokemonHeldItem, poke, combined_item)
        elif primary in pokemon_inventory and secondary in player_inventory:
            poke = PokemonHeldItem.get_item_holder(primary)
            dissociate(PokemonHeldItem, poke, primary)
            dissociate(PlayerInventory, player, secondary)
            associate(PokemonHeldItem, poke, combined_item)
        else:
            raise Exception("We lost our way (items, whatever)")
