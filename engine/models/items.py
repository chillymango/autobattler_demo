"""
Items and Inventory

TODO: split this into multiple modules
"""
import aenum
from enum import Enum
import typing as T

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr
from engine.models.base import Entity
from engine.models.stats import Stats
import random

from utils.strings import camel_case_to_snake_case 
if T.TYPE_CHECKING:
    # TODO: i think it's a bad design if all of the Item objects need a reference to `env`, so
    # i am leaving a todo task to remove this circular dependency. Spaghetti codeeee
    from engine.env import Environment
    from engine.pokemon import EvolutionManager, PokemonFactory
    from engine.player import PlayerManager
    from engine.models.player import Player
    from engine.models.pokemon import BattleCard
    from engine.models.pokemon import Pokemon
    from engine.shop import ShopManager

# DEFAULT ITEM COSTS
# TODO: store somewhere else for clarity, or make configurable
SMALL_SHARD_COST = 2
LARGE_SHARD_COST = 4

L1_CONSUMABLE_COST = 1
L2_CONSUMABLE_COST = 2
L3_CONSUMABLE_COST = 3
L4_CONSUMABLE_COST = 4
L5_CONSUMABLE_COST = 5

COMMON_STONE_COST = 3
RARE_STONE_COST = 6

TM_COST = 1


class TargetType(Enum):
    """
    Intended use target
    """

    PLAYER = 1
    POKEMON = 2


class Item(Entity):
    """
    Base Class for Item
    """

    # if item is marked as consumed, the item manager should clean it up
    name: int = 0  # maps to ItemName enum
    consumed: bool = False
    holder: Entity = Field(default=None, exclude={"inventory"})
    cost: int = 1  # the "value" of a specific item
    level: int = 0  # the "power" of a specific item
    _env: "Environment" = PrivateAttr()
    tt: TargetType = None

    def __init__(self, env: "Environment" = None, **kwargs):
        """
        Hydrate each item instance with any other required keyword inputs and set env
        """
        super().__init__(**kwargs)
        self._env = env

        if self.__class__ == Item:
            # NOTE: a base Item constructor would always override the name field.
            # The base Item should not run the next segment to ensure that the name
            # field is still encoded properly in the JSON message.
            return
        self.name = ItemName[self.__class__.__name__].value


class PersistentItemMixin:
    """
    Mixin for items that trigger during phase updates

    Example item usage here includes:
    * item that updates Player state before every turn (e.g adds balls, hp, energy)
    * item that updates Player state after every battle phase (e.g gives energy if you win battle)
    """

    active: bool = False

    def turn_setup(self):
        """
        Run item logic during turn_setup
        """
        pass

    def turn_execute(self):
        """
        Run item logic during turn_execute
        """
        pass

    def turn_cleanup(self):
        """
        Run item logic during turn_cleanup
        """
        pass


class PlayerItem(Item):
    """
    Base class for items which operate on players
    """

    tt: TargetType = TargetType.PLAYER  # target type


class PokemonItem(Item):
    """
    Base class for items which get assigned to Pokemon
    """

    tt: TargetType = TargetType.POKEMON


class CombatItem(PokemonItem):
    """
    Base class for items which trigger before or after combat.

    The battle sequencer should handle this
    """
    
    slotless: bool = False #some items don't compete for slots

    def pre_battle_action(self, context: T.Dict):
        """
        Run this before any fighting happens
        """
        pass

    def pre_combat_action(self, context: T.Dict):
        """
        During battle sequencing, run this before each individual combat
        """
        pass

    def on_tick_action(self, context: T.Dict):
        """
        Run this action on all ticks
        """
        pass

    def on_fast_move_action(self, context: T.Dict):
        """
        Run this action on all fast hits
        """
        pass

    def on_enemy_fast_move_action(self, context: T.Dict):
        """
        Run this action on all enemy fast hits
        """
        pass

    def on_enemy_charged_move_action(self, context: T.Dict):
        """
        Run this action on all enemy charged hits
        """
        pass

    def on_charged_move_action(self, context: T.Dict):
        """
        Run this action on all charged moves
        """
        pass

    def post_combat_action(self, context: T.Dict):
        """
        During battle sequencing, run this after each individual combat
        """
        pass

    def post_battle_action(self, context: T.Dict):
        """
        Run this after all fighting happens
        """
        pass


class BasicHeroPowerMixIn:
    """
    Hero Powers that can be used once per turn
    """
    used: bool =  False
    success: bool = False

    def can_use(self):
        """
        ensure correct timing
        """
        if self.used == False:
            return True
        else:
            print('hero power already used this turn')
            return False

    def immediate_action(self, player: "Player" = None):
        """
        ensure once per turn
        """
        if self.can_use() == True:
            self.use(player)
            if self.success == True:
                self.used = True
    

class PassiveHeroPowerMixin:
    """
    Hero powers that accept no player input
    """
    def pre_battle_action(self, context: T.Dict):
        """
        Run this before any fighting happens
        """
        pass

    def post_battle_action(self, context: T.Dict):
        """
        Run this after all fighting happens
        """
        pass

    def turn_setup(self):
        """
        Run hp logic during turn_setup
        """
        pass

    def turn_cleanup(self):
        """
        Run hp logic during turn_cleanup
        """
        pass


class InstantItemMixin:
    """
    Item that gets used immediately
    """

    def can_use(self):
        """
        TODO: implement defaults

        Probably want to set this on game phase, e.g cannot activate pokemon upgrades
        during combat phases
        """
        return True

    def immediate_action(self):
        """
        Use item
        """
        if not self.can_use():
            return
        self.use()
        self.record_consumption()

    def record_consumption(self):
        """
        By default this just sets the consumed flag to True.

        More complex consumption criteria could count number of uses or something like that.
        """
        self.consumed = True

    def use(self):
        """
        Child classes define usage actions

        The target should be available at self.pokemon if the target is a Pokemon, or
        at self.player if the target is a Player.
        """
        raise NotImplementedError


class InstantPokemonItem(InstantItemMixin, PokemonItem):
    """
    Base class for type checking
    """


class InstantPlayerItem(InstantItemMixin, PlayerItem):
    """
    Base class for type checking
    """


class PersistentPokemonItem(PersistentItemMixin, PokemonItem):
    """
    Not totally sure what goes here yet, maybe something like
    * increase ATK by 1 every turn
    """


class PersistentPlayerItem(PersistentItemMixin, PlayerItem):
    """
    Base class for type checking
    """

class PlayerHeroPower(BasicHeroPowerMixIn, PlayerItem):
    """
    Base class for once-per-turn hero powers
    """

class PassiveHeroPower(PassiveHeroPowerMixin, PlayerItem):
    """
    Base class for passive hero powers
    """

class ComplexHeroPower(PassiveHeroPowerMixin, BasicHeroPowerMixIn, PlayerItem):
    """
    Base class for once-per-turn hero powers
    """


# EXAMPLES:
# COMBAT ITEM
class Shard(CombatItem):

    stat: Stats = None  # stat the Shard adjusts

class SmallHPShard(Shard):
    """
    Small HP Shard

    Grants a small amount of health at combat start
    """
    stat = Stats.HP
    cost = SMALL_SHARD_COST
    level = 1


class LargeHPShard(Shard):
    """
    Large HP Shard

    Grants a large amount of health at combat start
    """
    stat = Stats.HP
    cost = LARGE_SHARD_COST
    level = 2


class SmallEnergyShard(Shard):
    """
    Small Energy Shard

    Grants a small amount of energy at combat start
    """
    stat = Stats.ENG
    cost = SMALL_SHARD_COST
    level = 1


class LargeEnergyShard(Shard):
    """
    Large Energy Shard

    Grants a large amount of energy at combat start
    """
    stat = Stats.ENG
    cost = LARGE_SHARD_COST
    level = 2

class SmallDefenseShard(Shard):
    """
    Small Defense Shard

    Grants a small amount of Defense at combat start
    """
    stat = Stats.DEF
    cost = SMALL_SHARD_COST
    level = 1


class LargeDefenseShard(Shard):
    """
    Large Defense Shard

    Grants a large amount of Defense at combat start
    """
    stat = Stats.DEF
    cost = LARGE_SHARD_COST
    level = 2

class SmallAttackShard(Shard):
    """
    Small Attack Shard

    Grants a small amount of Attack at combat start
    """
    stat = Stats.ATK
    cost = SMALL_SHARD_COST
    level = 1


class LargeAttackShard(Shard):
    """
    Large Attack Shard

    Grants a large amount of Attack at combat start
    """
    stat = Stats.ATK
    cost = LARGE_SHARD_COST
    level = 2

class SmallSpeedShard(Shard):
    """
    Small Speed Shard

    Grants a small amount of Speed at combat start
    """
    stat = Stats.SPD
    cost = SMALL_SHARD_COST
    level = 1


class LargeSpeedShard(Shard):
    """
    Large Speed Shard

    Grants a large amount of Speed at combat start
    """
    stat = Stats.SPD
    cost = LARGE_SHARD_COST
    level = 2


# COMBAT ITEM
class CombinedItem(CombatItem):

    name: str = "CombinedItem"  # assign a default name here
    stat_contribution: T.List[int] = Field(default_factory=lambda:  [0,0,0,0,0]) #contribution of ATK,DEF,ENG,HP,SPD


class LifeOrb(CombinedItem):
    """
    Life Orb
    Significantly increases damage, deals damage per tick to holder
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:  [1,0,0,0,0])

    def on_battle_start(self, context: T.Dict):
        """
        even more damage 
        """
        pass

    def on_tick_action(self, context: T.Dict):
        """
        deal damage to self 
        """
        pass


class LightClay(CombinedItem):
    """
    Light Clay
    Provide extra shield
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,0,0,0])

    def pre_battle_action(self, context: T.Dict):
        """
        give shields to teammates 
        """
        pass

class CellBattery(CombinedItem):
    """
    Cell Battery
    Provide energy per tick
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,0,0])

    def on_tick_action(self, context: T.Dict):
        """
        energy per tick 
        """
        pass


class Leftovers(CombinedItem):
    """
    Leftovers
    Provide energy per tick
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,0,1,0])

    def on_tick_action(self, context: T.Dict):
        """
        HP per tick 
        """
        pass


class Metronome(CombinedItem):
    """
    Metronome
    Provide attack speed on hit
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,0,0,1])


    def on_fast_move_action(self, context: T.Dict):
        """
        atk spd per tick 
        """
        pass

class ExpShare(CombinedItem):
    """
    EXP Share
    Provide bonus XP at end of battle
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,1,0,0,1])


    def post_battle_action(self, context: T.Dict):
        """
        xp post battle 
        """
        pass


class IntimidatingIdol(CombinedItem):
    """
    Intimidating Idol
    Lowers enemy attack at battle start
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [1,1,0,0,0])


    def pre_combat_action(self, context: T.Dict):
        """
        debuff enemy attack 
        """
        pass


class IronBarb(CombinedItem):
    """
    Iron Barb
    Deals damage on hit
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,1,0,1,0])
    
    def on_enemy_fast_move_action(self, context: T.Dict):
        """
        deal damage
        """
        pass

class FocusBand(CombinedItem):
    """
    Focus Band
    Revive after battle at low health
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [1,0,1,0,0])

    def post_combat_action(self, context: T.Dict):
        """
        revive
        """
        pass

class ShellBell(CombinedItem):
    """
    Shell Bell
    Lifesteal
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:  [1,0,0,1,0])

    def on_fast_move_action(self, context: T.Dict):
        """
        heal
        """
        pass

class EjectButton(CombinedItem):
    """
    Eject Button
    Swaps out to a favorable matchup
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,1,0])

    def on_tick_action(self, context: T.Dict):
        """
        check HP, then terminate the combat
        """
        pass

    def post_combat_action(self, context: T.Dict):
        """
        exhaust the button
        """
        pass


class ExpertBelt(CombinedItem):
    """
    Expert Belt
    boosts power of super effective hits
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [1,0,0,0,1])

    def on_fast_move_action(self, context: T.Dict):
        """
        check damage type, then boost power
        """
        pass
    def on_charged_move_action(self, context: T.Dict):
        """
        check damage type, then boost power
        """
        pass

class AssaultVest(CombinedItem):
    """
    Assault Vest
    reduces power of enemy charged moves
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,0,0,1])

    def on_enemy_charged_move_action(self, context: T.Dict):
        """
        reduce power
        """
        pass

class QuickPowder(CombinedItem):
    """
    Quick Powder
    boosts attack speed of teammates
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,0,1,1])

    def pre_battle_action(self, context: T.Dict):
        """
        boost speed of team
        """
        pass


class ChoiceSpecs(CombinedItem):
    """
    Choice Specs
    Your fast move becomes lock on
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,0,1])

    def pre_battle_action(self, context: T.Dict):
        """
        change your fast move
        """
        pass


class TM(InstantPokemonItem):

    def use(self):
        card: "BattleCard" = self.pokemon.battle_card
        if card.tm_flag != True:
            self.consumed = True
            self.pokemon.battle_card.tm_flag = True

    @classmethod
    def tm_factory(cls):
        """
        tm factory
        """
        return cls(name = 'TM')

#HERO POWER ITEMS
class BrockSolid(CombatItem):

    slotless = True

    def pre_battle_action(self, context: T.Dict):
        """
        give shields to teammates 
        """
        pass

    def post_battle_action(self, context: T.Dict):
        """
        remove shields 
        """
        self.consumed = True
        pass

class JanineEject(CombatItem):

    def on_tick_action(self, context: T.Dict):
        """
        check HP, then terminate the combat
        """
        pass

    def post_combat_action(self, context: T.Dict):
        """
        exhaust the button
        """
        pass

    def post_battle_action(self, context: T.Dict):
        """
        remove button 
        """
        self.consumed = True
        pass

class DragonScale(InstantPokemonItem):

    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        if self.holder.is_type('dragon'):
            return

        self.holder.battle_card.poke_type2 = 'dragon' 

        
class RedCooking(InstantPokemonItem):

    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        if self.holder.shiny == True:
            return

        self.holder.battle_card.shiny = True


# INSTANT ITEM

class RentalDitto(InstantPokemonItem):

    _target_type: str = PrivateAttr()
    
    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        self.ditto_clone()
    
    def ditto_clone(self):
        player: "Player" = self.player
        player_manager: PlayerManager = self.env.player_manager
        player_manager.create_and_give_pokemon_to_player(player,self.holder.name)


class Stone(InstantPokemonItem):

    _target_type: str = PrivateAttr()
    cost = COMMON_STONE_COST

    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        if not self.holder.is_type(self.target_type):
            return
        self.stone_evo()

    def stone_evo(self):
        """
        Subclasses define this abstract method
        """
        raise NotImplementedError


class CommonStone(Stone):
    """
    Fire, Water, Thunder, Leaf, Moon Stones
    """

    def stone_evo(self):
        evo_manager: EvolutionManager = self.env.evolution_manager
        # handle eevee specially
        # TODO: make choice evolution types more generic
        if self.holder.name == "eevee":
            if self.target_type == "leaf":
                # invalid Eeveelution (for now!!)
                return
            evo_manager.evolve(self.holder, choice=self.target_type)
            self.consumed = True
            return

        # try and evolve
        if not evo_manager.get_evolution(self.holder.name):
            return
        evo_manager.evolve(self.holder)
        self.consumed = True


class FireStone(CommonStone):
    """
    Used to evolve fire-type Pokemon (and Eevee!)
    """

    _target_type = "fire"
    cost = COMMON_STONE_COST


class WaterStone(CommonStone):
    """
    Used to evolve fire-type Pokemon (and Eevee!)
    """
    _target_type = 'water'
    cost = COMMON_STONE_COST


# EXAMPLE: PERSISTENT PLAYER ITEM
class PokeFlute(PersistentPlayerItem):

    # can define additional fields for item flexibility
    uses_left: int = 5  # can be passed as construction argument

    def turn_setup(self):
        """
        Give a player an extra PokeFlute charge when turn starts
        """
        if not self.player:
            return
        if self.uses_left > 0:
            self.uses_left -= 1
            player: "Player" = self.player
            player.flute_charges += 1

    def turn_cleanup(self):
        """
        Mark object as consumed for item cleanup if no charges left when turn is complete
        """
        if self.uses_left <= 0:
            self.consumed = True


# EXAMPLE: INSTANT PLAYER ITEM


class MasterBall(InstantPlayerItem):

    ball_count: int = 0

    def use(self, player: "Player" = None):
        """
        Add a masterball
        """
        if player is not None:
            self.player = player
        if not self.player:
            raise Exception("Cannot use a MasterBall on a null player")

        self.player.master_balls += self.ball_count

    @classmethod
    def level1_masterball(cls, env: "Environment"):
        """
        Level 1 Masterball
        """
        return cls()


#HERO POWERS

class BlaineBlaze(PassiveHeroPower):
    
    def turn_setup(self, player: "Player" = None):
        """
        next reroll is free 
        """
        player.energy += 1


class BluePower(PassiveHeroPower):
    
    def turn_setup(self, player: "Player" = None):
        """
        if it's the correct turn get a TM
        """
        turn_divisor = 4
        if self._env.state.turn_number % turn_divisor:
            player_manager: PlayerManager = self.env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "tm")

class BrunoBod(PassiveHeroPower):
    """
    buff HP at start of game
    """

    def StartOfGame(self, player: "Player" = None):
        buffed_hp = 35
        player.hitpoints = buffed_hp


class GiovanniGains(PlayerHeroPower):
    
    oncepergame: bool = False
    _reward_dict: dict = PrivateAttr(default={
        1: [1,1,0],
        2: [2,1,1],
        3: [2,2,1],
        4: [3,2,2],
        5: [3,3,2],
        6: [4,3,3],
        7: [5,4,3],
        8: [6,4,4],
        9: [7,5,5]
    })

    def use(self, player: "Player" = None):
        """
        if you haven't used it before, get rewards according to schedule
        """
        if self.oncepergame == False:
            rewards = self._reward_dict[self._env.state.turn_number]
            player.balls += rewards[0]
            player.energy += rewards[1]
            reward_items =  ['fire_stone', 'water_stone', 'thunder_stone', 'leaf_stone', 'moon_stone']
            player_manager: PlayerManager = self.env.player_manager
            for i in range(rewards[2]):
                player_manager.create_and_give_item_to_player(player, item_name = random.choice(reward_items))
            self.oncepergame == True


class BrockShieldPower(PlayerHeroPower):
    
    hp_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a brock's solid item 
        """
        if player.balls >= self.hp_cost :
            player.balls -= self.hp_cost
            player_manager: PlayerManager = self.env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "brock_solid")
            self.success = True

class GreensRocks(PlayerHeroPower):
    
    reroll_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a mineral
        """
        if player.energy >= self.reroll_cost :
            player.energy -= self.reroll_cost
            player_manager: PlayerManager = self.env.player_manager
            minerals = ['fire_stone', 'water_stone', 'thunder_stone', 'leaf_stone', 'moon_stone']
            player_manager.create_and_give_item_to_player(player, item_name = random.choice(minerals))
            self.success = True

class JanineJutsu(PlayerHeroPower):
    
    hp_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a janine's button item 
        """
        if player.balls >= self.hp_cost :
            player.balls -= self.hp_cost
            player_manager: PlayerManager = self.env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "janine_eject")
            self.success = True

class LanceFetish(ComplexHeroPower):
    
    hp_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a dragon scale item 
        """
        if player.balls >= self.hp_cost :
            player.balls -= self.hp_cost
            player_manager: PlayerManager = self.env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "dragon_scale")
            self.success = True
        
    def pre_battle_action(self, context: T.Dict):
        """
        if dragon, buff 
        """
        pass


class WillSac(PlayerHeroPower):
    
    hp_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get hurt, get $ 
        """
        if player.hitpoints > self.hp_cost :
            player.hitpoints -= self.hp_cost
            player.flute_charges += 1
            player.balls += 2
            self.success = True

class KogaNinja(ComplexHeroPower):

    hp_cost: int = 2
    unseal_cost = 4

    def post_battle_action(self, context: T.Dict):
        """
        if win, lower unseal cost
        """
        pass
    
    def use(self, player: "Player" = None):
        if self.unseal_cost == 0:
            if player.balls > self.hp_cost :
                player.balls -= self.hp_cost
                player_manager: PlayerManager = self.env.player_manager
                eevees = ['jolteon', 'vaporeon', 'flareon']
                player_manager.create_and_give_pokemon_to_player(player, random.choice(eevees))

        
class SurgeGorilla(PassiveHeroPower):

    def pre_battle_action(self, context: T.Dict):
        """
        check largest number of matching types, apply buff
        """
        pass


class RedCheater(PassiveHeroPower):
    """
    give plot device at start of game
    """

    def StartOfGame(self, player: "Player" = None):
        player_manager: PlayerManager = self.env.player_manager 
        player_manager.create_and_give_item_to_player(player, item_name = "red_cooking")

        
## OLDER STUFF BELOW HERE ##

class _Berry:
    def __init__(self, name, ):
        self.name = name
        
    def use(self, player,pokemon ):
        if self.name in player.inventory.keys():
            if player.inventory[self.name] > 0:
                """
                Berry
                """
                if pokemon.battle_card.berry != None:
                    print('Pokemon is already holding something')
                else:
                    pokemon.battle_card.berry = self.name
                    player.remove_item(self.name)

            else:
                print('None present in inventory')
        else:
                print('None present in inventory')


class _PlayerItem:
    def __init__(self, name, ):
        self.name = name

    def use(self, player ):
        if self.name in player.inventory.keys():
            if player.inventory[self.name] > 0:
                """
                PokeFlute: next N rerolls are free
                """
                if self.name == 'PokeFlute':
                    player.flute_charges += 2
                    player.remove_item(self.name)

                """
                Master Ball: next catch is free
                """
                if self.name == 'Master Ball':
                    player.master_balls +=1
                    player.remove_item(self.name)


            else:
                print('None present in inventory')
        else:
                print('None present in inventory')


class _PokePermItem(BaseModel):

    name: str

    def use(self, pokemon, player):
        if self.name == 'TM':
            if pokemon.battle_card.tm_flag == 1:
                print('It had no effect')
            else:
                pokemon.battle_card.tm_flag = 1

                player.remove_item(self.name)


class _OldItemClass:
    # OLDER DEFINITIONS
    def use(self, player, pokemon):
        """
        check to see if the item is in the inventory, then use it if it is there
        """
        evolution_manager: "EvolutionManager" = self.state.evolution_manager
        pokemon_factory: "PokemonFactory" = self.state.pokemon_factory
        if self.name in player.inventory.keys():
            if player.inventory[self.name] > 0:
                """
                TM: unlocks 2nd move
                """
                if self.name == 'TM':
                    if pokemon.battle_card.tm_flag == 1:
                        print('It had no effect')
                    else:
                        pokemon.battle_card.tm_flag = 1
            
                        player.remove_item(self.name)
                """
                Rare Candy: +1 turn of XP
                """
                if self.name == 'Rare Candy':
                    if evolution_manager.get_threshold( pokemon.name) != None:
                        pokemon.xp += 50
                        player.remove_item(self.name)
                        evolution_manager.evolution_checker(player, pokemon)
                        pokemon_factory.shiny_checker(player, pokemon)
                    else:
                        print('It had no effect')
                """
                Rental Ditto: clones a pokemon on the roster
                """
                if self.name == 'Rental Ditto':
                    
                    clone = pokemon_factory.create_pokemon_by_name(pokemon.name)
                    if player.add_to_roster(clone) == True:
                        pokemon_factory.shiny_checker(player, pokemon)
                        player.remove_item(self.name)
                    else:
                        print('It had no effect')

                """
                Stones: +3 XP if type matches, evolves Eevee
                """
                if self.name == 'Fire Stone':
                    stone_type = 'Fire'

                    if pokemon.name == 'eevee':
                        pokemon.xp == 0
                        evolved_form = 'flareon'
                        evolved_card = pokemon_factory.get_evolved_battle_card(
                        evolved_form, pokemon.battle_card
                            )
                        if pokemon_factory.get_nickname_by_pokemon_name(pokemon.name) == pokemon.nickname:
                            pokemon.nickname = pokemon_factory.get_nickname_by_pokemon_name(evolved_form)

                        # update name and battle card
                        pokemon.name = evolved_form
                        pokemon.battle_card = evolved_card
                        pokemon_factory.shiny_checker(player, pokemon)

                    elif (pokemon.battle_card.poke_type1 == stone_type) or (pokemon.battle_card.poke_type2 == stone_type):
                        if evolution_manager.get_threshold( pokemon.name) != None:
                            pokemon.xp += 150
                            player.remove_item(self.name)
                            evolution_manager.evolution_checker(player, pokemon)
                            pokemon_factory.shiny_checker(player, pokemon)
                        else:
                            print('It had no effect')
                    else:
                        print('The stone is not compatable')

                if self.name == 'Water Stone':
                    stone_type = 'Water'

                    if pokemon.name == 'eevee':
                        pokemon.xp == 0
                        evolved_form = 'vaporeon'
                        evolved_card = pokemon_factory.get_evolved_battle_card(
                        evolved_form, pokemon.battle_card
                            )
                        if pokemon_factory.get_nickname_by_pokemon_name(pokemon.name) == pokemon.nickname:
                            pokemon.nickname = pokemon_factory.get_nickname_by_pokemon_name(evolved_form)

                        # update name and battle card
                        pokemon.name = evolved_form
                        pokemon.battle_card = evolved_card
                        pokemon_factory.shiny_checker(player, pokemon)

                    elif (pokemon.battle_card.poke_type1 == stone_type) or (pokemon.battle_card.poke_type2 == stone_type):
                        if evolution_manager.get_threshold( pokemon.name) != None:
                            pokemon.xp += 150
                            player.remove_item(self.name)
                            evolution_manager.evolution_checker(player, pokemon)
                            pokemon_factory.shiny_checker(player, pokemon)
                        else:
                            print('It had no effect')
                    else:
                        print('The stone is not compatable')


                if self.name == 'Thunder Stone':
                    stone_type = 'Electric'

                    if pokemon.name == 'eevee':
                        pokemon.xp == 0
                        evolved_form = 'jolteon'
                        evolved_card = pokemon_factory.get_evolved_battle_card(
                        evolved_form, pokemon.battle_card
                            )
                        if pokemon_factory.get_nickname_by_pokemon_name(pokemon.name) == pokemon.nickname:
                            pokemon.nickname = pokemon_factory.get_nickname_by_pokemon_name(evolved_form)

                        # update name and battle card
                        pokemon.name = evolved_form
                        pokemon.battle_card = evolved_card
                        pokemon_factory.shiny_checker(player, pokemon)

                    elif (pokemon.battle_card.poke_type1 == stone_type) or (pokemon.battle_card.poke_type2 == stone_type):
                        if evolution_manager.get_threshold( pokemon.name) != None:
                            pokemon.xp += 150
                            player.remove_item(self.name)
                            evolution_manager.evolution_checker(player, pokemon)
                            pokemon_factory.shiny_checker(player, pokemon)
                        else:
                            print('It had no effect')
                    else:
                        print('The stone is not compatable')


                if self.name == 'Leaf Stone':
                    stone_type = 'Grass'

                    if (pokemon.battle_card.poke_type1 == stone_type) or (pokemon.battle_card.poke_type2 == stone_type):
                        if evolution_manager.get_threshold( pokemon.name) != None:
                            pokemon.xp += 150
                            player.remove_item(self.name)
                            evolution_manager.evolution_checker(player, pokemon)
                            pokemon_factory.shiny_checker(player, pokemon)
                        else:
                            print('It had no effect')
                    else:
                        print('The stone is not compatable')


                if self.name == 'Moon Stone':
                    stone_type = 'Fairy'

                    if (pokemon.battle_card.poke_type1 == stone_type) or (pokemon.battle_card.poke_type2 == stone_type):
                        if evolution_manager.get_threshold( pokemon.name) != None:
                            pokemon.xp += 150
                            player.remove_item(self.name)
                            evolution_manager.evolution_checker(player, pokemon)
                            pokemon_factory.shiny_checker(player, pokemon)
                        else:
                            print('It had no effect')
                    else:
                        print('The stone is not compatable')

                """
                Choice items: nerf one move, buff attack
                """
                if self.name == 'Choice Band':
                    if pokemon.battle_card.choiced == 0:
                        pokemon.battle_card.choiced = 1
                        player.remove_item(self.name)
                    else:
                        print('It had no effect')

                if self.name == 'Choice Specs':
                    if pokemon.battle_card.choiced == 0:
                        pokemon.battle_card.choiced = 2
                        player.remove_item(self.name)
                    else:
                        print('It had no effect')

            else:
                print('None present in inventory')
        else:
                print('None present in inventory')

# type annotations
AllPokemonItems = T.Union[PersistentPokemonItem, InstantPokemonItem]
AllPlayerItems = T.Union[PersistentPlayerItem, InstantPlayerItem]

# by default just convert to snakecase and capitalize
ITEM_NAME_LOOKUP: T.Dict[T.Type[Item], str] = dict()
ITEM_REGISTRY: T.Dict[str, T.Type[Item]] = dict()
# create a dynamic enum to encode item names from server to client
class ItemName(Enum):
    pass

idx = 0
def get_item_name_for_subclasses(klass):
    """
    Recursively update ITEM_NAME_LOOKUP for all subclasses of klass
    """
    global idx
    words = camel_case_to_snake_case(klass.__name__).split('_')
    ITEM_NAME_LOOKUP[klass] = ' '.join([word.capitalize() for word in words])
    ITEM_REGISTRY[klass.__name__] = klass
    aenum.extend_enum(ItemName, klass.__name__, idx)
    idx += 1

    for subclass in klass.__subclasses__():
        get_item_name_for_subclasses(subclass)

get_item_name_for_subclasses(Item)


def get_item_class_by_name(name: str) -> T.Type[Item]:
    """
    Get an item type class by name
    """
    return ITEM_REGISTRY[name]
