from engine.env import Environment
from engine.items import ItemManager
from engine.models.player import Player
from engine.pokemon import EvolutionManager, PokemonFactory
from engine.models.items import PersistentPokemonItem
from engine.models.items import PersistentPlayerItem
from engine.models.items import InstantPokemonItem
from engine.models.items import InstantPlayerItem
from engine.models.pokemon import Pokemon
from engine.player import PlayerManager
from engine.models.association import PlayerInventory
from engine.models.enums import PokemonId, PokemonType
env = Environment.create_webless_game(4)
env.initialize()
player = Player(name='balbert bang')
poke_factory: PokemonFactory = env.pokemon_factory
player_manager: PlayerManager = env.player_manager
player_manager.create_and_give_pokemon_to_player(player, 'eevee') 
player_manager.create_and_give_item_to_player(player, 'DragonScale')
item = PlayerInventory.get_inventory(player)[0] 
eevee = player_manager.player_roster(player)[0] 
player_manager.give_item_to_pokemon(eevee, item)
