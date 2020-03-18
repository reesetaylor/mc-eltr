#!/usr/bin/python3
import argparse
import json
import time
from pathlib import Path

from find_jar import find_jar
import no_logic
from no_logic import NoLogic
import skyblock
from skyblock import Skyblock

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

    # load the settings file
    
    settings = json.loads(Path("settings.json").read_text())

    # create the desired output folder if it doesn't exist
    output_folder = Path(settings["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    # set the seed
    seed = args.seed

    # set datapack information
    use_randomizer = "skyblock"
    dp_name = f"random_loot_{use_randomizer}_{seed}"
    dp_filename = output_folder / f"{dp_name}.zip"
    dp_description = f"Loot table randomizer, Seed: {seed}"
    dp_reset_msg = 'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, based on SethBling/Fasguy\'s script","color":"green"}]'

    # set location of Minecraft .jar
    jar, version = find_jar(args, parser.prog)

    print(f"Found Minecraft version {version}")

    print("Generating datapack...")

    # TODO: add recipe randomization
    # call the randomizer
    if(use_randomizer == "skyblock"):
        # item obtainment data for use with skyblock randomizer
        obtainment_data = json.loads(Path("obtainment.json").read_text())
        # player starts with unlimited cobblestone
        randomized_tables = Skyblock(jar, settings, obtainment_data, "dirt").randomize(seed)
    else:
        randomized_tables = NoLogic(jar, settings, obtainment_data).randomize(seed)

    # write the loot tables to a datapack
    # randomized_tables.write_to_datapack(dp_name, dp_description, dp_reset_msg, dp_filename)

    # write the cheatsheet
    # randomized_tables.dump_cheatsheet(output_folder / ("cheatsheet_" + str(seed)))

    # all done
    # print(f"Created datapack {dp_filename}. Enjoy!")