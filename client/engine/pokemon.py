"""
Pokemon Object Representation
"""
import typing as T
from collections import defaultdict
from collections import namedtuple
from uuid import uuid4
import random
from engine.base import Component
import pandas as pd

DEFAULT_XP_GAIN = 50.0


EvolutionConfig = namedtuple("EvolutionConfig", ["evolved_form", "turns_to_evolve"])


class Pokemon:
    """
    Instantiate unique object based on name
    """

    def __init__(
        self,
        pokemon_name,
        battle_card,
        nickname,
        id=None, 
    ):
        self.name: str = pokemon_name
        self.battle_card: BattleCard = battle_card
        self.id = id or uuid4()
        self.item = None
        self.xp: float = 0
        self.nickname = nickname

    def __str__(self):
        return ("Shiny" * self.battle_card.shiny + " {}".format(self.nickname)).strip()

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

    def __repr__(self):
        return "BattleCard({}): {}".format(self.name, self.to_string())


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
    NAME_PATH = "qtassets/sanitized_names.csv"

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
        self.nickname_map = pd.read_csv(self.NAME_PATH)
        mew_m_fast = ['SNARL', 'DRAGON_TAIL', 'VOLT_SWITCH', 'INFESTATION', 'SHADOW_CLAW', 'POUND', 'STEEL_WING', 'POISON_JAB', 'CHARGE_BEAM', 'FROST_BREATH', 'DRAGON_TAIL', 'ROCK_SMASH', 'WATERFALL']
        mew_m_charged = ['ANCIENT_POWER','DRAGON_CLAW','ICE_BEAM','HYPER_BEAM','SOLAR_BEAM','THUNDER_BOLT','FLAME_CHARGE','LOW_SWEEP','ENERGY_BALL','STONE_EDGE','GYRO_BALL','DARK_PULSE','DAZZLING_GLEAM','SURF']
        porygon_m_fast = ["HIDDEN_POWER_BUG",
                "HIDDEN_POWER_DARK",
                "HIDDEN_POWER_DRAGON",
                "HIDDEN_POWER_ELECTRIC",
                "HIDDEN_POWER_FIGHTING",
            "HIDDEN_POWER_FIRE",
            "HIDDEN_POWER_FLYING",
            "HIDDEN_POWER_GHOST",
            "HIDDEN_POWER_GRASS",
            "HIDDEN_POWER_GROUND",
            "HIDDEN_POWER_ICE",
            "HIDDEN_POWER_POISON",
            "HIDDEN_POWER_PSYCHIC",
            "HIDDEN_POWER_ROCK",
            "HIDDEN_POWER_STEEL",
            "HIDDEN_POWER_WATER"   ]
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

    def get_nickname_by_pokemon_name(self, pokemon_name):
        return self.nickname_map[self.nickname_map.name == pokemon_name].sanitized_name.iloc[0]

    def create_pokemon_by_name(self, pokemon_name):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_default_battle_card(pokemon_name)
        if pokemon_name == 'mew':
            battle_card.move_f = random.choice(self.mew_m_fast)
            battle_card.move_ch = random.choice(self.mew_m_charged)
        if pokemon_name == 'porygon':
            battle_card.move_f = random.choice(self.porygon_m_fast)


        nickname = self.get_nickname_by_pokemon_name(pokemon_name)
        return Pokemon(pokemon_name, battle_card, nickname)

    def create_PVEpokemon_by_name(self, pokemon_name):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_PVE_battle_card(pokemon_name)
        battle_card.bonus_shield = -1
        nickname = self.get_nickname_by_pokemon_name(pokemon_name)
        return Pokemon(pokemon_name, battle_card, nickname)


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

    def evolve(self, pokemon: Pokemon):
        """
        Perform an in-place evolution operation on a Pokemon

        Process:
        * check if evolution is valid
        * reset pokemon XP
        * get evolved form by name
        * create evolved form battle card
        * update nickname if it's default nickname, otherwise retain nickname
        """
        # check evolution
        evolved_form = self.get_evolution(pokemon.name)
        if evolved_form is None:
            return

        # reset xp
        pokemon.xp = 0

        # get battle card
        pokemon_factory: PokemonFactory = self.state.pokemon_factory
        evolved_card = pokemon_factory.get_evolved_battle_card(
            evolved_form, pokemon.battle_card
        )

        # if nickname is default, update nickname
        if pokemon_factory.get_nickname_by_pokemon_name(pokemon.name) == pokemon.nickname:
            pokemon.nickname = pokemon_factory.get_nickname_by_pokemon_name(evolved_form)

        # update name and battle card
        pokemon.name = evolved_form
        pokemon.battle_card = evolved_card

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
                        'Party member {} XP exceeds threshold ({} >= {})'
                        .format(party_member.name, party_member.xp, threshold)
                    )
                    self.evolve(party_member)
