"""
Matchmaker

The class in this module is responsible for creating pairs for matches.
"""
import typing as T
from collections import defaultdict
from itertools import combinations
from random import shuffle

from engine.base import Component
from engine.models.enums import PokemonId
from engine.models.match import Match
from engine.models.player import EntityType
from engine.models.player import Player
from engine.player import PlayerManager

if T.TYPE_CHECKING:
    from engine.pokemon import PokemonFactory


class CreepRoundManager(Component):
    """
    Responsible for creating Creep Rounds

    Creates creep players and assigns Pokemon as required.

    Creep Pokemon do not have spare party members -- i.e they will run three units in both
    party and team for a predetermined matchup.
    """

    CONFIG_PATH = "data/creep_rounds.txt"

    def initialize(self):
        self.creep_round_pokemon = defaultdict(lambda: [])
        with open(self.CONFIG_PATH, 'r') as creep_rounds_file:
            creep_rounds_raw = creep_rounds_file.readlines()

        pokemon_factory: PokemonFactory = self.env.pokemon_factory

        for idx, line in enumerate(creep_rounds_raw):
            round_num = None
            if line.startswith('#'):
                continue
            try:
                round_num = int(line)
                # load the next six lines with it
                pokemon_names = [
                    pokemon.strip().split(',')[0] for pokemon in creep_rounds_raw[idx + 1:idx + 7]
                ]
                team = [
                    pokemon_factory.create_PVEpokemon_by_name(pokemon) for pokemon in pokemon_names
                ]
                self.creep_round_pokemon[round_num] = team
            except ValueError:
                # re-raise exception if a line number was parseable
                if round_num is not None:
                    print('Error parsing creep round {}'.format(round_num))
                    raise

    def create_creep_player(self):
        # do a lookup based on the current run
        creep_player = Player(name="Creep Round", type=EntityType.CREEP)
        self.state.creeps.append(creep_player)
        player_manager: PlayerManager = self.env.player_manager
        turn = self.state.turn_number
        for pokemon in self.creep_round_pokemon[turn]:
            player_manager.give_pokemon_to_player(creep_player, pokemon)
        return creep_player

    def remove_creeps(self):
        """
        Wipe all creep round players
        """
        for creep in self.state.creeps:
            creep.delete()
        self.state.creeps = []

    def organize_creep_round(self):
        """
        Organize a round with 'creep' players. All humans and computers that are still alive
        will play against creep opponents.
        """
        matches = []
        for player in self.state.players:
            creep_player = self.create_creep_player()
            match = Match(player1=player.id, player2=creep_player.id)
            matches.append(match)

        return matches

    def organize_clone_round(self):
        """
        TODO: should be able to also create random clones of other teams.
        """
        return self.create_creep_player()


class Matchmaker(Component):
    """
    Takes a list of players. Stores previous match history and uses this in priority
    assessment for future matches.
    """

    @property
    def current_matches(self):
        return self.matches[-1]

    def initialize(self):
        self.players = {
            EntityType.HUMAN: [x for x in self.state.players if x.type == EntityType.HUMAN],
            EntityType.COMPUTER: [x for x in self.state.players if x.type == EntityType.COMPUTER],
        }
        self.matches: T.List[T.List[Match]] = [[]]
        self.opponents_by_player = defaultdict(lambda: [])


    @staticmethod
    def get_player_opponent_in_round(player, matches: T.List[Match]):
        """
        In a group of matches, determine the one the specified player is participating in.

        Return the player object for their opponent. Return None if player is not participating.
        """
        for match in matches:
            if match.has_player(player.id):
                if match.player1 == player:
                    return match.player2
                return match.player1

        return None

    @property
    def turn(self):
        """
        Current turn number according to the matchmaker

        NOTE: this could fall out of sync with the game env, may be worth syncing
        with a global or something
        """
        return len(self.matches)

    def previous_match_between_players(self, player1_id: str, player2_id: str):
        """
        Determine what round the provided players last played a match in.
        """
        for idx, matches in enumerate(reversed(self.matches)):
            for match in matches:
                if match.has_player(player1_id) and match.has_player(player2_id):
                    return self.turn - idx - 1

        return 0

    def organize_round(self):
        """
        Organize a round between human and 'computer' players.
        Returns a dict that returns a Match object

        Round matchmaking is done by giving every potential match a score.

        Lowest average scores are selected for matches.
        This is done by sorting the pair scores in order and then selecting pairs in ascending
        order, so long as both parties have not been assigned to a match already.

        Score modifications:
        * played last round (80)
        * played two rounds ago (60)
        * played three rounds ago (40)
        * played four rounds ago (20)
        * played five+ rounds ago (0)
        * previous match results do not match (35)

        If there are an odd number of players to match, the algorithm above will run and the
        left over player will receive a creep round matchup.
        """
        # find who is still alive
        live_players: T.List[Player] = []
        for human in self.players[EntityType.HUMAN]:
            if human.is_alive:
                live_players.append(human)
        for computer in self.players[EntityType.COMPUTER]:
            if computer.is_alive:
                live_players.append(computer)

        # list potential matches
        all_matches = [Match(player1=p1.id, player2=p2.id) for p1, p2 in combinations(live_players, 2)]
        shuffle(all_matches)  # to prevent guessing of matches based on lobby order

        # calculate match scores based on match history
        match_scores = dict()  # maps Match to integer score
        for match in all_matches:
            # check when the last time they played was and add score accordingly
            last_played = self.previous_match_between_players(*match.players)
            if last_played:
                delta = self.turn - last_played
                recency_score = max(4 - delta, 0) * 20
            else:
                recency_score = 0

            # TODO: implement power matching later
            powermatch_score = 0

            # aggregate
            match_scores[match] = recency_score + powermatch_score

        # sort match scores ascending and pull the first values
        sorted_scores = dict(sorted(match_scores.items(), key=lambda item: item[1]))
        remaining_players = [player.id for player in live_players]
        idx = 0
        determined_matches = []
        while remaining_players and idx < len(sorted_scores):
            match: Match = list(sorted_scores.keys())[idx]
            if match.players[0] in remaining_players and match.players[1] in remaining_players:
                determined_matches.append(match)
                remaining_players.remove(match.players[0])
                remaining_players.remove(match.players[1])
            idx += 1

        if len(remaining_players) > 1:
            raise ValueError("More than one player left over. What the hell happened!")
        elif len(remaining_players) == 1:
            # organize a creep round for this player
            creep_player = self.env.creep_round_manager.create_creep_player()
            match = Match(player1=remaining_players[0].id, player2=creep_player.id)
            determined_matches.append(match)

        # update player opponent history
        for match in determined_matches:
            self.opponents_by_player[match.players[0]].append(match.players[1])
            self.opponents_by_player[match.players[1]].append(match.players[0])

        return determined_matches

    def turn_setup(self):
        """
        If a creep round is determined for everyone, do nothing. The creep round
        manager should have organized a creep round.
        If there is no creep round, organize a player round.
        """
        print('Running Matchmaker')
        creep_round_manager: CreepRoundManager = self.env.creep_round_manager
        creeps = creep_round_manager.creep_round_pokemon[self.state.turn_number]
        if not any(creeps):
            print('Trying to organize real round')
            self.state.current_matches = self.organize_round()
        else:
            print('Trying to organize creep round')
            # remove any existing creeps first
            creep_round_manager.remove_creeps()
            self.state.current_matches = creep_round_manager.organize_creep_round()

    def turn_cleanup(self):
        """
        Update matches with what was played
        """
        self.matches.append(self.state.current_matches)
