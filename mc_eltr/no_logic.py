import random
from loot_tables_sqlite import LootTables

class NoLogic(LootTables):
    def randomize(self, seed):
        randomize_recipes = self.settings["randomize_recipes"]

        return "foo"