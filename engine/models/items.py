"""
Items and Inventory

TODO: split this into multiple modules

TODO: more structuring on the context field that gets passed from battle engine
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
from engine.weather import WeatherManager
from engine.models.battle import Event
from engine.models.combat_hooks import CombatHook
from engine.models.enums import Move, PokemonId, PokemonType
from engine.models.shop import ShopOffer
from engine.models.player import Player
from engine.models.pokemon import BattleCard
from engine.models.pokemon import Pokemon

from utils.strings import camel_case_to_snake_case, crunch_spaces 
if T.TYPE_CHECKING:
    # TODO: i think it's a bad design if all of the Item objects need a reference to `env`, so
    # i am leaving a todo task to remove this circular dependency. Spaghetti codeeee
    from engine.batterulogico import Battler
    from engine.batterulogico import EventLogger
    from engine.batterulogico import RenderLogger
    from engine.env import Environment
    from engine.items import ItemManager
    from engine.pokemon import EvolutionManager, PokemonFactory
    from engine.player import PlayerManager
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


def per_second(stat: float):
    """
    Converts a tick-rate value to a per-second value.

    There are 10 ticks in a second.

    A helper function for visual clarity.
    """
    return stat / 10.0


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

    holder: "Player" = None
    tt: TargetType = TargetType.PLAYER  # target type

    def set_player_target(self, player: "Player"):
        self.holder = player


class PokemonItem(Item):
    """
    Base class for items which get assigned to Pokemon
    """

    holder: "Pokemon" = None
    tt: TargetType = TargetType.POKEMON

    def set_pokemon_target(self, pokemon: "Pokemon"):
        self.holder = pokemon


class CombatItem(PokemonItem):
    """
    Base class for items which trigger before or after combat.

    The battle sequencer should handle this
    """

    _slotless: bool = False #some items don't compete for slots

    _is_remote: bool = False  # some items apply effects from bench (while Poke alive)
    _is_global: bool = False  # some items always apply effects

    @property
    def is_remote(self):
        return self._is_remote

    @property
    def is_global(self):
        return self._is_global

    def get_item_holder_from_context(self, context: T.Dict) -> "Battler":
        """
        Get the Battle Card holding the item from context.
        """
        team1_items = context['team1_items']
        team2_items = context['team2_items']

        for battler, item in team1_items.items():
            if item == self:
                return battler
        for battler, item in team2_items.items():
            if item == self:
                return battler

        raise Exception(f"{self} is not being referenced by context {context}???")

    def get_team_cards_of_holder(self, context: T.Dict) -> T.List["Battler"]:
        """
        Get a list of team cards for a holder
        """
        team = self.get_team_of_holder(context)
        if team == 1:
            return context['team1']
        elif team == 2:
            return context['team2']
        raise Exception('Cannot find team???')

    def get_team_of_holder(self, context: T.Dict) -> "Battler":
        """
        Get the team that the item holder is on.

        Returns 1 if on team 1 and 2 if on team 2.
        """
        item_holder = self.get_item_holder_from_context(context)
        if item_holder in context['team1']:
            return 1
        if item_holder in context['team2']:
            return 2
        raise Exception(f"{self} is not attached to a team on this fight????")

    def get_enemy_team_from_context(self, context: T.Dict) -> int:
        if self.get_team_of_holder(context) == 1:
            return 2
        elif self.get_team_of_holder(context) == 2:
            return 1
        raise Exception("fall thru wyd")

    def get_active_enemy_from_context(self, context: T.Dict) -> "Battler":
        """
        Determine the team the item holder is on. Return the battle card representing the
        active battler on the other team.
        """
        team = self.get_team_of_holder(context)
        if team == 1:
            return context['current_team2']
        if team == 2:
            return context['current_team1']
        raise Exception("No enemies found? What's going on")

    def get_enemy_team_cards(self, context: T.Dict) -> T.List["Battler"]:
        """
        Get a list of enemy team cards
        """
        team = self.get_enemy_team_from_context(context)
        if team == 1:
            return context['team1']
        elif team == 2:
            return context['team2']
        raise Exception('Cannot find team???')

    def get_method(self, combat_hook: CombatHook) -> T.Callable:
        if combat_hook == CombatHook.PRE_BATTLE:
            return self.pre_battle_action
        if combat_hook == CombatHook.PRE_COMBAT:
            return self.pre_combat_action
        if combat_hook == CombatHook.ON_TICK:
            return self.on_tick_action
        if combat_hook == CombatHook.ON_FAST_MOVE:
            return self.on_fast_move_action
        if combat_hook == CombatHook.ON_ENEMY_FAST_MOVE:
            return self.on_enemy_fast_move_action
        if combat_hook == CombatHook.ON_CHARGED_MOVE:
            return self.on_charged_move_action
        if combat_hook == CombatHook.ON_ENEMY_CHARGED_MOVE:
            return self.on_enemy_charged_move_action
        if combat_hook == CombatHook.POST_COMBAT:
            return self.post_combat_action
        if combat_hook == CombatHook.POST_BATTLE:
            return self.post_battle_action

    def pre_battle_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this before any fighting happens
        """
        pass

    def pre_combat_action(self, **context: T.Any):
        """
        During battle sequencing, run this before each individual combat
        """
        pass

    def on_tick_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this action on all ticks
        """
        pass

    def on_fast_move_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this action on all fast hits
        """
        pass

    def on_enemy_fast_move_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this action on all enemy fast hits
        """
        pass

    def on_enemy_charged_move_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this action on all enemy charged hits
        """
        pass

    def on_charged_move_action(self, **context: T.Any) -> T.List[Event]:
        """
        Run this action on all charged moves
        """
        pass

    def post_combat_action(self, **context: T.Any) -> T.List[Event]:
        """
        During battle sequencing, run this after each individual combat
        """
        pass

    def post_battle_action(self, **context: T.Any) -> T.List[Event]:
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
    

class ChargedHeroPowerMixIn:
    """
    Hero Powers that can be used until inactive
    """
    active: bool = True

    def can_use(self):
        """
        ensure correct timing
        """
        if self.active == True:
            return True
        else:
            print('hero power inactive')
            return False

    def immediate_action(self, player: "Player" = None):
        """
        ensure once per turn
        """
        if self.can_use() == True:
            self.use(player)

class PassiveHeroPowerMixin:
    """
    Hero powers that accept no player input
    """
    def pre_battle_action(self, **context: T.Any):
        """
        Run this before any fighting happens
        """
        pass

    def post_battle_action(self, **context: T.Any):
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
        if self.use():
            self.record_consumption()

    def record_consumption(self):
        """
        By default this just sets the consumed flag to True.

        More complex consumption criteria could count number of uses or something like that.
        """
        self.consumed = True
        item_manager: "ItemManager" = self._env.item_manager
        item_manager.remove_item(self)

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

class ChargedHeroPower(ChargedHeroPowerMixIn, PlayerItem):
    """
    Base class for multi-turn hero powers
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

HeroPowerType = T.Union[ChargedHeroPower, PlayerHeroPower, PassiveHeroPower, ComplexHeroPower]


# EXAMPLES:
# COMBAT ITEM
SHARD_MULT = 2

class Shard(CombatItem):

    stat_contribution: T.List[int] = Field(default_factory=lambda:  [0,0,0,0,0]) #contribution of ATK,DEF,ENG,HP,SPD
    stat: Stats = None  # stat the Shard adjusts

    def __init__(self, _env: "Environment" = None, **kwargs):
        super().__init__(_env=_env, **kwargs)
        self.stat_contribution[self.stat.value] = self.level * SHARD_MULT


class SmallHitPointShard(Shard):
    """
    Small HP Shard

    Grants a small amount of health at combat start
    """
    stat = Stats.HP
    cost = SMALL_SHARD_COST
    level = 1


class LargeHitPointShard(Shard):
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
    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,0,0,0,0]) #contribution of ATK,DEF,HP,ENG,SPD


class LifeOrb(CombinedItem):
    """
    Life Orb
    Significantly increases damage, deals damage per tick to holder
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [1,0,0,0,0])

    _HEALTH_LOSS = 2.0  # 2 HP per second
    _DAMAGE_BUFF = 0.10  # 10% damage increase per level

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        more damage
        """
        holder = self.get_item_holder_from_context(context).battlecard
        battler = self.get_item_holder_from_context(context)
        team = self.get_team_of_holder(context)
        before = holder.attack
        holder.modifiers[Stats.ATK.value] += self._DAMAGE_BUFF * self.level * before
        after = holder.attack
        if logger is not None:
            logger(
                "LifeOrb pre_battle",
                f"{holder.name.name} ATK {before:.1f} -> {after:.1f}"
            )
        if render is not None:
            render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|atk|"+ str(round(after/holder.atk_, 2))   +"|[from] item: Life Orb")

    def on_tick_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        lose health per tick
        """
        holder = self.get_item_holder_from_context(context)
        team = self.get_team_of_holder(context)

        before = holder.hp
        after = holder.hp - per_second(self._HEALTH_LOSS) * self.level
        holder.hp = after
        if logger is not None:
            logger(
                "LifeOrb on_tick",
                f"{holder.battlecard.name.name} HP: {before:.1f} -> {after:.1f}"
            )
        if render is not None:
            render("|-damage|p" + str(team)+ "b: " +holder.nickname+ "|"+str(int(after))+r"\/"+str(int(holder.battlecard.max_health))+"|[from] item: Life Orb | [of] p" + str(team)+ "b: " +holder.nickname)


class LightClay(CombinedItem):
    """
    Light Clay
    Provide extra shield
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,0,0,0])

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        give shields to teammates 
        """
        holder = self.get_item_holder_from_context(context).battlecard
        team = self.get_team_of_holder(context)

        team_cards = self.get_team_cards_of_holder(context)
        shields_to_give = self.level
        while shields_to_give > 0:
            for card in team_cards:
                card.battlecard.bonus_shield += 1
                shields_to_give -= 1
                if logger is not None:
                    logger(
                        "LightClay pre_battle",
                        f"{holder.name.name} gives shield to {card.battlecard.name.name}"
                    )
                if render:
                    "|-start|p" + str(team)+"a: "+ card.nickname + "|Shielded|[from] item: Light Clay| [of] p" + str(team) + "a: " + holder.nickname



class CellBattery(CombinedItem):
    """
    Cell Battery
    Provide energy per tick
    """

    _ENERGY = 1.0

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,0,0,1,0])

    def on_tick_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        energy per tick 
        """
        holder = self.get_item_holder_from_context(context).battlecard
        team = self.get_team_of_holder(context)
        before = holder.energy
        after = holder.energy + per_second(self._ENERGY) * self.level
        holder.energy = after
        if logger:
            logger(
                'CellBattery on_tick',
                f"team{team} {holder.name.name} energy: {before:.2f} -> {after:.2f}"
            )


class Leftovers(CombinedItem):
    """
    Leftovers
    Provide energy per tick
    """

    _HEALTH_PER_TICK = 3.0

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,0,0])

    def on_tick_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        health per tick 
        """
        holder = self.get_item_holder_from_context(context)
        team = f"team{self.get_team_of_holder(context)}"
        before = holder.hp
        after = holder.hp + per_second(self._HEALTH_PER_TICK)
        holder.hp = after
        if logger:
            logger(
                "LeftOvers on_tick",
                f"team{team} {holder.battlecard.name.name} HP {before:.1f} -> {after:.1f}"
            )
        render("|-heal|p"+str(team[-1])+"a: "+holder.nickname+"|" + str(round(after)) + r"\/" + str(round(holder.battlecard.max_health))+"|[from] item: Leftovers")


class Metronome(CombinedItem):
    """
    Metronome
    Provide attack speed on hit
    """

    _SPEED_BONUS = 0.5
    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,0,0,0,1])

    def on_fast_move_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        atk spd per tick 
        """
        holder = self.get_item_holder_from_context(context).battlecard
        battler = self.get_item_holder_from_context(context)
        attacker: BattleCard = context['attacker'].battlecard
        if holder != attacker:
            return
        team = self.get_team_of_holder(context)
        before = holder.modifiers[Stats.SPD.value]
        before = holder.speed
        holder.modifiers[Stats.SPD.value] += self._SPEED_BONUS * self.level
        after = holder.speed
        if logger:
            logger(
                "Metronome on_fast_move",
                f"team{team} {holder.name.name} SPD {before:.1f} -> {after:.1f}"
            )
        if render:
            render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|spd|"+ str(round(after, 2))   +"|[from] item: Metronome")


class FrozenHeart(CombinedItem):
    """
    Frozen Heart

    Reduces attack speed of all enemies
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,0,0,1])
    _SPD_REDUCTION = 2.0

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        Reduce SPD of all opponents
        """
        holder = self.get_item_holder_from_context(context).battlecard
        holder_poke = self.get_item_holder_from_context(context)

        enemy_team = self.get_enemy_team_cards(context)
        for battler in enemy_team:
            card = battler.battlecard
            team = self.get_team_of_holder(context)

            before = card.speed
            card.modifiers[Stats.SPD.value] += self.level * self._SPD_REDUCTION
            after = card.speed
            if logger is not None:
                logger(
                    "FrozenHeart pre_battle",
                    f"{holder.name.name} reduced {card.name.name} SPD {before:.1f} -> {after:.1f}"
                )
            if render:
                render("|-unboost|p" + str(team)+"a: "+ battler.nickname + "|spd|" +  str(round(after, 2)/100) +"|[from] item: Frozen Heart| [of] p" + str(team) + "a: " + holder_poke.nickname)



class IntimidatingIdol(CombinedItem):
    """
    Intimidating Idol
    Lowers enemy attack at battle start
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [1,1,0,0,0])
    ATK_DEBUFF = 3.0

    def pre_combat_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any) -> T.List[Event]:
        """
        debuff enemy attack 
        """
        enemy = self.get_active_enemy_from_context(context).battlecard
        enemy_team = self.get_enemy_team_from_context(context)
        before = enemy.attack
        enemy.modifiers[Stats.ATK.value] -= self.level * self.ATK_DEBUFF
        after = enemy.attack
        if logger:
            logger(
                "IntimidatingIdol pre_combat",
                f"team{enemy_team} ATK {before:.0f} -> {after:.0f}"
            )


class IronBarb(CombinedItem):
    """
    Iron Barb
    Deals damage on hit
    """

    _DAMAGE = 2.0
    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,1,0,0])

    def on_enemy_fast_move_action(self, logger: "EventLogger" = None, render: "RenderLogger" = None, **context: T.Any):
        """
        deal damage
        """
        holder = self.get_item_holder_from_context(context)
        attacker = context['attacker']

        if holder == attacker:
            return
        enemy = self.get_active_enemy_from_context(context)
        enemy_team = self.get_enemy_team_from_context(context)
        before = enemy.hp
        after = enemy.hp - self._DAMAGE * self.level
        enemy.hp = after
        if logger:
            logger(
                "IronBarb on_enemy_fast_move",
                f"team{enemy_team} HP {before} -> {after}"
            )
        if render:
            render(
                "|-damage|p" + enemy_team + "a:" + enemy.nickname + "|" + str(int(after)) + r"\/" + str(int(enemy.battlecard.max_health)) + "|[from] item: Iron Barb|[of] p" + str(3-int(enemy_team)) +"a: " + holder.nickname
            )


class FocusBand(CombinedItem):
    """
    Focus Band
    Revive after battle at low health
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [1,0,1,0,0])

    def post_combat_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        revive
        """
        if self.consumed:
            return
        self.consumed = True
        battler = self.get_item_holder_from_context(context)
        holder = battler.battlecard
        team = self.get_team_of_holder(context)
        # do not trigger if holder did not faint
        if holder.status == 1:
            return

        holder.status = 1
        holder.energy = 100
        if self.level == 1:
            battler.hp = 1
        elif self.level == 2:
            battler.hp = holder.max_health * 0.15
        elif self.level == 3:
            battler.hp = holder.max_health * 0.25
        else:
            raise Exception(f"what kind of bonkers level is {self.level}")
        if logger is not None:
            logger(
                "FocusBand post_combat",
                f"team{team} {holder.name.name} revived with {battler.hp} HP and {holder.energy} ENG"
            )
        if render:
            render("|-enditem|p" + str(team) + "a: " + battler.nickname + "|Focus Sash")
            render("|-damage|p" + str(team) + "a:" + battler.nickname + "|" + str(int(battler.hp)) + r"\/" + str(int(holder.max_health)) )


class ShellBell(CombinedItem):
    """
    Shell Bell
    Lifesteal
    """

    _LIFESTEAL_PCT: float = 5.0  # percent of move damage

    stat_contribution: T.List[int] = Field(default_factory=lambda:  [1,0,1,0,0])

    def _on_damage_move_action(
        self,
        name: str,
        logger: "EventLogger" = None,
        render: "RenderLogger" = None,
        **context: T.Any
    ):
        """
        Heal after dealing move damage

        NOTE(albert/will): this does pre-mitigation damage, which may be imbalanced...
        """
        battler = self.get_item_holder_from_context(context)
        holder = self.get_item_holder_from_context(context).battlecard
        team = self.get_team_of_holder(context)
        move: str = context['move']
        if move == holder.move_f.name:
            damage = holder._move_f_damage
        elif move == holder.move_ch.name:
            damage = holder._move_ch_damage
        elif move == holder.move_tm.name:
            damage = holder._move_tm_damage
        else:
            raise Exception(f"Received unknown move {move.name}")

        before = holder.health
        after = holder.health + self._LIFESTEAL_PCT / 100.0 * self.level * damage
        holder.health = after
        if logger is not None:
            logger(
                f"ShellBell {name}",
                f"team{team} {holder.name.name} HP {before:.1f} -> {after:.1f}"
            )
        render("|-heal|p" + str(team) + "a: " + battler.nickname + "|" + str(int(after)) + r"\/" + str(int(holder.max_health)) + "|[from] item: Shell Bell")

    def on_fast_move_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        self._on_damage_move_action("on_fast_move", logger=logger, render = render,**context)

    def on_charged_move_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        self._on_damage_move_action("on_charged_move", logger=logger, render = render,**context)


class EjectButton(CombinedItem):
    """
    Eject Button
    Swaps out to a favorable matchup
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,1,0])

    def on_tick_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        check HP, then terminate the combat
        """
        if self.consumed:
            return
        hp_factor = self.level * 0.25
        battler = self.get_item_holder_from_context(context)
        holder = battler.battlecard
        if battler.hp > hp_factor * holder.max_health:
            # do not trigger until health falls below certain amount
            return
        self.consumed = True
        # TODO: initiate swap...


class ExpertBelt(CombinedItem):
    """
    Expert Belt
    boosts power of super effective hits
    """

    _MULTIPLIER = 0.1  # 10% extra damage per level
    stat_contribution: T.List[int] = Field(default_factory=lambda: [1,0,0,0,1])

    def _on_damage(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        attacker: Battler = context['attacker']
        holder = self.get_item_holder_from_context(context)
        if attacker.battlecard != holder.battlecard:
            return
        before = holder.battlecard.multiplier
        after = self._MULTIPLIER * self.level
        holder.battlecard.multiplier = after
        if logger is not None:
            logger(
                "ExpertBelt on_attack",
                f"{holder.nickname} Super Effective Additive Multiplier {before:.1f} -> {after:.1f}"
            )
        if render:
            render("|-message|Expert Belt boosts the move's power!")


    def on_fast_move_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        check damage type, then boost power
        """
        self._on_damage(logger=logger, render = render,**context)

    def on_charged_move_action(self, logger: "EventLogger", render: "RenderLogger" = None, **context: T.Any):
        """
        check damage type, then boost power
        """
        self._on_damage(logger=logger,  render = render ,**context)

    def post_combat_action(self, **context: T.Any):
        """
        Reset multipliers by undoing the addition
        """
        holder = self.get_item_holder_from_context(context)
        holder.battlecard.multiplier -= self._MULTIPLIER * self.level


class AssaultVest(CombinedItem):
    """
    Assault Vest
    reduces power of enemy charged moves
    """

    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,1,0,0,1])
    _POWER_REDUCTION: int = 2

    def on_enemy_charged_move_action(
        self,
        logger: "EventLogger" = None,
        render: "RenderLogger" = None,
        **context: T.Any
    ):
        """
        reduce power
        """
        attacker: BattleCard = context['attacker'].battlecard
        holder = self.get_item_holder_from_context(context).battlecard
        if attacker == holder:
            return

        enemy = self.get_active_enemy_from_context(context).battlecard
        enemy_team = self.get_enemy_team_from_context(context)
        before = enemy.attack
        enemy.modifiers[Stats.ATK.value] -= self._POWER_REDUCTION * self.level
        after = enemy.attack
        if logger is not None:
            logger(
                "AssaultVest on_enemy_charged_move",
                f"team{enemy_team} {enemy.name.name} ATK {before:.1f} -> {after:.1f}"
            )
        if render is not None:
            render("|-message|Assault Vest lowers the move's power!")


class QuickPowder(CombinedItem):
    """
    Quick Powder
    boosts attack speed of teammates
    """

    _SPEED_STAT = 1.0
    stat_contribution: T.List[int] = Field(default_factory=lambda: [0,0,1,0,1])

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        boost speed of team
        """
        team_battlers = self.get_team_cards_of_holder(context)
        team = self.get_team_of_holder(context)

        for battler in team_battlers:
            card = battler.battlecard
            before = card.speed
            card.modifiers[Stats.SPD.value] += self.level * self._SPEED_STAT
            after = card.speed
            if logger is not None:
                logger(
                    'QuickPowder pre_battle',
                    f"{card.name.name} SPD {before:.1f} -> {after:.1f}"
                )
            if render:
                render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|spd|"+ str(round(after, 2) /100 ) +"|[from] item: Quick Powder")



class ChoiceSpecs(CombinedItem):
    """
    Choice Specs
    Your fast move becomes lock on, you get energy on hit
    """
    _ENG_GAIN = 1.0
    stat_contribution: T.List[int] = Field(default_factory=lambda:   [0,0,1,0,1])

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        change your fast move
        """
        lock_on = Move.LOCK_ON
        holder = self.get_item_holder_from_context(context).battlecard
        team = self.get_team_of_holder(context)
        holder.move_f = lock_on
        if logger is not None:
            logger(
                "ChoiceSpecs pre_battle",
                f"team{team} move became {lock_on.name}"
            )

    def on_fast_move_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        energy onhit
        """
        holder = self.get_item_holder_from_context(context).battlecard
        team = self.get_team_of_holder(context)
        before = holder.energy
        after = holder.energy + self._ENG_GAIN * self.level
        holder.energy = after
        if logger is not None:
            logger(
                "ChoiceSpecs on_fast_move",
                f"team{team} {holder.name.name} ENG {before:.1f} -> {after:.1f}"
            )


class TechnicalMachine(InstantPokemonItem):

    def use(self):
        print('Using TM')
        card: "BattleCard" = self.holder.battle_card
        if card.tm_flag:
            raise Exception("Target already has TM move")
        self.holder.battle_card.tm_flag = True
        return True


#HERO POWER ITEMS
class BrockSolid(CombatItem):

    slotless = True

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        give shields to teammates 
        """
        holder = self.get_item_holder_from_context(context).battlecard
        team_cards = self.get_team_cards_of_holder(context)
        shields_to_give = 2
        team = self.get_team_of_holder(context)

        while shields_to_give > 0:
            for card in team_cards:
                card.battlecard.bonus_shield += 1
                shields_to_give -= 1
                if logger is not None:
                    logger(
                        "Brock Solid pre_battle",
                        f"{holder.name.name} gives shield to {card.battlecard.name.name}"
                    )
                if render:
                    "|-start|p" + str(team)+"a: "+ card.nickname + "|Shielded|[from] item: Brock Solid| [of] p" + str(team) + "a: " + holder.nickname

    def post_battle_action(self, **context: T.Any):
        """
        """
        self.consumed = True
        pass

class JanineEject(CombatItem):

    def on_tick_action(self, **context: T.Any):
        """
        check HP, then terminate the combat
        """
        pass

    def post_combat_action(self, **context: T.Any):
        """
        exhaust the button
        """
        pass

    def post_battle_action(self, **context: T.Any):
        """
        remove button 
        """
        self.consumed = True
        pass


class DragonScale(InstantPokemonItem):

    def use(self) -> bool:
        if not isinstance(self.holder, Pokemon):
            return False

        if self.holder.is_type(PokemonType.dragon):
            return False

        self.holder.battle_card.poke_type2 = PokemonType.dragon

        return True


class RedCooking(InstantPokemonItem):

    def use(self):
        if not isinstance(self.holder, Pokemon):
            return False

        if self.holder.battle_card.shiny == True:
            return False

        self.holder.battle_card.shiny = True
        return True


# INSTANT ITEM

class RentalDitto(InstantPokemonItem):

    _target_type: str = PrivateAttr()
    
    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        self.ditto_clone()
        return True
    
    def ditto_clone(self):
        player: "Player" = self.player
        player_manager: PlayerManager = self._env.player_manager
        player_manager.create_and_give_pokemon_to_player(player,self.holder.name)


class RareCandy(InstantPokemonItem):
    def use(self):
        evo_manager: EvolutionManager = self._env.evolution_manager
        # handle eevee specially
        # TODO: make choice evolution types more generic
        im: "ItemManager" = self._env.item_manager
        holder = im.get_pokemon_item_holder(self)
        if holder is None:
            raise Exception("No Pokemon found as a valid target")

        if not evo_manager.get_evolution(holder.name):
            return False
        holder.add_xp(50)
        threshold = self.get_threshold(holder.name.name)
        if holder.xp >= threshold:
            print(
                'Party member {} XP exceeds threshold ({} >= {})'
                .format(holder.name.name, holder.xp, threshold)
            )
            self.evolve(holder)
            shop_manager: "ShopManager" = self.env.shop_manager
            shop_manager.check_shiny(self.player, holder.name.name)

        return True


class Stone(InstantPokemonItem):

    _target_type: str = PrivateAttr()
    cost = COMMON_STONE_COST

    def use(self):
        print("using stone")
        return self.stone_evo()

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

        print('running stone evo')
        evo_manager: EvolutionManager = self._env.evolution_manager

        # handle eevee specially
        # TODO: make choice evolution types more generic
        im: "ItemManager" = self._env.item_manager
        if self.holder is None:
            print('Holder is none')
            raise Exception("No Pokemon found as a valid target")
        player = evo_manager.find_owner(self.holder)

        if self.holder.name == PokemonId.eevee:
            if PokemonType.water in self._target_type:
                return self.eve_volve(evo = "vaporeon", pokemon = self.holder, evo_name = PokemonId.vaporeon, player = player)
            if PokemonType.fire in self._target_type:
                return self.eve_volve(evo = "flareon", pokemon = self.holder, evo_name = PokemonId.flareon, player = player)
            if PokemonType.electric in self._target_type:
                return self.eve_volve(evo = "jolteon", pokemon = self.holder, evo_name = PokemonId.jolteon, player = player)
            return False

        print('holder is not eevee')
        # try and evolve
        if not evo_manager.get_evolution(self.holder.name.name):
            return False
        if (self.holder.is_type(PokemonType.dragon)) or (self.holder.name == PokemonId.magikarp):
            print('not compatable with stones')
            return False
        if ((self.holder.battle_card.poke_type1 in self._target_type) or (self.holder.battle_card.poke_type2 in self._target_type)):
            print('holder qualifies for stone')
            self.holder.add_xp(150)
            threshold = evo_manager.get_threshold(self.holder.name.name)
            if self.holder.xp >= threshold:
                print(
                    'Party member {} XP exceeds threshold ({} >= {})'
                    .format(self.holder.name.name, self.holder.xp, threshold)
                )
                evo_manager.evolve(self.holder)
                shop_manager: "ShopManager" = self._env.shop_manager
                shop_manager.check_shiny(player, self.holder.name.name)
            return True
        return False

    def eve_volve(self, evo, pokemon, evo_name, player):
        print("evolving eevee with stone")
        pokemon_factory: PokemonFactory = self._env.pokemon_factory
        pokemon.xp = 0
        evolved_form = evo
        evolved_card = pokemon_factory.get_evolved_battle_card(
        evolved_form, pokemon.battle_card
            )
        print(evolved_card)
        if pokemon_factory.get_nickname_by_pokemon_name(pokemon.name.name) == pokemon.nickname:
            pokemon.nickname = pokemon_factory.get_nickname_by_pokemon_name(evolved_form)

        # update name and battle card
        pokemon.name = evo_name
        pokemon.battle_card = evolved_card
        shop_manager: "ShopManager" = self._env.shop_manager
        shop_manager.check_shiny(player, pokemon.name.name)
        return True


class FireStone(CommonStone):
    """
    Used to evolve fire-type Pokemon (and Eevee!)
    """
    _target_type = [PokemonType.fire]
    cost = COMMON_STONE_COST


class WaterStone(CommonStone):
    """
    Used to evolve fire-type Pokemon (and Eevee!)
    """
    _target_type = [PokemonType.water, PokemonType.ice]
    cost = COMMON_STONE_COST


class ThunderStone(CommonStone):
    """
    Used to evolve steel and electric-type Pokemon (and Eevee!)
    """
    _target_type = [PokemonType.electric, PokemonType.psychic]
    cost = COMMON_STONE_COST

class LeafStone(CommonStone):
    """
    Used to evolve grass and bug-type Pokemon
    """
    _target_type = [PokemonType.grass, PokemonType.bug]
    cost = COMMON_STONE_COST

class DuskStone(CommonStone):
    """
    Used to evolve dark and poison-type Pokemon
    """
    _target_type = [PokemonType.dark, PokemonType.poison]
    cost = COMMON_STONE_COST

class HardStone(CommonStone):
    """
    Used to evolve rock and ground-type Pokemon
    """
    _target_type = [PokemonType.rock, PokemonType.ground, PokemonType.steel]
    cost = COMMON_STONE_COST

class MoonStone(CommonStone):
    """
    Used to evolve fairy and normal-type Pokemon
    """
    _target_type = [PokemonType.fairy, PokemonType.normal]
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

class SabrinaFuture(PassiveHeroPower):

    def turn_setup(self, player: "Player" = None):
        weather_manager: WeatherManager = self._env.weather_manager
        forecast_today = weather_manager.weather_forecast[self._env.state.turn_number]
        forecast_tmrw = weather_manager.weather_forecast[self._env.state.turn_number+1]
        forecast_dat = weather_manager.weather_forecast[self._env.state.turn_number+2]

        """
        display these somehow
        """

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        
        team_battlers = self.get_team_cards_of_holder(context)
        weather = self._env.state.weather 
        weather_manager: WeatherManager = self._env.weather_manager
        bonus_types = weather_manager.weather_bonuses[weather]

        for battler in team_battlers:
            card = battler.battlecard
            if ((card.poke_type1 in bonus_types) | (card.poke_type2 in bonus_types) ):
                card._move_ch_energy = (0.66*card._move_ch_energy )
                card._move_tm_energy = (0.66*card._move_tm_energy )

                if logger is not None:
                    logger(
                        'Sabrina pre_battle'
                    )
                if render:
                    render("|-message|Sabrina's Hero Power activates!")


class BlaineButton(ChargedHeroPower):
    
    counter: int = 0
    bust: bool = False
    jackpot: bool = True
    _PRIZE: int = 5
    _max_dict: dict = PrivateAttr(default={
        0: 9,
        1: 9,
        2: 9,
        3: 9,
        4: 11,
        5: 11,
        6: 11,
        7: 12,
        8: 12,
        9: 13,
        10:13,
        11:13,
        12:14,
        13:14,
        14:15,
        15:15,
        16:15,
        17:16,
        18:16,
        19:17,
        20:17,
        21:17,
    })

    def turn_setup(self, player: "Player" = None):
        """
        next reroll is free 
        """
        self.counter = 0
        self.bust = False
        self.jackpot = False

    def use(self, player: "Player" = None):
        if self.bust == False:
            max = self._max_dict[self._env.state.turn_number]
            roll = random.randint(1,6)
            self.counter += roll
            if self.counter > max:
                self.bust = True
                self.counter = -5
                print('U busted')
            elif self.counter == max: 
                self.jackpot = True
                player.balls += self._PRIZE
                print('u hit the jackpot poggers')
        else:
            print('no more rolls')

        return



    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        boost stats of team
        """
        team_battlers = self.get_team_cards_of_holder(context)
        if render:
            render("|-message|Blaine's Hero Power Activates!") 

        for battler in team_battlers:
            card = battler.battlecard
            before = card.attack
            team = self.get_team_of_holder(context)

            card.modifiers[Stats.ATK.value] +=  self.counter*0.2
            after = card.attack
            if logger is not None:
                logger(
                    'BlaineBlaze pre_battle',
                    f"{card.name.name} ATK {before:.1f} -> {after:.1f}"
                )
            if render:
                render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|atk|"+ round(after/card.atk_, 2) ) 

        for battler in team_battlers:
            card = battler.battlecard
            before = card.defense
            card.modifiers[Stats.DEF.value] += self.counter*0.2
            after = card.defense
            if logger is not None:
                logger(
                    'BlaineBlaze pre_battle',
                    f"{card.name.name} DEF {before:.1f} -> {after:.1f}"
                )
            if render:
                render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|def|"+ round(after/card.def_, 2) ) 

class BlueSmell(PassiveHeroPower):

    reroll_cost = 3.0

    def use(self, player: "Player" = None):
        # TODO: fix deferred import
        from engine.models.association import associate
        from engine.models.association import dissociate
        from engine.models.association import PlayerShop
        if player.energy >= self.reroll_cost:
            player.energy -= self.reroll_cost
            shop_manager: ShopManager = self._env.shop_manager
            bonus_shop = shop_manager.get_shop_by_turn_number(self, self._env.state.turn_number)
            for card in self.state.shop_window[player]:
                if card is not None:
                    dissociate(PlayerShop, player, card)
            for rolled in bonus_shop.roll_shop():
                associate(PlayerShop, player, ShopOffer(pokemon=PokemonId[rolled]))

class MistyTrustFund(PassiveHeroPower):
    
    def turn_setup(self, player: "Player" = None):
        """
        if it's the correct turn get cash
        """
        turn_divisor = 4
        income = 4
        if self._env.state.turn_number % turn_divisor:
            player.balls += income


class ErikaGarden(PassiveHeroPower):
    
    def turn_setup(self, player: "Player" = None):
        """
        if it's the correct turn grow your pokes
        """
        turn_divisor = 4
        if self._env.state.turn_number % turn_divisor:
            player_manager: PlayerManager = self._env.player_manager
            for party_member in player_manager.player_party(player):
                if party_member is None or party_member.name not in self.evolution_config:
                    continue
                party_member.add_xp(self.XP_PER_TURN)
                threshold = self.get_threshold(party_member.name)
                if party_member.xp >= threshold:
                    print(
                        'Party member {} XP exceeds threshold ({} >= {})'
                        .format(party_member.name, party_member.xp, threshold)
                    )
                    self.evolve(party_member)
                    shop_manager: "ShopManager" = self._env.shop_manager
                    shop_manager.shiny_checker(player, party_member.name)


class BrunoBod(PassiveHeroPower):
    """
    buff HP at start of game
    """

    def StartOfGame(self, player: "Player" = None):
        buffed_hp = 35
        player.hitpoints = buffed_hp


class BlastOff(PlayerHeroPower):
    current_cost: int = 5
    immune: bool = False

    def turn_setup(self, player: "Player" = None):
        self.immune = False

    def use(self, player: "Player" = None):
        if player.balls >= self.current_cost :
            player.balls -= self.current_cost
            self.current_cost += 2
            self.immune = True
    def post_battle_action(self, **context: T.Any):
        """
        if lose and immune, don't take damage.
        """
        pass



class GiovanniGains(PlayerHeroPower):
    
    oncepergame: bool = False
    _reward_dict: dict = PrivateAttr(default={
        1: [1,1,0],
        2: [1,1,0],
        3: [1,1,0],
        4: [2,1,1],
        5: [2,1,1],
        6: [3,2,1],
        7: [3,2,1],
        8: [3,2,2],
        9: [4,2,2],
        10: [4,3,2],
        11: [4,3,2],
        12: [5,3,3],
        13: [5,3,3],
        14: [5,4,3],
        15: [6,4,3],
        16: [7,4,4],
        17: [8,4,4],
        18: [9,5,5],
        19: [10,5,5],
        20: [11,5,5],
        21: [12,5,5]
    })

    def use(self, player: "Player" = None):
        """
        if you haven't used it before, get rewards according to schedule
        """
        if self.oncepergame == False:
            rewards = self._reward_dict[self._env.state.turn_number]
            player.balls += rewards[0]
            player.energy += rewards[1]
            reward_items =  ["SmallEnergyShard","SmallAttackShard","SmallSpeedShard","SmallHitPointShard","TechnicalMachine","SmallDefenseShard"]
            player_manager: PlayerManager = self._env.player_manager
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
            player_manager: PlayerManager = self._env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "BrockSolid")
            self.success = True

class GreensRocks(PlayerHeroPower):
    
    reroll_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a mineral
        """
        if player.energy >= self.reroll_cost :
            player.energy -= self.reroll_cost
            player_manager: PlayerManager = self._env.player_manager
            minerals = ['FireStone', 'WaterStone', 'ThunderStone', 'LeafStone', 'MoonStone', 'HardStone', 'DuskStone']
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
            player_manager: PlayerManager = self._env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "JanineEject")
            self.success = True

class LanceFetish(ComplexHeroPower):
    
    hp_cost: int = 2

    def use(self, player: "Player" = None):
        """
        get a dragon scale item 
        """
        if player.balls >= self.hp_cost :
            player.balls -= self.hp_cost
            player_manager: PlayerManager = self._env.player_manager
            player_manager.create_and_give_item_to_player(player, item_name = "DragonScale")
            self.success = True
        
    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        boost stats of dragons
        """
        team_battlers = self.get_team_cards_of_holder(context)
        if render:
            render("|-message|Lance's Hero Power Activates!") 

        for battler in team_battlers:
            team = self.get_team_of_holder(context)

            card = battler.battlecard
            if ((card.poke_type1 == PokemonType.dragon) | (card.poke_type2 == PokemonType.dragon) ) :
                before = card.attack
                card.modifiers[Stats.ATK.value] += 2
                after = card.attack
                if logger is not None:
                    logger(
                        'LanceFetish pre_battle',
                        f"{card.name.name} ATK {before:.1f} -> {after:.1f}"
                    )
                if render:
                    render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|atk|"+ round(after/card.atk_, 2) ) 

        for battler in team_battlers:
            card = battler.battlecard
            if ((card.poke_type1 == PokemonType.dragon) | (card.poke_type2 == PokemonType.dragon) ) :
                before = card.defense
                card.modifiers[Stats.DEF.value] += 2
                after = card.defense
                if logger is not None:
                    logger(
                        'LanceFetish pre_battle',
                        f"{card.name.name} DEF {before:.1f} -> {after:.1f}"
                    )
                if render:
                    render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|def|"+ round(after/card.def_, 2) ) 


class WillSac(PlayerHeroPower):
    
    hp_cost: int = 1
    success: bool = False
    used: bool = False

    def turn_setup(self):
        self.success = False
        self.used = False

    def use(self, player: "Player" = None):
        """
        get hurt, get $ 
        """
        if player.hitpoints > self.hp_cost :
            player.hitpoints -= self.hp_cost
            player.flute_charges += 1
            player.balls += 3
            self.success = True


class KogaNinja(ComplexHeroPower):

    hp_cost: int = 2
    unseal_cost = 4

    def post_battle_action(self, **context: T.Any):
        """
        if win, lower unseal cost
        """
        pass
    
    def use(self, player: "Player" = None):
        if self.unseal_cost == 0:
            if player.balls > self.hp_cost :
                player.balls -= self.hp_cost
                player_manager: PlayerManager = self._env.player_manager
                eevees = ['jolteon', 'vaporeon', 'flareon']
                player_manager.create_and_give_pokemon_to_player(player, random.choice(eevees))

        
class SurgeGorilla(PassiveHeroPower):

    def pre_battle_action(self, logger: "EventLogger" = None,render: "RenderLogger" = None, **context: T.Any):
        """
        check largest matching type, apply buff
        """
        team_battlers = self.get_team_cards_of_holder(context)
        types = []
        for battler in team_battlers:
            if battler.poke_type1 != PokemonType.none:
                types.append(battler.poke_type1)
            if battler.poke_type2 != PokemonType.none:
                types.append(battler.poke_type2)
        best_type = max(types,key=types.count)

        if render:
            render("|-message|Lt. Surge's Hero Power Activates!") 

        for battler in team_battlers:
            team = self.get_team_of_holder(context)

            card = battler.battlecard
            if ((card.poke_type1 == best_type) | (card.poke_type2 == best_type) ) :
                before = card.attack
                card.modifiers[Stats.ATK.value] += 2
                after = card.attack
                if logger is not None:
                    logger(
                        'LanceFetish pre_battle',
                        f"{card.name.name} ATK {before:.1f} -> {after:.1f}"
                    )
                if render:
                    render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|atk|"+ round(after/card.atk_, 2) ) 

        for battler in team_battlers:
            card = battler.battlecard
            if ((card.poke_type1 == best_type) | (card.poke_type2 == best_type) ) :
                before = card.defense
                card.modifiers[Stats.DEF.value] += 2
                after = card.defense
                if logger is not None:
                    logger(
                        'LanceFetish pre_battle',
                        f"{card.name.name} DEF {before:.1f} -> {after:.1f}"
                    )
                if render:
                    render("|-boost|p" + str(team)+ "b: " +battler.nickname+ "|def|"+ round(after/card.def_, 2) ) 


class RedCheater(PassiveHeroPower):
    """
    give plot device at start of game
    """

    def StartOfGame(self, player: "Player" = None):
        player_manager: PlayerManager = self._env.player_manager 
        player_manager.create_and_give_item_to_player(player, item_name = "RedCooking")


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
