#!/usr/bin/python3
import json
import time
from pathlib import Path

from mc_eltr.find_jar import find_jar
from mc_eltr.no_logic import NoLogic

def main():
    # load the settings file
    settings = json.loads(Path("settings.json").read_text())

    # create the desired output folder if it doesn't exist
    output_folder = Path(settings["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    # set the seed
    seed = int(str(time.time()).replace(".",""))

    # set location of Minecraft .jar
    jar = find_jar()

    # set datapack information
    dp_name = f"random_loot_{seed}"
    dp_filename = f"{dp_name}.zip"
    dp_description = f"Loot table randomizer, Seed: {seed}"
    dp_reset_msg = 'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, based on SethBling/Fasguy\'s script","color":"green"}]'

    if jar is None:
        print("whoops, couldn't find the .jar")
        exit()

    
    obtainment_data = json.loads(Path("data/obtainment.json").read_text())
    randomized_tables = NoLogic(jar, settings, obtainment_data).randomize(seed)

    # write the loot tables to a datapack
    randomized_tables.write_to_datapack(dp_name, dp_description, dp_reset_msg, dp_filename)

    # write the cheatsheet if selected
    if settings["cheatsheet"]:
        randomized_tables.write_cheatsheet((f"cheatsheet_{str(seed)}.txt"))

    # all done
    print(f"Created datapack {dp_filename}. Enjoy!")