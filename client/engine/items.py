"""
Items and Inventory
"""
from engine.state import GameState
from engine.pokemon import EvolutionManager, PokemonFactory

class PokePermItem:
    def __init__(self, name, state):
        self.name = name
        self.state = state


    def use(self, player,pokemon ):
        """
        check to see if the item is in the inventory, then use it if it is there
        """
        evolution_manager: EvolutionManager = self.state.evolution_manager
        pokemon_factory: PokemonFactory = self.state.pokemon_factory
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




class _Item:
    """
    Base class for items
    """
    #permanent items
    #eviolite: def buff if NFE
    #choice specs: your fast move becomes lock on (or maybe yawn?). +2 attack buff
    #choice band: your charged move(s) become frustration. +2 attack buff
    #weakness policy: if opponent has super effective move, +1 attack buff

    #global items
    #master ball: next buy is free
    #poke flute: next N rerolls are free

    #battle items: one round only
    #ganlon berry: an extra shield
    #oran berry: if poke survives a fight, restore 10%hp
    #sitrus berry: if poke survives a fight, restore 30%hp
    #leppa berry: start with 10 energy
    #power herb: start with 30 energy
    #salac berry: if poke survives, gain 40 energy
    #focus band: if poke dies, revive at back of team with 1hp and 100 energy



    def use(self):
        """
        Callback for item use
        """


class _Consumable:
    """
    Consumable item. Disappears after one use.
    """
