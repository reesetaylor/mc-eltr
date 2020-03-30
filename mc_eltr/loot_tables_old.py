from collections import UserDict
import zipfile
from pathlib import Path
import json
from tabulate import tabulate
import io

# extend dict with convenience functions for loot tables
class LootTables(UserDict):
    original_pairings = dict()
    original_blocks = set()
    
    # TODO: also gather recipes in a Recipes object for use with attainability
    # accepts a path to the .jar and initializes loot tables from the chosen subfolders
    def __init__(self, jar_path: Path = None, randomize_loot = {}):
        super().__init__(self)

        if jar_path is not None:
            loot_tables_folder = "data/minecraft/loot_tables"
            loot_tables_subfolders = tuple(
                list((Path(loot_tables_folder) / sf).as_posix() for sf in randomize_loot)
            )
            
            try:
                jar = zipfile.ZipFile(jar_path)
            except FileNotFoundError:
                print("Could not find the minecraft .jar file " + str(jar_path))
                exit()

            for file_path in jar.namelist():
                if file_path.startswith(loot_tables_subfolders):
                    # short name e.g. "dirt"
                    block = Path(file_path).stem
                    loot = jar.open(file_path).read()
                    # if we want to modify the json, we would do so here
                    # record the file this loot table originally goes with
                    self.original_pairings[block] = {"filename": file_path, "loot_table": loot}
            
            jar.close()
            
            self.original_blocks = set(self.original_pairings.keys())
            self.paired_loot_ = []

    def paired_blocks(self):
        return set(self.keys())

    def unpaired_blocks(self):
        return self.original_blocks - self.paired_blocks()

    def paired_loot(self):
        return set(self.paired_loot_)

    def unpaired_loot(self):
        return self.original_blocks - self.paired_loot()

    # TODO: validation
    # TODO: weigh SQLite as an option for filtering
    def pair_block_loot(self, block, loot):
        self[block] = loot
        self.paired_loot_.append(loot)
        return self
    
    def get_block_loot(self, block):
        if self[block] is not None:
            return self[block]
        else:
            return None
    
    def original_filename(self, block):
        return self.original_pairings[block]['filename']

    def original_loot(self, block):
        return self.original_pairings[block]["loot_table"]
        

    def write_to_datapack(self, name, desc, reset_msg, out_file):
        buffer = io.BytesIO()
        datapack = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)

        for block in self:
            # get the filename for the block
            filename = self.original_filename(block)
            # and write the loot table of the block paired with it
            loot_table = self.original_loot(self[block])
            datapack.writestr(filename, loot_table)

        datapack.writestr(
            "pack.mcmeta",
            json.dumps({"pack": {"pack_format": 1, "description": desc}}, indent=4),
        )

        datapack.writestr(
            "data/minecraft/tags/functions/load.json",
            json.dumps({"values": [name + ":reset"]}),
        )

        datapack.writestr(
            "data/" + name + "/functions/reset.mcfunction", reset_msg,
        )

        datapack.close()

        datapack_file = open(out_file, "wb")
        datapack_file.write(buffer.getvalue())
        datapack_file.close()
    
    # dumps to the console by default for debugging
    def dump_cheatsheet(self, out_file: Path = None):

        columns = {
            "Block": sorted(self.keys()),
            "Loot table": list(self[block] for block in sorted(self.keys())),
        }

        output = tabulate(columns, headers=["Block", "Loot Table"])

        if out_file is not None:
            f = open(out_file, "w")
            print(output, file=f)
            f.close()
        else:
            print(output)