"""
Weather Manager
"""
import typing as T
from collections import defaultdict
from random import sample

from engine.base import Component
from engine.models.enums import PokemonType
from engine.models.weather import WeatherType
import random

class WeatherManager(Component):
    """
    Manages the weather conditions
    """

    def initialize(self):
        super().initialize()

        # NOTE(albert): this probably won't change, and won't need to be configured, but should
        # still live in a config file
        self.weather_bonuses: T.Dict[WeatherType, T.List[PokemonType]] = defaultdict(lambda: [])
        self.weather_bonuses.update({
            WeatherType.SNOWY: [PokemonType.ice, PokemonType.steel],
            WeatherType.FOGGY: [PokemonType.dark, PokemonType.ghost],
            WeatherType.WINDY: [PokemonType.flying, PokemonType.dragon, PokemonType.psychic],
            WeatherType.PARTLY_CLOUDY: [PokemonType.normal, PokemonType.rock],
            WeatherType.RAINY: [PokemonType.water, PokemonType.electric, PokemonType.bug],
            WeatherType.CLEAR: [PokemonType.grass, PokemonType.fire, PokemonType.ground],
            WeatherType.OVERCAST: [PokemonType.fairy, PokemonType.fighting, PokemonType.poison]
        })
        self.weather_forecast = [x for x in WeatherType if x is not WeatherType.NONE] * 10
        random.shuffle(self.weather_forecast)

    def turn_setup(self):
        """
        Weather changes on turn setup
        """
        # randomly get a new weather type
        weather = self.weather_forecast[self.state.turn_number]
        self.change_weather(weather)


#    def get_random_weather(self):
#        weather_options = [x for x in WeatherType if x is not WeatherType.NONE]
#        return sample(weather_options, 1)[0]

    def change_weather(self, weather: WeatherType):
        """
        Change the weather
        """
        print(f'Setting the weather to {weather.name}')
        self.state.weather = weather
        # TODO: set battle markers or something like that here...
