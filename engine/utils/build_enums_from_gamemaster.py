"""
Read the PoGo gamemaster JSON and generate an enum of all Pokemon.

The enum order is just the order in which we read Pokemon in.

NOTE: this is NOT expected to be backward compatible.
"""
import json
import typing as T

GAMEMASTER_PATH = "battle_engine\\src\\data\\gamemaster.json"
OUTPUT_PATH = "engine\\models\\enums.py"


def main():
    with open(GAMEMASTER_PATH, 'r') as gamemaster_json:
        gamemaster = json.load(gamemaster_json)

    # get all pokemon
    pokemon_dict = gamemaster['pokemon']
    pokemon_names: T.List[str] = []
    pokemon_ids: T.List[str] = []
    for pokemon in pokemon_dict:
        pokemon_names.append(pokemon['speciesName'])
        pokemon_ids.append(pokemon['speciesId'])

    types = list(gamemaster['types'].keys())

    # get moves
    moves_list = gamemaster['moves']
    moves = [move['moveId'] for move in moves_list]

    # write out
    with open(OUTPUT_PATH, 'w+') as output_enums_file:
        output_enums_file.write("## AUTOGENERATED ENUMS FILE ##\n\n\n")
        output_enums_file.write("from enum import Enum\n\n")

        output_enums_file.write("class PokemonId(Enum):\n")
        for idx, _id in enumerate(pokemon_ids):
            output_enums_file.write("    {} = {}\n".format(_id, idx))
        output_enums_file.write("\n\n")

        output_enums_file.write("class PokemonName(Enum):\n")
        seen = set()
        for idx, name in enumerate(pokemon_names):
            if name in seen:
                continue
            seen.add(name)
            output_enums_file.write("    {} = {}\n".format(
                name.replace(' ', '_').replace('(', '').replace(')', '')
                    .replace('-', '_').replace('\'', '').replace('.', '_'), idx)
            )
        output_enums_file.write("\n\n")

        output_enums_file.write("class Move(Enum):\n")
        for idx, move_id in enumerate(moves):
            output_enums_file.write("    {} = {}\n".format(move_id, idx))
        # include a `none` move
        output_enums_file.write("    none = {}".format(idx + 1))
        output_enums_file.write("\n\n")

        output_enums_file.write("class PokemonType(Enum):\n")
        for idx, type_ in enumerate(types):
            output_enums_file.write("    {} = {}\n".format(type_, idx))
        output_enums_file.write("\n")


if __name__ == "__main__":
    main()
