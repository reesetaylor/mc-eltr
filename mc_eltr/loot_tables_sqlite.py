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

        # delete old db
        if os.path.exists("sql/loot_tables.db"):
            os.remove("sql/loot_tables.db")

        self.conn = sqlite3.connect("sql/loot_tables.db")
        # return lists instead of lists of tuples
        self.conn.row_factory = lambda cursor, row: row[0]

        # create tables
        self.conn.executescript(
            """
            CREATE TABLE blocks(
                block PRIMARY KEY,
                type,
                area,
                fname text NOT NULL
            );

            CREATE TABLE drops(
                rowid integer PRIMARY KEY,
                block text NOT NULL,
                item text NOT NULL,
                FOREIGN KEY (block) REFERENCES blocks(block)
            );

            CREATE TABLE recipes(
                rowid integer PRIMARY KEY,
                item text NOT NULL,
                needs text NOT NULL
            );

            CREATE TABLE assigned(
                rowid integer PRIMARY KEY,
                block text NOT NULL,
                loot text NOT NULL,
                FOREIGN KEY (block) REFERENCES blocks(block),
                FOREIGN KEY (loot) REFERENCES block(block)
            );
        """
        )

        # convert the loot_tables subfolders into full paths
        # defined as a member for use in scan loot tables
        self.loot_tables_folder = Path("data/minecraft/loot_tables")
        loot_tables_subfolders = tuple(
            list((self.loot_tables_folder / sf).as_posix() for sf in randomize_loot)
        )

        # sheep folder for aliasing sheep filenames
        self.sheep_folder = Path("data/minecraft/loot_tables/entities/sheep")

        # recipes
        recipes_folder = Path("data/minecraft/recipes").as_posix()
        recipes_files = []

        # tags
        tags_folder = Path("data/minecraft/tags/items").as_posix()
        # needs to be accessed from add_item in skyblock
        self.tags = {}

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
            elif file_path.startswith(tags_folder):
                tag = json.load(jar.open(file_path))
                tag_name = Path(file_path).stem
                self.tags[tag_name] = [t.split(":")[-1] for t in tag["values"]]

            elif file_path.startswith(recipes_folder):
                recipes_files.append(Path(file_path).name)

        # scan recipes in a second loop once tags are scanned
        for f in recipes_files:
            # open file contents as json
            file_path = (recipes_folder / Path(f)).as_posix()
            recipe = json.load(jar.open(file_path))
            # write recipe to db
            self.scan_recipe(recipe)

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
        unreliable_drops = []
        for ud in obtainment_data["unreliable_drops"]:
            unreliable_drops.append((ud[0], ud[1]))
        
        self.conn.executemany("DELETE FROM drops WHERE block=? AND item=?", unreliable_drops)

        self.conn.commit()
    
    # convenience function to strip namespace
    def sns(self, name):
        return name.split(':')[-1]
    
    def scan_loot_table(self, block, loot_table):
        # there are a lot of conditions that affect what a block/entity drops
        # as long as it does pertain to any of the critical items
        # i.e. obsidian, flint and steel, or eyes of ender
        # 100% accurate information is not necessary
        sns = self.sns

        drop_values = []

        def scan_entry(block, e):
            if e["type"].endswith("item"):
                # prevent duplicates
                if not (block, sns(e["name"])) in drop_values:
                    drop_values.append((block, sns(e["name"])))
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

    def scan_recipe(self, recipe):
        # again, only really care about anything that could affect critical items
        sns = self.sns
        recipe_values = []
        if recipe["type"] == "minecraft:crafting_shaped":
            item = sns(recipe["result"]["item"])
            for i in recipe["key"]:
                for j in i:
                    if "item" in j:
                        recipe_values.append((item, sns(j["item"])))
                    elif "tag" in j:
                        recipe_values.append((item, sns(j["tag"])))
        elif recipe["type"] == "minecraft:crafting_shapeless":
            item = sns(recipe["result"]["item"])
            for i in recipe["ingredients"]:
                if "item" in i:
                    recipe_values.append((item, sns(i["item"])))
                elif "tag" in i:
                    recipe_values.append((item, sns(i["tag"])))
        elif recipe["type"] == "minecraft:smelting":
            item = sns(recipe["result"]["item"])
            if "item" in recipe["ingredient"]:
                recipe_values.append((item, sns(i["item"])))
            elif "tag" in recipe["ingredient"]:
                recipe_values.append((item, sns(i["tag"])))
        self.conn.executemany("INSERT INTO recipes(item,needs) VALUES (?,?)", recipe_values)