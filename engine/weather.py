"""
Weather Manager
"""
from random import sample
from engine.base import Component
from engine.models.weather import WeatherType


class WeatherManager(Component):
    """
    Manages the weather conditions
    """

    def initialize(self):
        super().initialize()
        # i'm sure something goes here eventually

    def turn_setup(self):
        """
        Weather changes on turn setup
        """
        # randomly get a new weather type
        weather = self.get_random_weather()
        self.change_weather(weather)

    def get_random_weather(self):
        weather_options = [x for x in WeatherType]
        return sample(weather_options, 1)[0]

    def change_weather(self, weather: WeatherType):
        """
        Change the weather
        """
        print(f'Setting the weather to {weather.name}')
        self.state.weather = weather
        # TODO: set battle markers or something like that here...
