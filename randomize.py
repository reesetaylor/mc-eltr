#!/usr/bin/python3
import argparse
import io
import json
import sys
import os
from pathlib import Path
import random
import time
import zipfile

# parse arguments
parser = argparse.ArgumentParser(description="Minecraft enhanced loot table randomizer")
parser.add_argument(
    "-s",
    "--seed",
    type=int,
    help="Integer seed for the randomizer. Default is to use current timestamp.",
    default=time.time(),
)
parser.add_argument(
    "-j",
    "--jar",
    help="Specify the location of the minecraft .jar to generate the datapack for. Default is to look in the normal location on Windows and Mac.",
)

parser.add_argument(
    "-r",
    "--randomize",
    help="Specify which loot tables to randomize in a comma-separated list. Use any combination of 'blocks', 'chests', 'entities', 'fishing', and 'gifts' to randomize just those loot tables e.g. "
    + parser.prog
    + " -r blocks,entities,fishing will randomize loot tables of blocks and entities but not chests or villager gifts. Default is to randomize all of the loot tables.",
    default="blocks,chests,entities,fishing,gifts",
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
def getMCJar():
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
        try:
            MCJar = zipfile.ZipFile(args.jar)
        except FileNotFoundError:
            print("Could not find the specifified minecraft .jar file " + args.jar)
            exit()
    else:
        # the minecraft folder
        MCFolder = getMCFolder(jarNotFound)
        for root, folder, files in os.walk(MCFolder / "versions"):
            for filename in files:
                if filename.endswith(".jar"):
                    MCJar = zipfile.ZipFile(Path(root) / filename)
    
    if MCJar is None:
        print("Unable to find the minecraft .jar\n" + jarNotFound)
    else:
        print("Found Minecraft version " + Path(MCJar.filename).stem)
        return MCJar


# determine what folders to read loot tables from in the .jar based on -r argument
# accepts the jarLootTablesFolder as an argument because best practices
def getJarLootTableSubfolders(folder):
    jarLootTablesSubfolders = []

    for subfolder in args.randomize.split(","):
        if subfolder == "gifts":
            jarLootTablesSubfolders.append(folder + "gameplay/hero_of_the_village/")
            jarLootTablesSubfolders.append(folder + "gameplay/cat_morning_gift.json")
        elif subfolder == "fishing":
            # notably does not randomize gameplay/fishing.json. if we did,
            # fishing would most likely just return a set item everytime
            # and some random block would have the loot table of fishing.
            # by leaving fishing.json where it is, the player can get a
            # random "fish" everytime they fish, which seems like more fun.
            jarLootTablesSubfolders.append(folder + "gameplay/fishing/")
        else:
            jarLootTablesSubfolders.append(folder + subfolder)
    return jarLootTablesSubfolders


# detects loot table files when looping through files in .jar
def isLootTableFile(filename, subfolders):
    # check if this file is in one of the folders specified by -r
    return filename.startswith(tuple(subfolders))


# TODO: consolidate loot table operations into a lootTableDict object
# reads the loot tables from the .jar into memory
def readLootTables(zipFile, subfolders):
    # a dictionary that stores the contents of each loot table with its filename as the key
    vanillaLootTables = {}
    # a just-for-fun variable
    lootTableCount = 0
    for filename in zipFile.namelist():
        if isLootTableFile(filename, subfolders):
            contents = zipFile.open(filename).read()
            vanillaLootTables[Path(filename)] = contents
            lootTableCount += 1
    zipFile.close()
    # loot tables that remain to be randomized which at the start is all of them
    remainingLootTables = list(vanillaLootTables.keys())
    print("Randomizing " + str(lootTableCount) + " loot tables.")
    return (vanillaLootTables, remainingLootTables)


# assign a lootTable to a filename in the datapack
def writeLootTable(lootTable, filename):
    # convert Path object to str for writestr
    filename = str(filename)
    # get the loot table that will be written to the filename
    lootTable = vanillaLootTables[lootTable]
    # write it to the in-memory datapack zip
    datapack.writestr(filename, lootTable)
    print(jarLootTablesFolder + filename)


# the minecraft .jar file
MCJar = getMCJar()
exit()
# loot_tables folder location in the .jar
# not a Path object because of complications with filename.startswith
jarLootTablesFolder = "data/minecraft/loot_tables/"
# the subfolders of loot_tables folder in the .jar. controlled with -r
jarLootTablesSubfolders = getJarLootTableSubfolders(jarLootTablesFolder)
print("Looking for loot tables in\n")
print(*jarLootTablesSubfolders, sep="\n")

(vanillaLootTables, remainingLootTables) = readLootTables(
    MCJar, jarLootTablesSubfolders
)

print("Generating datapack...")

# set datapack information
datapack_name = "random_loot_" + str(args.seed)
datapack_filename = datapack_name + ".zip"
datapack_desc = "Loot table randomizer, Seed: " + str(args.seed)

# anything we write to datapack will be saved into dpBytes
dpBytes = io.BytesIO()
datapack = zipfile.ZipFile(dpBytes, "w", zipfile.ZIP_DEFLATED)
# set datapack metadata
datapack.writestr(
    "pack.mcmeta",
    json.dumps({"pack": {"pack_format": 1, "description": datapack_desc}}, indent=4),
)
datapack.writestr(
    "data/minecraft/tags/functions/load.json",
    json.dumps({"values": ["{}:reset".format(datapack_name)]}),
)
datapack.writestr(
    "data/" + datapack_name + "/functions/reset.mcfunction",
    'tellraw @a ["",{"text":"Enhanced loot table randomizer by AtticusTG and vpcuitis, inspired by SethBling/Fasguy\'s script","color":"green"}]',
)

# seed RNG
random.seed(args.seed)

# randomly assign loot tables in the datapack
for filename in vanillaLootTables.keys():
    lootTable = random.choice(remainingLootTables)
    writeLootTable(lootTable, filename)
    remainingLootTables.remove(lootTable)

# clean up
datapack.close()

# write the datapack bytes to a file in the folder
# 'wb' is write mode and binary mode, since we are writing bytes
datapack_file = open(datapack_filename, "wb")
datapack_file.write(dpBytes.getvalue())

# all done
print("Created datapack " + datapack_filename)
if "fishing" in args.randomize.split(","):
    print("Happy fishing!")
else:
    print("Enjoy!")

