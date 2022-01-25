"""
Items and Inventory

TODO: split this into multiple modules
"""
import typing as T

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr
from engine.models.base import Entity
from engine.models.stats import Stats

if T.TYPE_CHECKING:
    # TODO: i think it's a bad design if all of the Item objects need a reference to `env`, so
    # i am leaving a todo task to remove this circular dependency. Spaghetti codeeee
    from engine.env import Environment
    from engine.pokemon import EvolutionManager, PokemonFactory
    from engine.models.player import Player
    from engine.models.pokemon import BattleCard
    from engine.models.pokemon import Pokemon

# DEFAULT ITEM COSTS
# TODO: store somewhere else for clarity, or make configurable
SMALL_BERRY_COST = 2
LARGE_BERRY_COST = 4

L1_CONSUMABLE_COST = 1
L2_CONSUMABLE_COST = 2
L3_CONSUMABLE_COST = 3
L4_CONSUMABLE_COST = 4
L5_CONSUMABLE_COST = 5

COMMON_STONE_COST = 3
RARE_STONE_COST = 6

TM_COST = 1


class Item(Entity):
    """
    Base Class for Item
    """

    name: str  # not unique, all subclasses should define a default here though
    # if item is marked as consumed, the item manager should clean it up
    consumed: bool = False
    holder: Entity = Field(default=None, exclude={"inventory"})
    cost: int = 1  # the "value" of a specific item
    level: int = 0  # the "power" of a specific item
    _env: "Environment" = PrivateAttr()

    def __init__(self, env: "Environment", **kwargs):
        """
        Hydrate each item instance with any other required keyword inputs and set env
        """
        super().__init__(**kwargs)
        self._env = env


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

    holder: "Player" = Field(default=None, exclude={"inventory"})


class PokemonItem(Item):
    """
    Base class for items which get assigned to Pokemon
    """

    holder: "Pokemon" = Field(default=None, exclude={"battle_card"})


class CombatItem(PokemonItem):
    """
    Base class for items which trigger before or after combat.

    The battle sequencer should handle this
    """

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


# EXAMPLES:
# COMBAT ITEM
class Berry(CombatItem):

    stat: Stats = None  # stat the Berry adjusts
    name: str = "Berry"  # assign a default name here


class SmallSitrusBerry(Berry):
    """
    Small Sitrus Berry

    Grants a small amount of health upon exiting successful combat
    """
    name = 'Small Sitrus Berry'
    stat = Stats.HP
    cost = SMALL_BERRY_COST
    level = 1

    def post_combat_action(self, context: T.Dict):
        """
        If Pokemon still alive, gain 10% HP
        """
        pass


class LargeSitrusBerry(Berry):
    """
    Large Sitrus Berry

    Grants a large amount of health upon exiting successful combat
    """
    name = 'Large Sitrus Berry'
    stat = Stats.HP
    cost = LARGE_BERRY_COST
    level = 2


class SmallLeppaBerry(Berry):
    """
    Small Leppa Berry

    Grants a small amount of energy at combat start
    """
    name = 'Small Leppa Berry'
    stat = Stats.ENG
    cost = SMALL_BERRY_COST
    level = 1


class LargeLeppaBerry(Berry):
    """
    Large Leppa Berry

    Grants a large amount of energy at combat start
    """
    name = 'Large Leppa Berry'
    stat = Stats.ENG
    cost = LARGE_BERRY_COST
    level = 2

# TODO: implement the rest of the berry classes


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


class ChoiceItem(InstantPokemonItem):

    def use(self):
        card: "BattleCard" = self.pokemon.battle_card
        if card.choiced == 'No':
            self.consumed = True
            if self.name == 'Choice Band':
                card.choiced = 'Fast'
                card.move_f = 'YAWN'
                card.f_move_type = 'Normal'
                card.attackbuff += 2
            elif self.name == 'Choice Specs':
                card.choiced == 'Charged'
                card.move_ch = 'FRUSTRATION'
                card.ch_move_type = 'Normal'
                card.tm_flag = 1
                card.tm_move_type = 'Normal'
                card.move_tm = 'STRUGGLE'
                card.attackbuff += 2
            elif self.name == 'Choice Scarf':
                card.choiced = 'Fast-Speed'
                card.spdbuff = 0.66
                card.move_f = 'YAWN'
                card.f_move_type = 'Normal'

    @classmethod
    def choice_band_factory(cls):
        return cls(name = 'Choice Band')

    @classmethod
    def choice_specs_factory(cls):
        return cls(name = 'Choice Specs')

    @classmethod
    def choice_scarf_factory(cls):
        return cls(name = 'Choice Scarf')

# INSTANT ITEM
class Stone(InstantPokemonItem):

    target_type: str
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
    Fire, Water, Thunder, Leaf Stones
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

    name = 'Fire Stone'
    target_type = "fire"
    cost = COMMON_STONE_COST


class WaterStone(CommonStone):
    """
    Used to evolve fire-type Pokemon (and Eevee!)
    """

    name = 'Water Stone'
    target_type = 'water'
    cost = COMMON_STONE_COST


# EXAMPLE: PERSISTENT PLAYER ITEM
class PokeFlute(PersistentPlayerItem):

    name: str = "Poke Flute"
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

    name: str = "Master Ball"
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
