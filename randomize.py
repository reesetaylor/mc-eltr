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
    help="Integer seed for the randomizer. Defaults to current timestamp.",
    default=time.time(),
)
parser.add_argument(
    "-j",
    "--jar",
    help="Specify the location of the minecraft.jar to generate the datapack from.",
)

args = parser.parse_args()

# message to print if automatically finding the jar fails
jarNotFound = (
    "Please specify the location of the minecraft.jar using the -j option e.g.\n"
    + parser.prog
    + " -j "
    + str(Path.home())
    + "/.minecraft/bin/minecraft.jar"
)

# get the path of the Minecraft folder
def getMCFolder():
    # attempt to set the location of minecraft.jar
    # windows
    if sys.platform == "win32":
        MCFolder = Path(os.getenv("APPDATA")) / ".minecraft"
    # mac
    elif sys.platform == "darwin":
        MCFolder = Path.home() / "Library" / "Application Support" / "minecraft"
        pass
    # linux/other
    else:
        print(
            "Automatically finding minecraft.jar is only implemented for windows and mac.\n"
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


MCFolder = getMCFolder()

# get a zip file object of minecraft.jar
def getMCJar():
    if args.jar is not None:
        try:
            MCJar = zipfile.ZipFile(args.jar)
        except FileNotFoundError:
            print("Cannot find the specifified minecraft.jar file")
            exit()
        return MCJar
    else:
        # most up-to-date version is sorted to the start of the list
        versions = sorted(os.listdir(MCFolder / "versions"))
        version = versions[0]
        print("Found Minecraft version " + version)
        MCJar = zipfile.ZipFile(MCFolder / "versions" / version / (version + ".jar"))
        return MCJar


# reads the loot tables from the .jar into memory
def readLootTables(zipFile):
    # a dictionary that stores the contents of each loot table with its filename as the key
    vanillaLootTables = {}
    # a just-for-fun variable
    blockCount = 0
    for filename in zipFile.namelist():
        if filename.startswith(zipPath):
            contents = zipFile.open(filename).read()
            vanillaLootTables[Path(filename).name] = contents
            blockCount += 1
    zipFile.close()
    # loot tables that remain to be randomized which at the start is all of them
    remainingLootTables = list(vanillaLootTables.keys())
    print("Randomizing " + str(blockCount) + " blocks")
    return (vanillaLootTables, remainingLootTables)


# assign a lootTable to a filename in the datapack
def writeLootTable(lootTable, filename):
    # get the loot table that will be written to the filename
    lootTable = vanillaLootTables[lootTable]
    # write it to the in-memory datapack zip
    datapack.writestr((zipPath + filename), lootTable)


# the minecraft.jar file
MCJar = getMCJar()
# location of the loot tables inside the .jar
zipPath = "data/minecraft/loot_tables/blocks"
(vanillaLootTables, remainingLootTables) = readLootTables(MCJar)

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
    'tellraw @a ["",{"text":"Loot table randomizer by AtticusTG and vpcuitis, based on the original script by SethBling","color":"blue"}]',
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
print("Enjoy!")

