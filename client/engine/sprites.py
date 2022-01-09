"""
Load Sprites for Pokemon
"""
import os
from collections import defaultdict

from engine.base import Component


class SpriteManager(Component):

    ASSETS_DIR = 'qtassets'

    DISABLED = False

    def initialize(self):
        super().initialize()
        # load normie sprites
        self.normie_sprites = defaultdict(lambda: None)
        self.normie_base = os.path.join(self.ASSETS_DIR, 'sprites', 'normie')
        for filename in os.listdir(self.normie_base):
            pokemon, ext = filename.split('.')
            self.normie_sprites[pokemon] = os.path.join(self.normie_base, filename)

        # load shiny sprites
        self.shiny_sprites = defaultdict(lambda: None)
        self.shiny_base = os.path.join(self.ASSETS_DIR, 'sprites', 'shiny')
        for filename in os.listdir(self.shiny_base):
            pokemon, ext = filename.split('.')
            self.shiny_sprites[pokemon] = os.path.join(self.shiny_base, filename)

    def get_normie_sprite(self, pokemon_name):
        if not self.disabled:
            return self.normie_sprites[pokemon_name]
        return None

    def get_shiny_sprite(self, pokemon_name):
        if not self.disabled:
            return self.shiny_sprites[pokemon_name]
        return None
