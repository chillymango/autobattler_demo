"""
Items and Inventory

TODO: split this into multiple modules
"""
import typing as T

from pydantic import BaseModel
from engine.models.base import Entity

if T.TYPE_CHECKING:
    # TODO: i think it's a bad design if all of the Item objects need a reference to `env`, so
    # i am leaving a todo task to remove this circular dependency. Spaghetti codeeee
    from engine.env import Environment
    from engine.pokemon import EvolutionManager, PokemonFactory
    from engine.models.player import Player
    from engine.models.pokemon import BattleCard
    from engine.models.pokemon import Pokemon


class Item(Entity):
    """
    Base Class for Item
    """

    name: str  # not unique, all subclasses should define a default here though
    # if item is marked as consumed, the item manager should clean it up
    consumed: bool = False
    holder: Entity = None

    def __init__(self, env: "Environment", **kwargs):
        """
        Hydrate each item instance with any other required keyword inputs and set env
        """
        super().__init__(**kwargs)
        self.env: "Environment" = env


class PersistentItemMixin:
    """
    Mixin for items that trigger during phase updates

    Example item usage here includes:
    * item that updates Player state before every turn (e.g adds balls, hp, energy)
    * item that updates Player state after every battle phase (e.g gives energy if you win battle)
    """

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


class PokemonItem(Item):
    """
    Base class for items which get assigned to Pokemon
    """


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

    def immediate_action(self, player=None):
        """
        Use item
        """
        if player is not None:
            self.player = player
        if self.player is None:
            raise Exception(f"No action target for item {self.name} ({self.id})")

        self.use()

    def use(self):
        """
        Child classes define usage actions
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

    name: str = "Berry"  # assign a default name here
    consumed: bool = False  # instantiate to True, garbage collect
    health_factor: float = 0.0

    def post_combat_action(self):
        """
        Increment health if Pokemon fought and is still alive
        """
        super().pre_combat_action()  # check if Berry is assigned first
        card: "BattleCard" = self.pokemon.battle_card
        if card.health > 0:  # TODO: add a check here on whether the Pokemon fought
            # mark the berry as consumed
            self.consumed = True
            # execute action here
            card.health += self.health_factor * card.hp_iv  # TODO: mark max health here

    @classmethod
    def oran_berry_factory(cls):
        """
        Example oran berry factory
        """
        return cls(name='Oran Berry', health_factor=0.1)


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

    def use(self):
        if self.target_type == "Fire":
            # do fire stone actions here
            pass
        elif self.target_type == "Water":
            # do water stone actions here
            pass
        # TODO: add other stone types
        else:
            # invalid stone type
            raise Exception("Unsupported stone type {}".format())

    @classmethod
    def fire_stone_factory(cls):
        return cls(name="Fire Stone", target_type="Fire")

    @classmethod
    def water_stone_factory(cls):
        return cls(name="Water Stone", target_type="Water")


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

    ball_count: int = 1

    def use(self, player: "Player" = None):
        """
        Add a masterball
        """
        if player is not None:
            self.player = player
        if not self.player:
            raise Exception("Cannot use a MasterBall on a null player")

        self.player.master_balls += self.ball_count


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
