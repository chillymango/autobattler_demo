"""
Matchmaker

The class in this module is responsible for creating pairs for matches.
"""
from collections import defaultdict
from itertools import combinations
from random import shuffle

from engine.base import Component
from engine.player import EntityType
from engine.player import Player
from engine.pokemon import Pokemon, PokemonFactory


class Match:
    """
    Represents a match between two players.
    """

    def __init__(self, player1, player2):
        self.players = (player1, player2)
        self._result = None  # set to player1 or player2

    def has_player(self, player):
        return player in self.players

    def __hash__(self):
        return hash(self.players)

    @property
    def result(self):
        return self._result

    @property
    def is_creep_match(self):
        return "Creep Round" in [player.name for player in self.players]

    @result.setter
    def set_result(self, winner):
        if winner not in self.players:
            raise ValueError(
                "Player {} did not play in match between {}".format(winner, self.players)
            )
        self._result = winner

    def __repr__(self):
        if self._result:
            resultstr = "{} wins".format(self._result)
        else:
            resultstr = "Not played"
        return "Match - ({}) vs ({}) ({})".format(self.players[0], self.players[1], resultstr)


class CreepRoundManager(Component):
    """
    Responsible for creating Creep Rounds

    Creates creep players and assigns Pokemon as required.

    Creep Pokemon do not have spare party members -- i.e they will run three units in both
    party and team for a predetermined matchup.
    """

    CONFIG_PATH = "engine/data/creep_rounds.txt"

    def initialize(self):
        self.creep_round_pokemon = defaultdict(lambda: [])
        with open(self.CONFIG_PATH, 'r') as creep_rounds_file:
            creep_rounds_raw = creep_rounds_file.readlines()

        pokemon_factory: PokemonFactory = self.state.pokemon_factory

        for idx, line in enumerate(creep_rounds_raw):
            if line.startswith('#'):
                continue
            try:
                round_num = int(line)
                # load the next three lines with it
                pokemon_names = [
                    pokemon.strip().split(',')[0] for pokemon in creep_rounds_raw[idx + 1:idx + 4]
                ]
                team = [
                    pokemon_factory.create_pokemon_by_name(pokemon) for pokemon in pokemon_names
                ]
                for pokemon in pokemon_names:
                    team.append(pokemon_factory.create_pokemon_by_name(pokemon))
                self.creep_round_pokemon[round_num] = team
            except ValueError:
                pass

    def create_creep_player(self):
        # do a lookup based on the current run
        creep_player = Player("Creep Round",type_=EntityType.CREEP)
        turn = self.state.turn.number
        creep_pokemon = self.creep_round_pokemon[turn]
        for idx, pokemon in enumerate(creep_pokemon):
            creep_player.add_to_party(pokemon)
            creep_player.add_party_to_team(idx)
        return creep_player

    def organize_creep_round(self):
        """
        Organize a round with 'creep' players. All humans and computers that are still alive
        will play against creep opponents.
        """
        matches = []
        for player in self.state.players:
            creep_player = self.create_creep_player()
            match = Match(player, creep_player)
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
        self.matches = [[]]
        self.opponents_by_player = defaultdict(lambda: [])


    @staticmethod
    def get_player_opponent_in_round(player, matches):
        """
        In a group of matches, determine the one the specified player is participating in.

        Return the player object for their opponent. Return None if player is not participating.
        """
        for match in matches:
            if match.has_player(player):
                if match.players[0] == player:
                    return match.players[1]
                return match.players[0]

        return None

    @property
    def turn(self):
        """
        Current turn number according to the matchmaker

        NOTE: this could fall out of sync with the game state, may be worth syncing
        with a global or something
        """
        return len(self.matches)

    def previous_match_between_players(self, player1, player2):
        """
        Determine what round the provided players last played a match in.
        """
        for idx, matches in enumerate(reversed(self.matches)):
            for match in matches:
                if match.has_player(player1) and match.has_player(player2):
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
        live_players = []
        for human in self.players[EntityType.HUMAN]:
            if human.is_alive:
                live_players.append(human)
        for computer in self.players[EntityType.COMPUTER]:
            if computer.is_alive:
                live_players.append(computer)

        # list potential matches
        all_matches = [Match(p1, p2) for p1, p2 in combinations(live_players, 2)]
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
        remaining_players = [player for player in live_players]
        idx = 0
        determined_matches = []
        while remaining_players and idx < len(sorted_scores):
            match = list(sorted_scores.keys())[idx]
            if match.players[0] in remaining_players and match.players[1] in remaining_players:
                determined_matches.append(match)
                remaining_players.remove(match.players[0])
                remaining_players.remove(match.players[1])
            idx += 1

        if len(remaining_players) > 1:
            raise ValueError("More than one player left over. What the hell happened!")
        elif len(remaining_players) == 1:
            # organize a creep round for this player
            creep_player = self.state.creep_round_manager.create_creep_player()
            match = Match(remaining_players[0], creep_player)
            determined_matches.append(match)

        # update player opponent history
        for match in determined_matches:
            self.opponents_by_player[match.players[0]].append(match.players[1])
            self.opponents_by_player[match.players[1]].append(match.players[0])

        return determined_matches
