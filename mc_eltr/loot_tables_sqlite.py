import os
import sys
import zipfile
from pathlib import Path
import json
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
        # set information about special blocks
        self.s_blocks = self.obt_data["special_blocks"]
        # jar path
        self.jar_path = jar_path
        # load settings for which loot tables to randomize
        randomize_loot = settings["randomize_loot"]
        # output folder
        self.output_folder = Path(settings["output_folder"])

        # open the .jar file
        # TODO: validate the .jar file in randomize
        jar = zipfile.ZipFile(self.jar_path)

        self.conn = sqlite3.connect(":memory:")
        # return nested lists instead of lists of tuples
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
                # block is the short name e.g. "dirt"
                block = Path(file_path).stem
                # check if this block is in the sheep folder
                if Path(file_path).parent.name == "sheep":
                    block = "sheep_" + block
                # open file contents as json
                loot_table = json.load(jar.open(file_path))
                # type of block (block, entity, fishing, gift)
                type_ = loot_table["type"].split(":")[-1]
                # scans what items are dropped from this block's loot table
                drop_values = self.scan_loot_table(block, loot_table)
                # we only care about this block if it has drops
                if drop_values:
                    # insert file information for the block
                    self.conn.execute(
                        "INSERT INTO blocks(block,type,area,fname) VALUES(?,?,?,?)",
                        (block, type_, "ow", file_path),
                    )
                    # insert block's loot table drops
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
        area_values = []
        for a in self.s_blocks:
            for b in self.s_blocks[a]:
                area_values.append((a, b))

        self.conn.executemany("UPDATE blocks SET area = ? WHERE block = ?", area_values)

        # remove unreliable drops from the drops table as they pertain to critical items
        # zombies DO NOT reliably drop iron
        unreliable_drops = []
        for ud in obtainment_data["unreliable_drops"]:
            unreliable_drops.append((ud[0], ud[1]))

        self.conn.executemany(
            "DELETE FROM drops WHERE block=? AND item=?", unreliable_drops
        )

        self.conn.commit()

    # convenience function to strip namespace
    def sns(self, name):
        return name.split(":")[-1]

    def scan_loot_table(self, block, loot_table):
        # there are a lot of conditions that affect what a block/entity drops
        # as long as it does not pertain to any of the critical items
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
                if "item" in recipe["key"][i]:
                        recipe_values.append((item, sns(recipe["key"][i]["item"])))
                elif "tag" in recipe["key"][i]:
                        recipe_values.append((item, sns(recipe["key"][i]["tag"])))

        elif recipe["type"] == "minecraft:crafting_shapeless":
            item = sns(recipe["result"]["item"])
            for i in recipe["ingredients"]:
                if "item" in i:
                    recipe_values.append((item, sns(i["item"])))
                elif "tag" in i:
                    recipe_values.append((item, sns(i["tag"])))

        elif recipe["type"] == "minecraft:smelting":
            item = sns(recipe["result"])
            i = recipe["ingredient"]
            if "item" in i:
                recipe_values.append((item, sns(i["item"])))
            elif "tag" in i:
                recipe_values.append((item, sns(i["tag"])))

        self.conn.executemany(
            "INSERT INTO recipes(item,needs) VALUES (?,?)", recipe_values
        )

    def write_to_datapack(self, dp_name, dp_description, dp_reset_msg, dp_filename):
        # buffer the datapack in memory before writing it to the disk
        buffer = io.BytesIO()
        datapack = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)

        # change output formatting
        self.conn.row_factory = lambda cursor, row: [row[0], row[1]]

        # get a list of destination filenames to write to and source filenames to write from
        filenames = self.conn.execute(
            """
            SELECT src.fname, dest.fname
            FROM assigned
            INNER JOIN blocks AS src
            ON assigned.loot = src.block
            INNER JOIN blocks AS dest
            ON assigned.block = dest.block
            """
        ).fetchall()

        self.conn.row_factory = lambda cursor, row: row[0]

        # open the jar
        jar = zipfile.ZipFile(self.jar_path)

        # copy the contents of every source file in the .jar to its destination file in the datapack
        for src_dest in filenames:
            src, dest = src_dest
            datapack.writestr(dest, jar.open(src).read())

        jar.close()

        # add metadata
        datapack.writestr(
            "pack.mcmeta",
            json.dumps({"pack": {"pack_format": 1, "description": dp_description}}, indent=4),
        )

        datapack.writestr(
            "data/minecraft/tags/functions/load.json",
            json.dumps({"values": [f"{dp_name}:reset"]}),
        )

        datapack.writestr(
            f"data/{dp_name}/functions/reset.mcfunction", dp_reset_msg,
        )

        # close the datapack
        datapack.close()

        # write the datapack to a file on the disk
        datapack_file = open((self.output_folder / dp_filename), "wb")
        datapack_file.write(buffer.getvalue())
        datapack_file.close()

    def write_cheatsheet(self, fname):
        #change output formatting
        self.conn.row_factory = lambda cursor, row: [row[0], row[1]]

        # retrieve the assigned table
        assigned = self.conn.execute(
            """
            SELECT block, loot
            FROM assigned 
            """
        ).fetchall()

        self.conn.row_factory = lambda cursor, row: row[0]

        # determine the longest name of a block for formatting
        longest_name = 0

        for row in assigned:
            for i in range(2):
                row[i].replace("_", " ")
            block, loot = row
            l = len(block)
            if l > longest_name:
                longest_name = l
        
        # width of cheat sheet columns
        width = longest_name + 2
        with open((self.output_folder / fname), 'w') as cheatsheet:
            for row in assigned:
                cheatsheet.write("".join(word.ljust(width) for word in row) + "\n")


