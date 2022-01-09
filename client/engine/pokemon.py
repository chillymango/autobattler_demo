"""
Pokemon Object Representation
"""
import typing as T
from collections import defaultdict
from collections import namedtuple
from uuid import uuid4

from engine.base import Component

DEFAULT_XP_GAIN = 50.0


EvolutionConfig = namedtuple("EvolutionConfig", ["evolved_form", "turns_to_evolve"])


class TmManager(Component):
    """
    Records Pokemon TM (Technical Machine) move modifications
    """

    CONFIG_PATH = 'engine/data/tm_movesets.txt'

    def initialize(self):
        """
        Load default TMs for all Pokemon
        """
        super().initialize()
        with open(self.CONFIG_PATH, 'r') as tm_movesets_file:
            tm_movesets_raw = tm_movesets_file.readlines()

        self.tm_movesets = defaultdict(lambda: "RETURN")
        for row in tm_movesets_raw:
            pokemon, tm_move = row.split()
            self.tm_movesets[pokemon] = tm_move.strip().upper()

    def get_tm_move(self, pokemon):
        """
        Get a TM move for a Pokemon
        """
        return self.tm_movesets[pokemon]


class PokemonFactory(Component):
    """
    Supports creating Pokemon instances
    """

    CONFIG_PATH = 'engine/data/default_movesets.txt'
    CONFIG_PATH_PVE = 'engine/data/PVE_movesets.txt'

    def initialize(self):
        """
        Load default movesets for all Pokemon when instantiating them.
        """
        super().initialize()
        with open(self.CONFIG_PATH, 'r') as default_movesets_file:
            default_movesets_raw = default_movesets_file.readlines()

        self.default_movesets = {}  # maps pokemon name to default BattleCard
        for line in default_movesets_raw:
            pokemon_name = line.split(',')[0]
            self.default_movesets[pokemon_name] = line

        with open(self.CONFIG_PATH_PVE, 'r') as PVE_movesets_file:
            PVE_movesets_raw = PVE_movesets_file.readlines()

        self.PVE_movesets = {}  # maps pokemon name to default BattleCard
        for line in PVE_movesets_raw:
            pokemon_name = line.split(',')[0]
            self.PVE_movesets[pokemon_name] = line

    def get_PVE_battle_card(self, pokemon_name):
        """
        Load the default battle card for a Pokemon
        """
        return BattleCard.from_string(self.PVE_movesets[pokemon_name])

    def get_default_battle_card(self, pokemon_name):
        """
        Load the default battle card for a Pokemon
        """
        return BattleCard.from_string(self.default_movesets[pokemon_name])

    def get_evolved_battle_card(self, evolved_form, battle_card):
        """
        Get an evolved battle card.

        Takes the original battle card and checks for tm_flag and shiny being set.
        These properties will be persisted to the new card.
        """
        evolved_card = BattleCard.from_string(self.default_movesets[evolved_form])
        if battle_card.shiny:
            evolved_card.make_shiny()
        if battle_card.tm_flag:
            tm_move = self.state.tm_manager.get_tm_move(evolved_form)
            evolved_card.set_tm_move(tm_move)

        return evolved_card

    def create_pokemon_by_name(self, pokemon_name):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_default_battle_card(pokemon_name)
        return Pokemon(pokemon_name, battle_card)

    def create_PVEpokemon_by_name(self, pokemon_name):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_PVE_battle_card(pokemon_name)
        battle_card.bonus_shield = -1
        return Pokemon(pokemon_name, battle_card)


class EvolutionManager(Component):
    """
    Pokemon Evolution Manager
    """

    XP_PER_TURN = 50.0

    CONFIG_PATH = "engine/data/evolutions_list.txt"

    def initialize(self):
        with open(self.CONFIG_PATH, 'r') as evolution_list_file:
            evolutions_raw = evolution_list_file.readlines()
        self.evolution_config: T.Dict[str, EvolutionConfig] = defaultdict(lambda: None)
        for line in evolutions_raw:
            base, turns, evolved = line.split()
            turns = int(turns)
            self.evolution_config[base] = EvolutionConfig(evolved, turns)

    def get_evolution(self, pokemon_name):
        """
        Look up the evolution of a Pokemon by name
        """
        if pokemon_name not in self.evolution_config:
            return None
        return self.evolution_config[pokemon_name].evolved_form

    def get_threshold(self, pokemon_name):
        """
        Look up the evolution XP threshold of a Pokemon by name
        """
        if pokemon_name not in self.evolution_config:
            return None
        return self.evolution_config[pokemon_name].turns_to_evolve * self.XP_PER_TURN

    def turn_cleanup(self):
        """
        After combat runs, update party Pokemon XP and initiate evolutions
        """
        for player in self.state.players:
            if not player.is_alive:
                continue
            for party_member in player.party:
                if party_member is None or party_member.name not in self.evolution_config:
                    continue
                party_member.add_xp(self.XP_PER_TURN)
                threshold = self.get_threshold(party_member.name)
                if party_member.xp >= threshold:
                    print(
                        'Party member {} XP exceeds threshold ({} > {})'
                        .format(party_member.name, party_member.xp, threshold)
                    )
                    # reset XP
                    party_member.xp = 0

                    # look up the evolution of a pokemon
                    evolved_form = self.get_evolution(party_member.name)
                    pokemon_factory: PokemonFactory = self.state.pokemon_factory
                    evolved_card = pokemon_factory.get_evolved_battle_card(
                        evolved_form, party_member.battle_card
                    )

                    # update pokemon
                    party_member.name = evolved_form
                    party_member.battle_card = evolved_card


class Pokemon:
    """
    Instantiate unique object based on name
    """

    def __init__(
        self,
        pokemon_name,
        battle_card,
        id=None,
    ):
        self.name = pokemon_name
        self.battle_card = battle_card
        self.id = id or uuid4()
        self.item = None
        self.xp = 0

    def __str__(self):
        return ("Shiny" * self.battle_card.shiny + " {}".format(self.name)).strip()

    def __repr__(self):
        return "{} ({})".format(self.name, self.id)

    def add_xp(self, amount=DEFAULT_XP_GAIN):
        """
        Add experience to a Pokemon
        """
        self.xp += amount


class BattleCard:
    """
    Pokemon Combat Representation

    Each Pokemon should have this instantiated
    """

    SHINY_POWER_FACTOR = 1.3  # multiply attack and defense by this number

    def __init__(
        self,
        name,
        move_f,
        move_ch,
        move_tm,
        level,
        a_iv,
        d_iv,
        hp_iv,
        tm_flag=False,
        shiny=False,
        health= 0,
        energy = 0,
        bonus_shield = 0,
        status = 1
    ):
        """
        Battle Card representation for a Pokemon.

        This should be generated by a Pokemon entry from a player roster and should be fed
        to the battle simulator.
        """
        self.name = name
        self.move_f = move_f
        self.move_ch = move_ch
        self.move_tm = move_tm
        self.level = int(level)
        self.a_iv = int(a_iv)
        self.d_iv = int(d_iv)
        self.hp_iv = int(hp_iv)
        self.tm_flag = tm_flag
        self.shiny = shiny
        self.health = health
        self.energy = energy
        self.bonus_shield = bonus_shield
        self.status = status  

    def make_shiny(self):
        """
        Mark a Pokemon as shiny and adjust stats.

        Does nothing if the Pokemon is already shiny.
        """
        if self.shiny:
            return False
        self.shiny = True
        #self.a_iv *= self.SHINY_POWER_FACTOR
        #self.d_iv *= self.SHINY_POWER_FACTOR
        return True

    def set_tm_move(self, move):
        """
        Add a TM move to a Pokemon

        Does nothing if the Pokemon already has a TM move.
        """
        if self.tm_flag:
            return False
        self.tm_flag = True
        self.move_tm = move.lower()
        return True

    @classmethod
    def from_string(cls, string):
        """
        Parse from a comma-delimited string

        This will initialize as a default.
        """
        l = string.split(',')
        return BattleCard(
            name = l[0],
            move_f = l[1],
            move_ch = l[2],
            move_tm = l[3],
            level = l[4],
            a_iv = l[5], 
            d_iv = l[6], 
            hp_iv = l[7],
            tm_flag = 0,
            shiny = 0
        )

    def to_string(self):
        """
        Return a PvPoke string representation of the Pokemon
        """
        return ",".join(str(x) for x in [
            self.name,
            self.move_f,
            self.move_ch,
            self.move_tm,
            self.level,
            self.a_iv,
            self.d_iv,
            self.hp_iv,
        ])
