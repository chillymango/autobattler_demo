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

    def get_normie_sprite(self, pokemon_name):
        if not self.disabled:
            return self.normie_sprites[pokemon_name]
        return None

    def get_shiny_sprite(self, pokemon_name):
        if not self.disabled:
            return self.shiny_sprites[pokemon_name]
        return None
