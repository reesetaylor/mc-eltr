#!/usr/bin/python3
import argparse
import json
import sys
import os
from pathlib import Path
import random
import time

from loot_tables import LootTables

# find the path of the Minecraft folder
def find_mc_folder(jar_not_found):
    # attempt to set the location of minecraft .jar
    # windows/cygwin
    if sys.platform == "win32":
        mc_folder = Path(os.getenv("APPDATA")) / ".minecraft"
    # mac
    elif sys.platform == "darwin":
        mc_folder = Path.home() / "Library" / "Application Support" / "minecraft"
    # linux/other
    else:
        print(
            "Automatically finding minecraft .jar is only implemented for windows and mac.\n"
            + jar_not_found
        )
        exit()
    if not mc_folder.exists():
        print(
            "Did not find Minecraft folder at the expected location ("
            + str(mc_folder)
            + ")\n"
            + jar_not_found
        )
        exit()
    else:
        return mc_folder


# find the path of the Minecraft .jar
def find_mc_jar(args):
    # message to print if automatically finding the jar fails
    jar_not_found = (
        "Please specify the location of the minecraft .jar using the -j option e.g.\n"
        + args.prog
        + " -j "
        + str(Path.home())
        + "/.minecraft/versions/1.5.2/1.5.2.jar"
    )

    mc_jar = None

    if args.jar is not None:
        if not Path(args.jar).is_file:
            print("Could not find the specifified minecraft .jar file " + args.jar)
        else:
            mc_jar = Path(args.jar)
    else:
        # the minecraft folder
        mc_folder = find_mc_folder(jar_not_found)
        mc_jar = next((mc_folder / "versions/").glob("*/*.jar"))

    if mc_jar is None:
        print("Unable to find the minecraft .jar\n" + jar_not_found)
    else:
        print("Found Minecraft version " + mc_jar.stem)
        return mc_jar

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description="Minecraft enhanced loot table randomizer")
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="Integer seed for the randomizer. Default is to use the current timestamp.",
        default=time.time(),
    )
    parser.add_argument(
        "-j",
        "--jar",
        help="Specify the location of the minecraft .jar to generate the datapack for. Default is to look in the normal location on Windows and Mac.",
    )

    args = parser.parse_args()

    # import settings

    settings_path = "randomizerSettings.json"

    # open the settings file
    with open(settings_path, 'r') as f:
        settings = json.load(f)

    # create the desired output folder if it doesn't exist
    output_folder = Path(settings["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    # set datapack information
    dp_name = "random_loot_" + str(args.seed)
    dp_filename = output_folder / (dp_name + ".zip")
    dp_description = "Loot table randomizer, Seed: " + str(args.seed)
    dp_reset_msg = 'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, based on SethBling/Fasguy\'s script","color":"green"}]'

    # TODO: add recipe randomization
    # set randomization for the chosen loot tables
    randomize_loot = settings["randomize_loot"]

    # set location of Minecraft .jar
    jar_path = find_mc_jar(args)

    print("Generating datapack...")
    
    # seed RNG
    random.seed(args.seed)

    # create an empty dictionary
    tables = LootTables(jar_path, randomize_loot)

    # each block starts out unpaired
    unpaired_blocks = tables.unpaired_blocks()

    # we assign each one a random loot table that is also unpaired
    for block in unpaired_blocks:
        # randomly choose loot that has not been paired yet
        loot = random.choice(tuple(tables.unpaired_loot()))
        # pair the block with loot
        tables.pair_block_loot(block, loot)

    # write the loot tables to a datapack
    tables.write_to_datapack(dp_name, dp_filename, dp_description, dp_reset_msg)

    # all done
    print("Created datapack " + str(dp_filename) + ". Enjoy!")

def randomize():


if __name__ == "__main__":
    main()