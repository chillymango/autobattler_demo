"""
Pokemon Object Representation
"""
import random
import pandas as pd
import typing as T
from collections import defaultdict

from engine.base import Component
from engine.models.enums import Move, PokemonId, PokemonType
from engine.models.pokemon import BattleCard
from engine.models.pokemon import EvolutionConfig
from engine.models.pokemon import Pokemon

if T.TYPE_CHECKING:
    from engine.player import PlayerManager
    from engine.shop import ShopManager


class TmManager(Component):
    """
    Records Pokemon TM (Technical Machine) move modifications
    """

    CONFIG_PATH = 'data/tm_movesets.txt'

    def initialize(self):
        """
        Load default TMs for all Pokemon
        """
        super().initialize()
        with open(self.CONFIG_PATH, 'r') as tm_movesets_file:
            tm_movesets_raw = tm_movesets_file.readlines()

        self.tm_movesets = defaultdict(lambda: None)
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

    CONFIG_PATH = 'data/default_movesets.txt'
    CONFIG_PATH_PVE = 'data/PVE_movesets.txt'
    NAME_PATH = "data/sanitized_names.csv"

    MOVE_REFERENCE_PATH = "data/move_types.csv"
    TYPE_REFERENCE_PATH = "data/pokemon_types.csv"

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
        self.mew_m_fast = ['SNARL', 'DRAGON_TAIL', 'VOLT_SWITCH', 'INFESTATION', 'SHADOW_CLAW', 'POUND', 'STEEL_WING', 'POISON_JAB', 'CHARGE_BEAM', 'FROST_BREATH', 'DRAGON_TAIL', 'ROCK_SMASH', 'WATERFALL']
        self.mew_m_charged = ['ANCIENT_POWER','DRAGON_CLAW','ICE_BEAM','HYPER_BEAM','SOLAR_BEAM','THUNDER_BOLT','FLAME_CHARGE','LOW_SWEEP','ENERGY_BALL','STONE_EDGE','GYRO_BALL','DARK_PULSE','DAZZLING_GLEAM','SURF']
        self.porygon_m_fast = [
            "HIDDEN_POWER_BUG",
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
            "HIDDEN_POWER_WATER"
        ]

        self.move_reference = pd.read_csv(self.MOVE_REFERENCE_PATH)
        self.type_reference = pd.read_csv(self.TYPE_REFERENCE_PATH)

    def get_pokemon_type_reference(self, name: str) -> T.Tuple[PokemonType, PokemonType]:
        """
        Get the Pokemon type reference

        TODO: read from gamemaster instead of loading a manual file
        """
        type1 = self.type_reference[self.type_reference.name == name].type1.iloc[0].lower()
        type2 = self.type_reference[self.type_reference.name == name].type2.iloc[0].lower()
        if type2 == 'no type':
            type2 = "none"  # feed into enum
        return (PokemonType[type1], PokemonType[type2])

    def get_move_type_reference(self, move: str) -> PokemonType:
        # TODO: fix this handling
        if move == 'none':
            return PokemonType.none

        return PokemonType[
            self.move_reference[self.move_reference.move == move].type.iloc[0].lower()
        ]

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
            tm_move = self.env.tm_manager.get_tm_move(evolved_form)
            evolved_card.set_tm_move(tm_move)

        return evolved_card

    def get_nickname_by_pokemon_name(self, pokemon_name):
        return self.nickname_map[self.nickname_map.name == pokemon_name].sanitized_name.iloc[0]

    def create_pokemon_by_name(self, pokemon_name: str):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_default_battle_card(pokemon_name)
        if pokemon_name == 'mew':
            battle_card.move_f = Move[random.choice(self.mew_m_fast)]
            battle_card.move_ch = Move[random.choice(self.mew_m_charged)]
        if pokemon_name == 'porygon':
            battle_card.move_f = Move[random.choice(self.porygon_m_fast)]
        return self.create_pokemon(pokemon_name, battle_card)

    def create_PVEpokemon_by_name(self, pokemon_name: str):
        """
        Create a new Pokemon by pokemon name.

        Example, pass in `pikachu` to create a default Pikachu.
        """
        battle_card = self.get_PVE_battle_card(pokemon_name)
        battle_card.bonus_shield = -1
        return self.create_pokemon(pokemon_name, battle_card)

    def create_pokemon(self, pokemon_name: str, battle_card: BattleCard):
        """
        Create a Pokemon by name
        """
        types = self.get_pokemon_type_reference(pokemon_name)
        fast_move_type = self.get_move_type_reference(battle_card.move_f.name)
        charged_move_type = self.get_move_type_reference(battle_card.move_ch.name)
        tm_move_type = self.get_move_type_reference(battle_card.move_tm.name)

        if types[0] is not None:
            battle_card.poke_type1 = types[0]
        else:
            battle_card.poke_type1 = None

        if types[1] is not None:
            battle_card.poke_type2 = types[1]
        else:
            battle_card.poke_type2 = None

        battle_card.f_move_type = fast_move_type
        battle_card.ch_move_type = charged_move_type
        battle_card.tm_move_type = tm_move_type
        nickname = self.get_nickname_by_pokemon_name(pokemon_name)

        return Pokemon(name=PokemonId[pokemon_name], battle_card=battle_card, nickname=nickname)


class EvolutionManager(Component):
    """
    Pokemon Evolution Manager
    """

    XP_PER_TURN = 50.0

    CONFIG_PATH = "data/evolutions_list.txt"

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

    def evolve(self, pokemon: Pokemon, choice: str = None):
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

        if choice is not None:
            # check choice evolutions
            # TODO: implement
            return

        # reset xp
        pokemon.xp = 0

        # get battle card
        pokemon_factory: PokemonFactory = self.env.pokemon_factory
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
            player_manager: "PlayerManager" = self.env.player_manager
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
                    shop_manager: "ShopManager" = self.env.shop_manager
                    shop_manager.shiny_checker(player, party_member.name)
