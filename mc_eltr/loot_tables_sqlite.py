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
        self.loot_tables_folder = Path("data/minecraft/loot_tables/entities/sheep")

        recipes_folder = Path("data/minecraft/recipes").as_posix()

        # initialize the database
        self.conn = sqlite3.connect("sql/loot_tables.db")

        conn = self.conn

        # read sqlite scripts
        create_tables, insert_lt_files, insert_drop = map(
            lambda s: Path(s).read_text(),
            [
                "sql/create_tables.sqlite",
                "sql/insert_lt_files.sqlite",
                "sql/insert_drop.sqlite",
            ],
        )

        conn.executescript(create_tables)

        # write the loot tables and recipes
        for file_path in jar.namelist():
            if file_path.startswith(loot_tables_subfolders):
                # short name e.g. "dirt"
                block = Path(file_path).stem
                # open file contents as json
                file_contents = json.load(jar.open(file_path))
                # type of item (block, entity, fishing, gift)
                type_ = file_contents["type"].split(":")[-1]
                # scans what items are dropped from this block's loot table
                drops = self.scan_loot_table(file_contents)
                # convert file contents back into a string
                file_contents = json.dumps(file_contents)
                # insert file information for the block
                conn.execute(insert_lt_files, (block, file_path, type_, file_contents))
                # insert block's loot table drops if it has any
                for drop in drops:
                    conn.execute(insert_drop, (block, drop))
            elif file_path.startswith(recipes_folder):
                # write recipe to db
                pass
        
        # all done with the .jar, close it
        jar.close()

        # add information about blocks that are in the end and the nether

        conn.commit()

    def scan_loot_table(self, loot_table):
        # there are a lot of conditions that affect what drops
        # as long as they don't affect any of the critical items
        # i.e. obsidian, flint and steel, or eyes of ender
        # 100% accurate information is not necessary
        drops = []
        # check that block/entity has drops
        if not "pools" in loot_table:
            return drops
        for p in loot_table["pools"]:
            for e in p["entries"]:
                if e["type"].endswith("item"):
                    drops.append(e["name"].split(":")[-1])
                elif e["type"] == "minecraft:alternatives":
                    for c in e["children"]:
                        if c["type"] == "minecraft:item":
                            drops.append(c["name"])
                elif e["type"] == "minecraft:loot_table":
                    # recursively read the referenced loot_table
                    # performance takes a hit, but only the colored sheep and a few others have this
                    # I think I also stopped caring about performance when I added SQLite
                    drops.append(
                        self.scan_loot_table(
                            json.loads(
                                (self.loot_tables_folder / Path(e["name"]).read_text())
                            )
                        )
                    )

        return drops

    def scan_recipe(self):
        pass