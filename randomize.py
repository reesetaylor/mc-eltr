#!/usr/bin/python3
import argparse
import json
import sys
import os
from pathlib import Path
import random
import time

from lootTables import LootTables

# parse arguments
parser = argparse.ArgumentParser(description="Minecraft enhanced loot table randomizer")
parser.add_argument(
    "-s",
    "--seed",
    type=int,
    help="Integer seed for the randomizer. Default is to use the last 4 places of the current timestamp.",
    default=time.time(),
)
parser.add_argument(
    "-j",
    "--jar",
    help="Specify the location of the minecraft .jar to generate the datapack for. Default is to look in the normal location on Windows and Mac.",
)

args = parser.parse_args()

# get the path of the Minecraft folder
def getMCFolder(jarNotFound):
    # attempt to set the location of minecraft .jar
    # windows/cygwin
    if sys.platform == "win32":
        MCFolder = Path(os.getenv("APPDATA")) / ".minecraft"
    # mac
    elif sys.platform == "darwin":
        MCFolder = Path.home() / "Library" / "Application Support" / "minecraft"
    # linux/other
    else:
        print(
            "Automatically finding minecraft .jar is only implemented for windows and mac.\n"
            + jarNotFound
        )
        exit()
    if not MCFolder.exists():
        print(
            "Did not find Minecraft folder at the expected location ("
            + str(MCFolder)
            + ")\n"
            + jarNotFound
        )
        exit()
    else:
        return MCFolder


# get a zip file object of the minecraft .jar
def getMCJarPath():
    # message to print if automatically finding the jar fails
    jarNotFound = (
        "Please specify the location of the minecraft .jar using the -j option e.g.\n"
        + parser.prog
        + " -j "
        + str(Path.home())
        + "/.minecraft/versions/1.5.2/1.5.2.jar"
    )

    MCJar = None

    if args.jar is not None:
        if not Path(args.jar).is_file:
            print("Could not find the specifified minecraft .jar file " + args.jar)
        else:
            MCJar = Path(args.jar)
    else:
        # the minecraft folder
        MCFolder = getMCFolder(jarNotFound)
        MCJar = next((MCFolder / "versions/").glob("*/*.jar"))

    if MCJar is None:
        print("Unable to find the minecraft .jar\n" + jarNotFound)
    else:
        print("Found Minecraft version " + MCJar.stem)
        return MCJar


# the location of the minecraft .jar
MCJarPath = getMCJarPath()
vanillaLootTables = LootTables().initFromJar(MCJarPath)
vanillaLootTables.dumpCheatSheet("cheatsheet_" + str(args.seed))

print("Generating datapack...")

randomizedLootTables = vanillaLootTables.copy().randomize(args.seed)

# set datapack information
dpName = "random_loot_" + str(args.seed)
dpFname = dpName + ".zip"
dpDesc = "Loot table randomizer, Seed: " + str(args.seed)
dpResetMsg = 'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, based on SethBling/Fasguy\'s script","color":"green"}]'

randomizedLootTables.writeToDatapack(dpName, dpDesc, dpResetMsg, dpFname)

# all done
print("Created datapack " + dpFname + ". Enjoy!")

