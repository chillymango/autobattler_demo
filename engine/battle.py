"""
NOTE: UNDEPRECATED!!!!
Battle Manager
"""
import copy
import typing as T

from engine.base import Component
from engine.batterulogico import battle
from engine.batterulogico import Event
from engine.models.association import PokemonHeldItem
from engine.models.battle import BattleStat
from engine.models.battle import BattleStatus
from engine.models.battle import BattleSummary
from engine.models.items import CombatItem
from engine.models.player import Player
from engine.models.pokemon import BattleCard, Pokemon
from engine.models.stats import Stats

if T.TYPE_CHECKING:
    from engine.player import PlayerManager


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.

    Provides a game interface into the mystical batterulogico module.
    """

    REPORT_DIALOG = True
    ENV_PROXY = 'battle'

    def initialize(self):
        """
        Load movesets from data file
        """
        super().initialize()

    def get_team(self, player: Player) -> T.List[Pokemon]:
        """
        Get a Player team
        """
        player_manager: "PlayerManager" = self.env.player_manager
        return player_manager.player_team(player)

    def assemble_team_cards(self, player: Player) -> T.List[BattleCard]:
        """
        Get a set of battle cards with modifiers attached.
        """
        player_manager: "PlayerManager" = self.env.player_manager
        player.party_config.populate_team_from_party()
        team = self.get_team(player)

        cards: T.List[BattleCard] = []
        for poke in team:
            if poke is None:
                continue
            battle_card = copy.copy(poke.battle_card)

            # adjust stats by just incrementing IVs
            # we may want a dedicated field for this in the future but this should suffice...
            battle_card.a_iv += poke.modifiers[Stats.ATK.value]
            battle_card.d_iv += poke.modifiers[Stats.DEF.value]
            battle_card.hp_iv += poke.modifiers[Stats.HP.value]
            cards.append(battle_card)

            # give any held items
            battle_card.give_item(PokemonHeldItem.get_held_item(poke))

        return cards

    def battle(self, player1: Player, player2: Player):
        """
        Run a battle between two players using the batterulogico engine.
        """
        p1_cards = self.assemble_team_cards(player1)
        p2_cards = self.assemble_team_cards(player2)
        return battle(p1_cards, p2_cards)

    def turn_execute(self):
        """
        For all matches, run battles.
        """
        matches = self.state.current_matches
        for match in matches:
            p1 = self.state.get_player_by_id(match.player1)
            p2 = self.state.get_player_by_id(match.player2)
            res = self.battle(p1, p2)

            events: T.List[Event] = res.get('events', [])
            recipients = (p1, p2)
            for event in events:
                if event.type == "faint":
                    msg = (event.value.replace("team1", f"{p1.name}'s")
                                      .replace("team2", f"{p2.name}'s"))
                    self.log(msg=msg, recipient=recipients)
                if event.type:
                    print(f"[{event.id}]: {event.type} - {event.value}")

            if res['winner'] == 'team1':
                self.log(msg=f"{p1} beats {p2}", recipient=recipients)
                losing_player = (p2,)
            elif res['winner'] == 'team2':
                self.log(msg=f"{p2} beats {p1}", recipient=recipients)
                losing_player = (p1,)
            else:
                self.log(msg=f"{p1} and {p2} tie", recipient=recipients)
                losing_player = (p1, p2)

            if losing_player is not None:
                for player in losing_player:
                    if self.state.stage.stage <= 4:
                        player.hitpoints -= 2
                    elif self.state.stage.stage <= 7:
                        player.hitpoints -= 4
                    else:
                        player.hitpoints -= 6
            stats = dict()
            team1 = self.get_team(p1)
            team2 = self.get_team(p2)
            team1_battle_dict = {
                'damagedealt': res['team1damagedealt'], 'damagetaken': res['team1damagetaken']
            }
            team2_battle_dict = {
                'damagedealt': res['team2damagedealt'], 'damagetaken': res['team2damagetaken']
            }
            stats.update(self.calcualate_battle_stats(team1, team1_battle_dict))
            stats.update(self.calcualate_battle_stats(team2, team2_battle_dict))

            summary = BattleSummary(
                winner=res['winner'],
                player1_id = p1.id,
                player2_id=p2.id,
                team1=[poke.id for poke in team1],
                team2=[poke.id for poke in team2],
                battle_stats=stats
            )
            # TODO: render
            msg = f"Battle between {p1} and {p2}"
            msg += f"Team 1 Summary:\n\t" + "\n\t".join(
                [f"{poke.nickname} - {summary.battle_stats[poke.id]}" for poke in team1]
            )
            msg += "\n\n"
            msg += f"Team 2 Summary:\n\t" + "\n\t".join(
                [f"{poke.nickname} - {summary.battle_stats[poke.id]}" for poke in team2]
            )
            msg += "\n\n"
            self.log(msg=msg, recipient=recipients)

    def calcualate_battle_stats(self, team: T.List[Pokemon], battle_dict: T.Dict) -> BattleStat:
        stats: T.Dict[str, BattleStat] = dict()
        for idx, poke in enumerate(team):
            stats[poke.id] = BattleStat(
                poke_id=poke.id,
                damage_taken=battle_dict['damagetaken'][idx],
                damage_dealt=battle_dict['damagedealt'][idx],
                # TODO: implement
                battle_status=BattleStatus.UNKNOWN
            )
        return stats
