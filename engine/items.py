"""
Items and Inventory
"""
from pydantic import BaseModel


class PokePermItem(BaseModel):

    name: str

    def use(self, pokemon, player):
        if self.name == 'TM':
            if pokemon.battle_card.tm_flag == 1:
                print('It had no effect')
            else:
                pokemon.battle_card.tm_flag = 1
    
                player.remove_item(self.name)


class _Item:
    """
    Base class for items
    """
    #permanent items
    #rare candy: XP+1
    #fire stone: if type1 == fire or type2 == fire: XP+3
    #water stone: if type1 == water or type2 == water: XP+3
    #leaf stone: if type1 == grass or type2 == grass: XP+3
    #thunder stone: if type1 == electric or type2 == electric: XP+3
    #eviolite: def buff if NFE
    #choice specs: your fast move becomes lock on. +2 attack buff
    #choice band: your charged move(s) become frustration. +2 attack buff
    #weakness policy: if opponent has super effective move, +1 attack buff

    #global items
    #rental ditto: clone a poke
    #master ball: next buy is free
    #poke flute: next N rerolls are free

    #battle items: use and consume
    #ganlon berry: an extra shield
    #oran berry: if poke survives a fight, restore 10hp
    #sitrus berry: if poke survives a fight, restore 30 hp
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
