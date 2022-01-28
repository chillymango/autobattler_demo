"""
Load Sprites for Pokemon
"""
import os
import typing as T
from collections import defaultdict

from engine.base import Component
from engine.models import items


class SpriteManager(Component):

    ASSETS_DIR = 'client/qtassets'

    ITEM_SPRITES_LOOKUP = 'data/item_sprites_manifest.txt'

    DISABLED = False

    def initialize(self):
        super().initialize()
        # load normie sprites
        self.normie_sprites = defaultdict(lambda: None)
        # NOTE: don't use os.path.join here because QtGui is stupid about path resolution on nt
        self.normie_base = '/'.join([self.ASSETS_DIR, 'sprites', 'normie'])
        for filename in os.listdir(self.normie_base):
            pokemon, _ = filename.split('.')
            self.normie_sprites[pokemon] = '/'.join([self.normie_base, filename])

        # load shiny sprites
        self.shiny_sprites = defaultdict(lambda: None)
        self.shiny_base = '/'.join([self.ASSETS_DIR, 'sprites', 'shiny'])
        for filename in os.listdir(self.shiny_base):
            pokemon, _ = filename.split('.')
            self.shiny_sprites[pokemon] = '/'.join([self.shiny_base, filename])

        # load type sprites
        self.type_sprites = defaultdict(lambda: None)
        self.type_base = '/'.join([self.ASSETS_DIR, 'sprites', 'typeicons'])
        for filename in os.listdir(self.type_base):
            typename, _ = filename.split('.')
            self.type_sprites[typename] = '/'.join([self.type_base, filename])

        # load trainer sprites
        self.trainer_sprites = defaultdict(lambda: None)
        self.trainer_base = '/'.join([self.ASSETS_DIR, 'sprites', 'trainer'])
        for filename in os.listdir(self.trainer_base):
            if os.path.isdir(os.path.join(self.trainer_base, filename)):
                continue
            trainername, _ = filename.split('.')
            self.trainer_sprites[trainername] = '/'.join([self.trainer_base, filename])

        # load PVE round sprites
        self.pve_round_sprites = defaultdict(lambda: None)
        self.pve_round_base = '/'.join([self.ASSETS_DIR, 'sprites', 'trainer', 'PVE'])
        for filename in os.listdir(self.pve_round_base):
            pveround, _ = filename.split('.')
            self.pve_round_sprites[pveround] = '/'.join([self.pve_round_base, filename])

        # load weather sprites
        self.weather_sprites = defaultdict(lambda: None)
        self.weather_base = '/'.join([self.ASSETS_DIR, 'sprites', 'weather'])
        for filename in os.listdir(self.weather_base):
            weathername, _ = filename.split('.')
            self.weather_sprites[weathername] = '/'.join([self.weather_base, filename])

        # load item sprites (directly)
        self.item_sprites = defaultdict(lambda: None)
        with open(self.ITEM_SPRITES_LOOKUP, 'r') as item_sprites_lookup:
            for line in item_sprites_lookup.readlines():
                try:
                    if line.startswith('#'):
                        continue
                    if not line.strip():
                        continue
                    klassname, path = line.strip().split()
                    item_base = '/'.join([self.ASSETS_DIR, 'sprites', 'itemicons'])
                    self.item_sprites[getattr(items, klassname)] = '/'.join([item_base, path])
                except Exception:
                    print(f'Failed to load sprites for {line}')

    def get_normie_sprite(self, pokemon_name):
        if not self.DISABLED:
            return self.normie_sprites[pokemon_name]
        return None

    def get_shiny_sprite(self, pokemon_name):
        if not self.DISABLED:
            return self.shiny_sprites[pokemon_name]
        return None

    def get_type_sprite(self, type_name: str):
        if not self.DISABLED:
            return self.type_sprites[type_name.capitalize()]
        return None

    def get_trainer_sprite(self, trainer_name: str) -> str:
        if not self.DISABLED:
            return self.trainer_sprites[trainer_name]
        return None

    def get_pve_round_sprite(self, creep_name: str):
        if not self.DISABLED:
            return self.pve_round_sprites[creep_name]
        return None

    def get_weather_sprite(self, weather_type: str) -> str:
        if not self.DISABLED:
            return self.weather_sprites[weather_type]
        return None

    def get_item_sprite(self, item_class: T.Type[items.Item]) -> str:
        """
        Look up what the item sprite resource name is
        """
        if not self.DISABLED:
            return self.item_sprites[item_class]
        return None
