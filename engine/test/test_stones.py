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
env = Environment.create_webless_game(4)
env.initialize()
player = Player(name='balbert bang')
poke_factory: PokemonFactory = env.pokemon_factory      
player_manager: PlayerManager = env.player_manager
player_manager: PlayerManager = env.player_manager
player_manager.create_and_give_pokemon_to_player(player, 'squirtle') 
player_manager.create_and_give_item_to_player(player, 'WaterStone')
squirtle = player_manager.player_roster(player)[0] 
water_stone = PlayerInventory.get_inventory(player)[0] 
player_manager.give_item_to_pokemon(squirtle, water_stone)
water_stone.use()
player_manager.remove_item_from_pokemon(squirtle)
player_manager.create_and_give_item_to_player(player, 'WaterStone')
water_stone = PlayerInventory.get_inventory(player)[0] 
player_manager.give_item_to_pokemon(squirtle, water_stone)
water_stone.use()

