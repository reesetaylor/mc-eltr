import os
import sys
import zipfile
from pathlib import Path
import json
from tabulate import tabulate
import io
import sqlite3

# wrapper around sqlite database
class LootTables:
    original_pairings = dict()
    original_blocks = set()

    # TODO: also gather recipes in a Recipes object for use with obtainability
    def __init__(self, jar_path, settings, obtainment_data):
        # set settings as a member for children to use
        self.settings = settings
        # set obtainment data as a memember for children to use
        self.obt_data = obtainment_data
        # load settings for which loot tables to randomize
        randomize_loot = settings["randomize_loot"]

        # open the .jar file
        try:
            jar = zipfile.ZipFile(jar_path)
        except FileNotFoundError:
            print("Could not find the minecraft .jar file " + str(jar_path))
            exit()

        # convert the loot_tables subfolders into full paths
        # defined as a member for use in scan loot tables
        self.loot_tables_folder = Path("data/minecraft/loot_tables")
        loot_tables_subfolders = tuple(
            list((self.loot_tables_folder / sf).as_posix() for sf in randomize_loot)
        )

        # sheep folder for aliasing sheep filenames
        self.sheep_folder = Path("data/minecraft/loot_tables/entities/sheep")

        recipes_folder = Path("data/minecraft/recipes").as_posix()

        # initialize the database
        if os.path.exists("sql/loot_tables.db"):
            os.remove("sql/loot_tables.db")

        self.conn = sqlite3.connect("sql/loot_tables.db")

        # read sqlite scripts
        self.scripts = {}
        for script in Path("sql/").glob("*.sqlite"):
            self.scripts[Path(script).stem] = Path(script).read_text()

        self.conn.executescript(self.scripts["create_tables"])

        # write the loot tables and recipes
        for file_path in jar.namelist():
            if file_path.startswith(loot_tables_subfolders):
                # short name e.g. "dirt"
                block = Path(file_path).stem
                # open file contents as json
                loot_table = json.load(jar.open(file_path))
                # type of block (block, entity, fishing, gift)
                type_ = loot_table["type"].split(":")[-1]
                # scans what items are dropped from this block's loot table
                drop_values = self.scan_loot_table(block, loot_table)
                # insert file information for the block
                self.conn.execute(
                    "INSERT INTO blocks(block,type,area,fname) VALUES(?,?,?,?)",
                    (block, type_, "ow", file_path),
                )
                # insert block's loot table drops if it has any
                self.conn.executemany(
                    "INSERT INTO drops(block,item) VALUES (?,?)", drop_values
                )
            elif file_path.startswith(recipes_folder):
                # write recipe to db
                pass

        # close the .jar until we need it again to write the datapack
        jar.close()

        # add information to blocks/entities only found in the nether or end
        s_blocks = self.obt_data["special_blocks"]
        area_values = []
        for a in s_blocks:
            for b in s_blocks[a]:
                area_values.append((a, b))

        self.conn.executemany("UPDATE blocks SET area = ? WHERE block = ?", area_values)

        # remove unreliable drops from the drops table as they pertain to critical items
        # zombies DO NOT reliably drop iron

        self.conn.commit()

    # TODO: gravel doesn't detect as dropping flint, which is necessary to ensure flintandsteel can be crafted
    def scan_loot_table(self, block, loot_table):
        # there are a lot of conditions that affect what a block/entity drops
        # as long as it does pertain to any of the critical items
        # i.e. obsidian, flint and steel, or eyes of ender
        # 100% accurate information is not necessary

        drop_values = []

        def scan_entry(block, e):
            if e["type"].endswith("item"):
                drop_values.append((block, e["name"].split(":")[-1]))
            elif e["type"] == "minecraft:alternatives":
                for c in e["children"]:
                    scan_entry(block, c)
            elif e["type"] == "minecraft:loot_table":
                pass

        # check that block/entity has drops
        if not "pools" in loot_table:
            return drop_values
        for p in loot_table["pools"]:
            for e in p["entries"]:
                scan_entry(block, e)

        return drop_values

    def scan_recipe(self):
        pass
