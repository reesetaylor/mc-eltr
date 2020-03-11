#!/usr/bin/python3
import argparse
import json
import time
from pathlib import Path

from find_jar import find_jar
from loot_tables import LootTables
import randomizers

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description="Minecraft enhanced loot table randomizer")
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="Integer seed for the randomizer. Default is to use the current timestamp.",
        default=int(str(time.time()).replace(".",""))
    )
    parser.add_argument(
        "-j",
        "--jar",
        help="Specify the location of the minecraft .jar to generate the datapack for. Default is to look in the normal location on Windows and Mac.",
    )

    args = parser.parse_args()

    # import settings

    settings_path = "settings.json"

    # open the settings file
    with open(settings_path, 'r') as f:
        settings = json.load(f)

    # create the desired output folder if it doesn't exist
    output_folder = Path(settings["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    # set the seed
    seed = args.seed

    # set datapack information
    use_randomizer = "no_logic"
    dp_name = "random_loot_" + use_randomizer + "_" + str(seed)
    dp_filename = output_folder / (dp_name + ".zip")
    dp_description = "Loot table randomizer, Seed: " + str(seed)
    dp_reset_msg = 'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, based on SethBling/Fasguy\'s script","color":"green"}]'

    # set location of Minecraft .jar
    jar = find_jar(args, parser.prog)

    # set randomization for the chosen loot tables
    randomize_loot = settings["randomize_loot"]

    print("Generating datapack...")

    # initialize a table from the loot tables in .jar
    initial_tables = LootTables(jar, randomize_loot)

    # TODO: add recipe randomization
    # call the randomizer
    randomized_tables = randomizers.no_logic(initial_tables, seed)

    # write the loot tables to a datapack
    randomized_tables.write_to_datapack(dp_name, dp_description, dp_reset_msg, dp_filename)

    # write the cheatsheet
    randomized_tables.dump_cheatsheet(output_folder / ("cheatsheet_" + str(seed)))

    # all done
    print("Created datapack " + str(dp_filename) + ". Enjoy!")